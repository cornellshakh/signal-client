# Data Models (Schemas)

The `signal-client` library previously had a `domain` layer, but this has been refactored to align with modern best practices. The core data models, now referred to as schemas, are located in the `infrastructure/schemas/` directory.

These schemas are Pydantic models that define the structure of the data used in API requests and responses (DTOs). This approach ensures that all communication with the Signal service is type-safe and that the core application logic is decoupled from the data transfer objects.

### `message.py`

- **Purpose:** Defines the `Message` model, which encapsulates all information about a single incoming or outgoing message. This includes the sender (`source`), content (`text`), timestamp, attachments, and any associated reactions or quotes.

### `contact.py` & `contacts.py`

- **Purpose:** These files define the models for Signal contacts.
- `contact.py`: Contains the `Contact` model, representing a single Signal user, including their phone number, name, and profile details.
- `contacts.py`: Contains logic for managing collections of contacts or parsing contact-related events.

### `group.py` & `groups.py`

- **Purpose:** These files define the models for Signal groups.
- `group.py`: Contains the `Group` model, representing a single group chat, including its ID, name, members, and other metadata.
- `groups.py`: Contains logic for managing collections of groups or parsing group-related events.

### `quote.py`

- **Purpose:** Defines the `Quote` model. When a user replies to a specific message, that reply includes a "quote" of the original message. This model represents that quoted content, including the original author and timestamp.

### `reaction.py`

- **Purpose:** Defines the `Reaction` model. This represents an emoji reaction to a message, linking the emoji to the target message and author.
