import logging
import pytest

from pss1830ssh.pss1830root import PSS1830Root
from pss1830ssh.pss1830 import PSSException

logging.basicConfig(level=logging.DEBUG)

class Response(object):

    def __init__(self, responses):
        self.current = -1
        self.responses = responses

    def recv(self, nbytes):
        return self.responses[self.current]

    def recv_ready(self):
        self.current += 1
        if self.current >= len(self.responses):
            return False
        if self.responses[self.current] is not None:
            return True
        return False

@pytest.fixture(name="mocked_pssroot")
def create_mocked_pssroot(mocker):
    pss = PSS1830Root('localhost', 1234, 'root', 'testpass')
    pss.TIMEOUT = 1
    pss.sleep_interval = 1
    mock_client = mocker.patch.object(pss, 'client')
    mock_channel = mocker.patch.object(pss, 'channel')
    mock_client.invoke_shell.return_value = mock_channel

    response = Response(['Welcome', None, '\r\nroot@EC1830-81-18-ACT:/root# '])
    mock_channel.recv_ready.side_effect = response.recv_ready
    mock_channel.recv.side_effect =  response.recv

    pss.open()
    return pss, mock_channel

def test_exec_command(mocked_pssroot):
    pss, mock_channel = mocked_pssroot
    recv_data = pss.execute('hello')
    mock_channel.sendall.assert_called_with('hello\n')

def test_close(mocked_pssroot):
    pss, channel = mocked_pssroot
    pss.close()
    channel.sendall.assert_called_with('exit\n')

def test_is_on_active(mocked_pssroot):
    pss, channel = mocked_pssroot
    assert pss.is_on_active()

def test_login_to_standby(mocked_pssroot):
    pss, channel = mocked_pssroot
    response = Response([
        'EC1830-81-18 login:', None,
        'Password:', None,
        'Welcome to MontaVista(R) Linux(R) Carrier Grade Edition 4.0 (0600995).\r\n'
        'root@EC1830-81-18-STDBY:/root\r\n# ', None,
        'root@EC1830-81-1-ACT:/root# ',
    ])

    channel.recv_ready.side_effect = response.recv_ready
    channel.recv.side_effect =  response.recv

    pss.login_to_stdby()
    assert pss.is_on_active() is False
    pss.logout_from_stdby()
    assert pss.is_on_active()

def test_login_to_slave_shelf(mocked_pssroot):
    pss, channel = mocked_pssroot
    response = Response([
        'EC1830-2-1 login:', None,
        'Password:', None,
        'Welcome to MontaVista(R) Linux(R) Carrier Grade Edition 4.0 (0600995).\r\n'
        'root@EC1830-2-1-ACT:/root\r\n# ', None,
        'root@EC1830-81-1-ACT:/root# ',
    ])

    channel.recv_ready.side_effect = response.recv_ready
    channel.recv.side_effect =  response.recv

    pss.login_to_shelf(shelf=2, ec=18)
    assert pss.is_on_master() is False
    pss.logout_from_shelf()

def test_login_to_slave_shelf_no_ec_provided(mocked_pssroot):
    pss, channel = mocked_pssroot
    response = Response([
            'EC1830-2-1 login:', None,
            'Password:', None,
            'Welcome to MontaVista(R) Linux(R) Carrier Grade Edition 4.0 (0600995).\r\n'
            'root@EC1830-2-1-STDBY:/root\r\n# ', None,
            'root@EC1830-81-1-ACT:/root# ', None,
            'EC1830-2-1 login:', None,
            'Password:', None,
            'Welcome to MontaVista(R) Linux(R) Carrier Grade Edition 4.0 (0600995).\r\n'
            'root@EC1830-2-18-ACT:/root\r\n# ', None,
            'root@EC1830-2-18-ACT:/root\r\n# '
    ])
    
    channel.recv_ready.side_effect = response.recv_ready
    channel.recv.side_effect =  response.recv

    pss.login_to_shelf(shelf=2)
    assert pss.is_on_master() is False

def test_login_to_shelf_fail(mocked_pssroot):
    pss, channel = mocked_pssroot
    response = Response(['EC1830-2-1 login:',])
    channel.recv.side_effect = response.recv
    channel.recv_ready.side_effect = response.recv_ready
    with pytest.raises(PSSException, match=r'Failed to login to shelf'):
        pss.login_to_shelf(shelf=2, ec=18)
        assert pss.is_on_active()
        assert pss.is_on_master()

def test_login_to_shelf_fail_no_prompt(mocked_pssroot):
    pss, channel = mocked_pssroot
    response = Response([
        'EC1830-2-1 login:', None,
        'Password:', None, 
        'Welcome to MontaVista(R) Linux(R) Carrier Grade Edition 4.0 (0600995).\r\n'
        ])
    channel.recv.side_effect = response.recv
    channel.recv_ready.side_effect = response.recv_ready
    with pytest.raises(PSSException, match=r'Failed to login to shelf'):
        pss.login_to_shelf(shelf=2, ec=18)
        assert pss.is_on_active()
        assert pss.is_on_master()
    
def test_login_to_slot_no_password_required(mocked_pssroot):
    pss, channel = mocked_pssroot
    response = Response([
        'EC1830-2-1 login:', None,
        '# ', None, '# '
        ])
    channel.recv.side_effect = response.recv
    channel.recv_ready.side_effect = response.recv_ready    
    pss.login_to_slot(shelf=2, slot=3)
    assert pss.is_on_active() is False
    assert pss.is_on_master()
