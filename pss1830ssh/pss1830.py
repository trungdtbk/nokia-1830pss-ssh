"""
Base classes for the pss1830ssh module

Author: Trung Truong
Company: Nokia NZ
"""
import time
import re
import logging
import paramiko


class PSSException(Exception):
    """Exception wrapper."""
    pass

#pylint: disable=too-many-instance-attributes
class PSS1830(object):
    """Common class for 1830PSS SSH session to root and CLI.
    """

    TIMEOUT = 30
    PROMPT_RE = None
    CTRL_C = '\x03'

    sleep_interval = 0.25

    logger = logging.getLogger(__name__)

    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connected = False
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.channel = None
        self.prompt = None

    def open(self):
        """Open a SSH connection to a NE."""
        self.logger.info('Opening SSH connection')
        if self.connected:
            self.logger.info('SSH already opened')
            return
        self.client.connect(self.host, self.port, self.username, self.password)
        self.channel = self.client.invoke_shell()
        self.channel.settimeout(self.TIMEOUT)
        self.connected = True
        self.logger.info('SSH connection opened')

    def close(self):
        """Close the SSH connection."""
        self.logger.info('Closing SSH connection')
        if self.connected:
            self.connected = False
            self.channel.close()
            self.client.close()
        self.logger.info('SSH connection closed')

    def execute(self, command):
        """Excecute a command on the NE."""
        self.logger.info('Executing: %s', command)
        if not self.connected:
            raise PSSException('Not connected')
        self._send(command)
        return self._recv_all()

    def cancel(self):
        """Send CTRL+C to cancel the current activity."""
        self._send(self.CTRL_C)

    def _expect(self, expect):
        """Expect a certain response from the NE."""
        self.logger.debug('waiting for: %s', expect)
        for _ in range(int(self.TIMEOUT/self.sleep_interval)):
            data = self._recv()
            match = self._match(expect, data)
            if match:
                self.logger.debug('received the expect')
                return match
            else:
                time.sleep(self.sleep_interval)
        return None

    def _get_prompt(self, prompt_re=None):
        """Get the NE's prompt."""
        self.logger.info('Getting prompt')
        self.prompt = None
        if not prompt_re:
            prompt_re = self.PROMPT_RE
        self._send('')
        data = self._expect(prompt_re)
        if data:
            self.prompt = data.group().strip()
        self.logger.info('Got prompt: %s', self.prompt)
        return self.prompt

    def _check_prompt(self, data):
        """Check if the data contains the prompt."""
        return self._match(self.prompt, data)

    #pylint: disable=no-self-use
    def _match(self, match, data):
        """Search for a match from the data."""
        result = None
        if match and data:
            result = re.search(match, data, re.DOTALL)
        return result

    def _send(self, command):
        """Send a command to the NE."""
        if not self.connected:
            raise PSSException('Not connected')
        self.channel.sendall(command + '\n')
        self.logger.debug('sent: %s', command)

    def _recv(self):
        """Receive data from the NE."""
        if not self.connected:
            raise PSSException('Not connected')
        data = ''
        while self.channel.recv_ready():
            new_data = self.channel.recv(1024)
            if new_data:
                data += new_data
        self.logger.debug('received: %s', data)
        return data

    def _recv_all(self):
        """Receive all available data from the NE."""
        retries = 0
        while retries < self.TIMEOUT/self.sleep_interval:
            data = self._recv()
            if data:
                yield data
                retries = 0
                if self._check_prompt(data):
                    break
            else:
                time.sleep(self.sleep_interval)
                retries += 1
        raise StopIteration()
