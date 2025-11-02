from __future__ import annotations

import pytest

from signal_client.infrastructure.api_clients.contacts_client import ContactsClient


@pytest.mark.asyncio
async def test_contacts_client(
    contacts_client: ContactsClient, aresponses
):
    """Test the contacts client."""
    # Arrange
    aresponses.add(
        "localhost:8080",
        "/v1/contacts/phonenumber",
        "GET",
        aresponses.Response(
            status=200,
            text='[{"uuid": "contact1"}]',
            headers={"Content-Type": "application/json"},
        ),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/contacts/phonenumber",
        "PUT",
        aresponses.Response(status=204),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/contacts/phonenumber/sync",
        "POST",
        aresponses.Response(status=204),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/contacts/phonenumber/contact1",
        "GET",
        aresponses.Response(
            status=200,
            text='{"uuid": "contact1"}',
            headers={"Content-Type": "application/json"},
        ),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/contacts/phonenumber/contact1/avatar",
        "GET",
        aresponses.Response(status=200, text="avatar data"),
    )

    # Act
    contacts = await contacts_client.get_contacts("phonenumber")
    await contacts_client.update_contact("phonenumber", {})
    await contacts_client.sync_contacts("phonenumber")
    contact = await contacts_client.get_contact("phonenumber", "contact1")
    avatar = await contacts_client.get_contact_avatar("phonenumber", "contact1")

    # Assert
    assert contacts == [{"uuid": "contact1"}]
    assert contact == {"uuid": "contact1"}
    assert avatar == b"avatar data"