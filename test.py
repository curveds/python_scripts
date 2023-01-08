import json
from unittest import mock

import pytest

from json_updater_via_ssh import get_credential

cluster = "NA-CLUSTER"

@mock.patch("json_updater_via_ssh.open", create=True, autospec=None)
def test_load_credentials_without_specified_ssh(
    mock_open,
):
    principal = "nauser"
    secret = "nauser"
    credentials = {
            "hosts": {
                "EU-CLUSTER": {
                    "title": "Eu cluster discription",
                    "host": "eu1-vm-host",
                    "user": "euuser"
                },
                "NA-CLUSTER": {
                    "title": "Na cluster description",
                    "host": "na1-vm-host",
                    "user": "nauser"
                }
            }
        }

    mock_open.side_effect = mock.mock_open(read_data=json.dumps(credentials))

    credentials = get_credential("/blah/blah", cluster)

    assert credentials.principal == principal
    assert credentials.secret == secret

@mock.patch("json_updater_via_ssh.open", create=True, autospec=None)
def test_load_credentials_with_specified_ssh(
    mock_open,
):
    principal = "nauser"
    ssh_key_path = "~/.ssh/id_rsa.pub"
    credentials = {
            "hosts": {
                "EU-CLUSTER": {
                    "title": "Eu cluster discription",
                    "host": "eu1-vm-host",
                    "user": "euuser"
                },
                "NA-CLUSTER": {
                    "title": "Na cluster description",
                    "host": "na1-vm-host",
                    "ssh_key_path": "~/.ssh/id_rsa.pub",
                    "user": "nauser"
                }
            }
        }

    mock_open.side_effect = mock.mock_open(read_data=json.dumps(credentials))

    credentials = get_credential("/blah/blah", cluster)

    assert credentials.principal == principal
    assert credentials.secret == ssh_key_path

@mock.patch("json_updater_via_ssh.open", create=True, side_effect=IOError, autospec=None)
def test_get_credentials_missing_file(
    mock_open,
):
    with pytest.raises(IOError):
        assert get_credential("/blah/blah", cluster)

@mock.patch("json_updater_via_ssh.open", create=True, autospec=None)
def test_get_credentials_keyerror(
    mock_open,
):
    credentials = {}

    mock_open.side_effect = mock.mock_open(read_data=json.dumps(credentials))

    with pytest.raises(KeyError):
        assert get_credential("/blah/blah", cluster)
