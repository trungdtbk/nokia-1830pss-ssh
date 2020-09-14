"""
Abstraction for a CLI interface of a NE
"""
from pss1830ssh.pss1830 import PSS1830
from pss1830ssh.pss1830 import PSSException

class PSS1830Cli(PSS1830):
    """Represent a CLI session to a 1830-PSS NE
    How to use:
        cli = PSS1830Cli('1.2.3.4', 22, 'admin', 'admin') # create an instance
        cli.open() # open CLI session
        result = cli.execute('show gen detail') # execute a command
        for data in result:
            print(data) # use the result
        cli.close() # close the CLI
    """

    PROMPT_RE = '\n[\w-]+# $'

    def __init__(self, host, port, username, password):
        super(PSS1830Cli, self).__init__(host, port, 'cli', 'cli')
        self.cli_user = username
        self.cli_pass = password

    def close(self):
        self._send('logout')
        super(PSS1830Cli, self).close()

    def open(self):
        super(PSS1830Cli, self).open()
        self._authenticate()
        self._get_prompt()
        if not self.prompt:
            raise PSSException('Failed to get the prompt')
        self._paging_disable()

    def _authenticate(self):
        self.logger.debug('Authenticating CLI')
        for expect, response in [
                ('\nUsername:', self.cli_user),
                ('\nPassword:', self.cli_pass),
                ('\nDo you.*(Y/N)?', 'Y')]:
            if self._expect(expect):
                self._send(response)
            else:
                self.close()
                raise PSSException(
                    'Failed to login. Expected: "%s" but not received: '
                    % expect.encode('unicode_escape'))
        self._recv()
        self.connected = True
        self.logger.debug('Authenticated CLI')

    def _paging_disable(self):
        list(self.execute('paging status disable'))

