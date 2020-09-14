import pytest

import pss1830ssh.pss1830cli as psscli
from pss1830ssh.pss1830 import PSSException

@pytest.fixture(name="notconnected")
def create_mocked_psscli(mocker):
    pss = psscli.PSS1830Cli('localhost', 22, 'test', 'test123')
    pss.TIMEOUT = 1
    mock_channel = mocker.patch.object(pss, 'channel')
    mock_client = mocker.patch.object(pss, 'client')
    mock_client.invoke_shell.return_value = mock_channel
    return pss, mock_channel

@pytest.fixture(name="connected")
def created_mocked_connected_psscli(notconnected, mocker):
    pss, channel = notconnected
    pss.connected = True
    pss.prompt = 'prompt#'
    return pss, channel

def test_open_success(notconnected):
    pss, channel = notconnected
    responses = [
        'Some banner',
        'Some welcome\r\nUsername:',
        '\r\nPassword: ',
        '\r\nDo you acknowledge (Y/N)?',
        'Some information',
        '\r\nprompt# ',
        '\r\nprompt# '
    ]
    channel.recv_ready.side_effect = [True, True, False, True, False, True, False, True, True, False, True, False]
    channel.recv.side_effect = responses
    pss.open()
    assert pss.connected
    assert pss.prompt == 'prompt#'

def test_open_fail(notconnected):
    pss, channel = notconnected
    channel.recv.side_effect = ['a']
    channel.recv_ready.side_effect = [False]*9 # give it enough tries
    with pytest.raises(PSSException, match=r'Failed to login'):
        pss.open()

def test_open_fail_no_prompt(notconnected):
    pss, channel = notconnected
    responses = [
        'Some banner',
        'Some welcome\r\nUsername:',
        '\r\nPassword: ',
        '\r\nDo you acknowledge (Y/N)?',
    ]
    channel.recv_ready.side_effect = [True, True, False, True, False, True] + [False]*9
    channel.recv.side_effect = responses
    with pytest.raises(PSSException, match=r'Failed to get the prompt'):
        pss.open()

def test_close(connected):
    pss, channel = connected
    pss.close()
    channel.sendall.assert_called_once_with('logout\n')

