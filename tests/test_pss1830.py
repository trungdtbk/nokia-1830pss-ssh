import socket
import pytest

import pss1830ssh.pss1830 as pss1830

HOST = 'localhost'
PORT = 2345
USER = 'test'
PASS = 'test123'

@pytest.fixture(name="notconnected")
def create_mocked_pss(mocker):
    pss = pss1830.PSS1830(HOST, PORT, USER, PASS)
    mock_paramiko_client = mocker.patch.object(pss, 'client')
    mock_paramiko_channel = mocker.patch.object(pss, 'channel')
    return (pss, mock_paramiko_client, mock_paramiko_channel)

@pytest.fixture(name="connected")
def create_mocked_pss_loggin(mocker):
    pss = pss1830.PSS1830(HOST, PORT, USER, PASS)
    mocker.patch.object(pss, 'client')
    pss.open()
    mock_paramiko_channel = mocker.patch.object(pss, 'channel')
    pss.channel = mock_paramiko_channel
    return (pss, mock_paramiko_channel)

def test_open(notconnected):
    pss, client, _ = notconnected
    assert pss.connected is False
    pss.open()
    assert pss.connected
    pss.open() # should not login twice
    client.connect.assert_called_once_with(HOST, PORT, USER, PASS)
    client.invoke_shell.assert_called_once()

def test_close(connected):
    pss, channel = connected
    assert pss.connected
    pss.close()
    assert pss.connected is False
    pss.close() # should return immediately as already logged out
    channel.close.assert_called_once()

def test_execute(connected):
    pss, channel = connected
    data = ['data1', 'data2']
    channel.recv_ready.side_effect = [True if d else False for d in data + ['']]
    channel.recv.side_effect = data
    rcv_data = list(pss.execute('hello'))
    assert rcv_data == [''.join(data)]

def test_execute_not_connected(notconnected):
    pss, _, _ = notconnected
    with pytest.raises(pss1830.PSSException, match=r'Not connected'):
        pss.execute('hello')
