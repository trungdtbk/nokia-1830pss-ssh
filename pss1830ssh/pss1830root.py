"""
Abstraction for NE root shell 
"""
import os
import time
from pss1830ssh.pss1830 import PSS1830
from pss1830ssh.pss1830 import PSSException


def get_ec_ip(shelf, ec):
    return '100.0.{shelf}.{ec}'.format(shelf=shelf, ec=ec)

class PSS1830Root(PSS1830):
    """Wrapper for PSS root mode."""

    PROMPT_RE = '(root@EC1830-\d+-\d+-ACT:/root[\r\n]*# $)|'\
                '(root@32EC2-\d+-\d+-ACT:[~\r\n]*# $)|'\
                '(root@EC1830-\d+-\d+-STDBY:/root[\r\n]*# $)|'\
                '(root@32EC2-\d+-\d+-STDBY:[~\r\n]*# $)'
    telnet_prompt_re = '.*# $'
    on_master = True
    slot_ip = '100.0.{shelf}.{slot}'

    def open(self):
        super(PSS1830Root, self).open()
        self._recv()
        self._get_prompt()

    def close(self):
        self._send('exit')
        super(PSS1830Root, self).close()

    def is_on_master(self):
        return self.on_master

    def is_on_active(self):
        """Check if it is currently on active EC."""
        return 'ACT' in self.prompt

    def _exit(self):
        self._send('exit')
        self._get_prompt()

    def _telnet(self, ip):
        self.logger.debug('telnet %s', ip)
        self._send('telnet %s' % ip)
        if self._expect('login:'):            
            self._send(self.username)
            time.sleep(1)
            data = self._recv()
            if self._match('Password:', data):
                self._send(self.password)
                self.logger.debug('telnet %s succeeded', ip)
                return True
            elif self._match(self.telnet_prompt_re, data):
                self.logger.debug('telnet %s succeeded', ip)
                return True

            # data = ''.join(self._recv_all())
            # if self._match(self.telnet_prompt_re, data):
            #     self.logger.debug('telnet %s succeeded', ip)
            #     return True
            # elif self._match('Password:', data):
            #     self._send(self.password)
            #     self.logger.debug('telnet %s succeeded', ip)
            #     return True
        self.cancel()
        self.logger.debug('telnet %s failed', ip)
        return False
    
    def login_to_slot(self, shelf, slot):
        """Telnet to a card/slot."""
        self.logger.debug('Logging in slot: %s/%s', shelf, slot)
        if self._telnet(self.slot_ip.format(shelf=shelf, slot=slot)):
            if self._get_prompt(self.telnet_prompt_re):
                self.logger.debug('Logged in slot: %s/%s', shelf, slot)
                return True
        raise PSSException('Failed to login to slot: %s/%s' % (shelf, slot))

    def logout_from_slot(self):
        if not self.is_on_active():
            self.logger.debug('Logging out slot')
            self._exit()

    def login_to_shelf(self, shelf, ec=None, act=True):
        """Telnet to a slave shelf."""
        self.logger.debug('Logging in shelf: %s (ec=%s, act=%s)' % (shelf, ec, act))
        ec_cards = [ec] if ec else [1, 18]
        login_ok = False
        for e in ec_cards:
            if self._telnet(get_ec_ip(shelf, e)):
                if self._get_prompt() and self.is_on_active() == act:
                    self.on_master = shelf == 81
                    login_ok = True
                    break
                elif self.prompt:
                    self._exit()
                else:
                    self.cancel()
        if not login_ok:
            raise PSSException('Failed to login to shelf (shelf=%s, ec=%s)' % (shelf, e))

    def logout_from_shelf(self):
        """Logout from a slave shelf."""
        self.logger.debug('Logging out shelf')
        if not self.is_on_master():
            self._exit()
            if not self.prompt:
                raise PSSException('Logout from an EC failed. Failed to get the prompt')
    
    def login_to_stdby(self):
        """Login to Standby EC."""
        if self.is_on_active() and self.is_on_master():
            self.logger.debug('Logging in standby EC')
            act_ec = int(self.prompt.split('-')[2])
            stdby_ec = 1 if act_ec == 18 else 18
            self.login_to_shelf(shelf=81, ec=stdby_ec, act=False)

    def logout_from_stdby(self):
        if not self.is_on_active():
            self.logger.debug('Logging out standby EC')
            self._exit()

    def get_file(self, remotepath, localpath, callback=None, recursive=True):
        """Get files from the NE to the local machine
        """
        self.logger.debug('Openning SFTP')
        scp = self.client.open_sftp()
        if recursive:
            scp.chdir(remotepath)
            for fname in scp.listdir():
                remote = os.path.join(remotepath, fname)
                local = os.path.join(localpath, fname)
                self.logger.debug('Transferring: %s to %s' % (remote, local))
                scp.get(remote, local, callback)
        else:
            self.logger.debug('Transferring: %s to %s' % (remotepath, localpath))
            scp.get(remotepath, localpath, callback)
        scp.close()
