import urllib.parse

import pytest

from congo_discord.service.invite import ADMINISTRATOR, PERMISSIONS, invite_url, permission_value

APP = "123456789012345678"


def test_invite_asks_only_the_permissions_the_code_uses():
    url = invite_url(APP)
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert url.startswith("https://discord.com/oauth2/authorize?")
    assert query["client_id"] == [APP]
    assert query["scope"] == ["bot applications.commands"]
    value = int(query["permissions"][0])
    assert value == permission_value() == (1 << 10) | (1 << 11) | (1 << 15) | (1 << 20) | (1 << 21)
    assert not value & ADMINISTRATOR
    assert set(PERMISSIONS) == {"VIEW_CHANNEL", "SEND_MESSAGES", "ATTACH_FILES", "CONNECT", "SPEAK"}


def test_invite_for_one_server_locks_the_choice():
    query = urllib.parse.parse_qs(urllib.parse.urlparse(invite_url(APP, "876543210987654321")).query)
    assert query["guild_id"] == ["876543210987654321"]
    assert query["disable_guild_select"] == ["true"]


@pytest.mark.parametrize("bad", ["", "abc", "123", "1234567890123456789012", "123456789012345678&scope=x"])
def test_invite_refuses_ids_that_are_not_numbers(bad):
    with pytest.raises(ValueError):
        invite_url(bad)
