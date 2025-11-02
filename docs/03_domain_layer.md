# Domain Layer

The `domain` layer contains the core data models and business logic of the `signal-client` library. These objects represent the fundamental entities within the Signal ecosystem, such as messages, contacts, and groups. They are plain Python objects, decoupled from the underlying infrastructure, making them easy to understand and test.

### `contact.py`

- **Purpose:** Defines the `Contact` model, which represents a single Signal user. It typically holds information such as the user's phone number, name, and profile details.

### `group.py` & `groups.py`

- **Purpose:** These files define the models for Signal groups.
- `group.py`: Contains the `Group` model, representing a single group chat, including its ID, name, members, and other metadata.
- `groups.py`: Likely contains logic for managing collections of groups or parsing group-related events.

### `message.py` & `messages.py`

- **Purpose:** These files are central to the library, defining how messages are represented.
- `message.py`: Defines the `Message` model, which encapsulates all information about a single incoming or outgoing message. This includes the sender (`source`), content (`text`), timestamp, attachments, and any associated reactions or quotes.
- `messages.py`: Likely contains helper functions or models for handling lists of messages or parsing different types of message events from the Signal service.

### `quote.py`

- **Purpose:** Defines the `Quote` model. When a user replies to a specific message, that reply includes a "quote" of the original message. This model represents that quoted content, including the original author and timestamp.

### `reaction.py`

- **Purpose:** Defines the `Reaction` model. This represents an emoji reaction to a message, linking the emoji to the target message and author.
