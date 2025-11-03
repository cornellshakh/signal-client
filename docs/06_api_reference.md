# API Reference

This document provides a detailed reference for the public-facing classes and methods in the `signal-client` library.

---

## `SignalClient`

**File:** `signal_client/bot.py`

The main entry point for the library. This class is used to configure and run the bot.

### `__init__(self, config: dict | None = None, container: Container | None = None)`

- **Description:** Initializes the `SignalClient`.
- **Parameters:**
  - `config` (optional): A dictionary of configuration options.
  - `container` (optional): A pre-configured `Container` instance for advanced use cases.

### `register(self, command: Command) -> None`

- **Description:** Registers a new command with the bot.
- **Parameters:**
  - `command`: An instance of a class that implements the `Command` protocol.

### `start(self) -> None`

- **Description:** Starts the bot's main event loop. This method is a coroutine and should be awaited.

### `shutdown(self) -> None`

- **Description:** Gracefully shuts down the bot and its resources.

---

## `Context`

**File:** `signal_client/context.py`

The `Context` object is passed to a command's `handle` method and provides a high-level API for interacting with the Signal service.

### Attributes

- `message: Message`: The parsed incoming message object from `infrastructure/schemas/message.py`.

### Methods

#### `send(self, text: str, recipient: str) -> None`

- **Description:** Sends a message to a specified recipient.
- **Parameters:**
  - `text`: The content of the message.
  - `recipient`: The phone number of the user to send the message to.

#### `reply(self, text: str) -> None`

- **Description:** Sends a message that quotes the original message that triggered the command.
- **Parameters:**
  - `text`: The content of the reply.

#### `react(self, emoji: str) -> None`

- **Description:** Adds an emoji reaction to the original message.
- **Parameters:**
  - `emoji`: The emoji to use for the reaction (e.g., "👍").

#### `remove_reaction(self) -> None`

- **Description:** Removes a previously added reaction from the original message.

#### `start_typing(self) -> None`

- **Description:** Displays the "typing..." indicator in the chat.

#### `stop_typing(self) -> None`

- **Description:** Hides the "typing..." indicator.

---

## `Command` Protocol

**File:** `signal_client/command.py`

The `Command` protocol defines the interface that all command classes must implement.

### Required Attributes

- `triggers: list[str | re.Pattern]`: A list of strings or compiled regex patterns that will trigger the command.
- `handle(self, context: Context) -> None`: The asynchronous method that contains the command's logic.

### Optional Attributes

- `whitelisted: list[str]`: A list of user phone numbers or group IDs to restrict the command to.
- `case_sensitive: bool`: Determines if the `triggers` should be matched in a case-sensitive manner (default: `False`).

---

## API Clients

The following sections detail the methods available in each of the API clients. These clients are accessible via the `Context` object in a command's `handle` method.

### `RateLimiter`

**File:** `signal_client/services/rate_limiter.py`

- `acquire()`: Acquires a permit from the rate limiter. This is an async method that should be awaited.

### `AccountsClient`

**File:** `signal_client/infrastructure/api_clients/accounts_client.py`

- `get_accounts()`: Lists all accounts.
- `get_account(phone_number: str)`: Gets information about a specific account.
- `set_device_name(phone_number: str, data: dict)`: Sets the device name.
- `set_pin(phone_number: str, data: dict)`: Sets a PIN.
- `remove_pin(phone_number: str)`: Removes a PIN.
- `set_registration_lock_pin(phone_number: str, data: dict)`: Sets a registration lock PIN.
- `remove_registration_lock_pin(phone_number: str)`: Removes a registration lock PIN.
- `lift_rate_limit(phone_number: str, data: dict)`: Lifts rate limit restrictions.
- `update_settings(phone_number: str, data: dict)`: Updates the account settings.
- `set_username(phone_number: str, data: dict)`: Sets a username.
- `remove_username(phone_number: str)`: Removes a username.

### `AttachmentsClient`

**File:** `signal_client/infrastructure/api_clients/attachments_client.py`

- `get_attachments()`: Lists all attachments.
- `get_attachment(attachment_id: str)`: Serves an attachment.
- `remove_attachment(attachment_id: str)`: Removes an attachment.

### `ContactsClient`

**File:** `signal_client/infrastructure/api_clients/contacts_client.py`

- `get_contacts(phone_number: str)`: Lists contacts.
- `update_contact(phone_number: str, data: dict)`: Updates or adds a contact.
- `sync_contacts(phone_number: str)`: Syncs contacts to linked devices.
- `get_contact(phone_number: str, uuid: str)`: Lists a specific contact.
- `get_contact_avatar(phone_number: str, uuid: str)`: Returns the avatar of a contact.
- `block_contact(phone_number: str, data: dict)`: Blocks a contact.
- `unblock_contact(phone_number: str, data: dict)`: Unblocks a contact.

### `DevicesClient`

**File:** `signal_client/infrastructure/api_clients/devices_client.py`

- `get_devices(phone_number: str)`: Lists linked devices.
- `add_device(phone_number: str, data: dict)`: Links another device.
- `remove_device(phone_number: str, device_id: str)`: Removes a linked device.
- `get_qrcodelink()`: Links a device and generates a QR code.
- `register(phone_number: str)`: Registers a phone number.
- `verify(phone_number: str, token: str)`: Verifies a registered phone number.
- `unregister(phone_number: str)`: Unregisters a phone number.

### `GeneralClient`

**File:** `signal_client/infrastructure/api_clients/general_client.py`

- `get_about()`: Lists general information about the API.
- `get_configuration()`: Lists the REST API configuration.
- `set_configuration(data: dict)`: Sets the REST API configuration.
- `get_mode(phone_number: str)`: Gets the mode of an account.
- `set_mode(phone_number: str, data: dict)`: Sets the mode of an account.
- `get_settings(phone_number: str)`: Lists account-specific settings.
- `set_settings(phone_number: str, data: dict)`: Sets account-specific settings.
- `get_health()`: Performs an API health check.

### `GroupsClient`

**File:** `signal_client/infrastructure/api_clients/groups_client.py`

- `get_groups(phone_number: str)`: Lists all Signal Groups.
- `create_group(phone_number: str, request: CreateGroupRequest)`: Creates a new Signal Group.
- `get_group(phone_number: str, group_id: str)`: Lists a Signal Group.
- `update_group(phone_number: str, group_id: str, request: UpdateGroupRequest)`: Updates the state of a Signal Group.
- `delete_group(phone_number: str, group_id: str)`: Deletes a Signal Group.
- `add_admins(phone_number: str, group_id: str, request: ChangeGroupAdminsRequest)`: Adds admins to a group.
- `remove_admins(phone_number: str, group_id: str, request: ChangeGroupAdminsRequest)`: Removes admins from a group.
- `get_avatar(phone_number: str, group_id: str)`: Returns the avatar of a Signal Group.
- `set_avatar(phone_number: str, group_id: str, data: dict)`: Sets the avatar of a Signal Group.
- `block(phone_number: str, group_id: str)`: Blocks a Signal Group.
- `unblock(phone_number: str, group_id: str)`: Unblocks a Signal Group.
- `join(phone_number: str, group_id: str)`: Joins a Signal Group.
- `add_members(phone_number: str, group_id: str, request: ChangeGroupMembersRequest)`: Adds members to a group.
- `remove_members(phone_number: str, group_id: str, request: ChangeGroupMembersRequest)`: Removes members from a group.
- `quit(phone_number: str, group_id: str)`: Quits a Signal Group.

### `IdentitiesClient`

**File:** `signal_client/infrastructure/api_clients/identities_client.py`

- `get_identities(phone_number: str)`: Lists Identities.
- `trust_identity(phone_number: str, number_to_trust: str, data: dict)`: Trusts an Identity.

### `MessagesClient`

**File:** `signal_client/infrastructure/api_clients/messages_client.py`

- `send(data: dict)`: Sends a signal message.
- `get_messages(phone_number: str, recipient: str, limit: int | None = None)`: Gets messages from a recipient.
- `remote_delete(phone_number: str, data: dict)`: Deletes a signal message.
- `set_typing_indicator(phone_number: str, data: dict)`: Shows the "typing..." indicator.
- `unset_typing_indicator(phone_number: str, data: dict)`: Hides the "typing..." indicator.

### `ProfilesClient`

**File:** `signal_client/infrastructure/api_clients/profiles_client.py`

- `get_profile(phone_number: str)`: Gets a profile.
- `update_profile(phone_number: str, data: dict)`: Updates a profile.
- `get_profile_avatar(phone_number: str)`: Gets a profile avatar.

### `ReactionsClient`

**File:** `signal_client/infrastructure/api_clients/reactions_client.py`

- `send_reaction(phone_number: str, data: dict)`: Sends a reaction.
- `remove_reaction(phone_number: str, data: dict)`: Removes a reaction.

### `ReceiptsClient`

**File:** `signal_client/infrastructure/api_clients/receipts_client.py`

- `send_receipt(phone_number: str, data: dict)`: Sends a receipt.

### `SearchClient`

**File:** `signal_client/infrastructure/api_clients/search_client.py`

- `search_registered_numbers(phone_number: str, numbers: list[str])`: Checks if numbers are registered.

### `StickerPacksClient`

**File:** `signal_client/infrastructure/api_clients/sticker_packs_client.py`

- `get_sticker_packs(phone_number: str)`: Lists installed sticker packs.
- `add_sticker_pack(phone_number: str, data: dict)`: Adds a sticker pack.
- `get_sticker_pack(phone_number: str, pack_id: str, sticker_id: str)`: Gets a sticker from a sticker pack.
