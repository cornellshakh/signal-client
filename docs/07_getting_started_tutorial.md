# Getting Started Tutorial: Building a Dad Joke Bot

Welcome to the `signal-client` getting started tutorial! In this guide, we will walk you through the process of building a simple but fun Signal bot that tells dad jokes.

By the end of this tutorial, you will have learned how to:

- Set up the `signal-cli-rest-api` service.
- Install the `signal-client` library.
- Create a simple command.
- Run your bot and interact with it on Signal.

---

## Step 1: Prerequisites

Before you begin, make sure you have the following installed:

- [Docker](https://www.docker.com/get-started)
- [Python 3.9+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/)

---

## Step 2: Set Up the Signal API Service

The `signal-client` library communicates with the Signal network through the `signal-cli-rest-api` service. Let's get it running.

1.  **Create a Directory for Configuration:**

    ```bash
    mkdir signal-cli-config
    ```

2.  **Run the API Service in `normal` Mode:**

    This command will start the service and mount the local configuration directory into the container.

    ```bash
    docker run -p 8080:8080 \
        -v $(pwd)/signal-cli-config:/home/.local/share/signal-cli \
        -e 'MODE=normal' bbernhard/signal-cli-rest-api:latest
    ```

3.  **Link Your Signal Account:**

    Open the following link in your browser to generate a QR code:
    [http://127.0.0.1:8080/v1/qrcodelink?device_name=my-bot](http://127.0.0.1:8080/v1/qrcodelink?device_name=my-bot)

    In your Signal mobile app, go to **Settings > Linked devices** and scan the QR code.

4.  **Restart in `json-rpc` Mode:**

    Once you have successfully linked your device, stop the running container (with `Ctrl+C`) and restart it in `json-rpc` mode. This is the mode the library uses to listen for incoming messages.

    ```bash
    docker run -p 8080:8080 \
        -v $(pwd)/signal-cli-config:/home/.local/share/signal-cli \
        -e 'MODE=json-rpc' bbernhard/signal-cli-rest-api:latest
    ```

    You should see output indicating that the service is listening for messages.

---

## Step 3: Create Your Bot Project

1.  **Create a Project Directory:**

    ```bash
    mkdir dad-joke-bot
    cd dad-joke-bot
    ```

2.  **Install `signal-client`:**

    ```bash
    pip install signal-client
    ```

3.  **Create a `main.py` File:**

    This file will contain the code for our bot.

    ```bash
    touch main.py
    ```

---

## Step 4: Write the Bot's Code

Open `main.py` in your favorite editor and add the following code.

```python
# main.py
import asyncio
import random
from signal_client import SignalClient, Command, Context

# A list of classic dad jokes
DAD_JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "I'm reading a book on anti-gravity. It's impossible to put down!",
    "What do you call a fake noodle? An Impasta!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Did you hear about the claustrophobic astronaut? He just needed a little space.",
]

# 1. Define our command
class JokeCommand:
    triggers = ["!joke"]

    async def handle(self, context: Context) -> None:
        """This method is called when the command is triggered."""
        joke = random.choice(DAD_JOKES)
        await context.reply(f"Here's a joke for you:\n\n{joke}")
        await context.react("😂")

# 2. Configure and run the client
async def main():
    # Replace with your bot's phone number in E.164 format
    # (e.g., "+1234567890")
    phone_number = "+1234567890"

    config = {
        "signal_service": "http://localhost:8080",
        "phone_number": phone_number,
    }

    client = SignalClient(config)
    client.register(JokeCommand())

    print("Bot is starting...")
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())
```

**Important:** Make sure to replace `+1234567890` with the phone number of the account you linked in Step 2.

---

## Step 5: Run Your Bot

You are now ready to run your bot!

1.  **Run the `main.py` file:**

    ```bash
    python main.py
    ```

    You should see the message "Bot is starting...".

2.  **Test it Out:**

    From another Signal account, send a message containing `!joke` to your bot's phone number. The bot should reply with a random dad joke and a "😂" reaction!

---

## Congratulations!

You have successfully built your first Signal bot. You can now expand on this foundation by adding more commands, integrating with other APIs, and building more complex logic.

Happy bot-building!

---

## A Complete, Runnable Example

For your convenience, here is the complete code for the Dad Joke Bot. You can save this as `main.py` and run it directly after setting up the `signal-cli-rest-api` service.

```python
# main.py
import asyncio
import random
import os
from signal_client import SignalClient, Command, Context

# A list of classic dad jokes
DAD_JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "I'm reading a book on anti-gravity. It's impossible to put down!",
    "What do you call a fake noodle? An Impasta!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Did you hear about the claustrophobic astronaut? He just needed a little space.",
]

# 1. Define our command
class JokeCommand(Command):
    """
    A simple command that replies with a random dad joke.
    """
    async def handle(self, context: Context) -> None:
        """This method is called when the command is triggered."""
        joke = random.choice(DAD_JOKES)
        await context.reply(f"Here's a joke for you:\n\n{joke}")
        await context.react("😂")

# 2. Configure and run the client
async def main():
    # It's recommended to use an environment variable for the phone number
    phone_number = os.environ.get("SIGNAL_PHONE_NUMBER")
    if not phone_number:
        raise ValueError(
            "Please set the SIGNAL_PHONE_NUMBER environment variable."
        )

    config = {
        "signal_service": "http://localhost:8080",
        "phone_number": phone_number,
    }

    client = SignalClient(config)
    client.register("!joke", JokeCommand())

    print("Bot is starting...")
    await client.start()

if __name__ == "__main__":
    # To run this, set the SIGNAL_PHONE_NUMBER environment variable:
    # export SIGNAL_PHONE_NUMBER="+1234567890"
    # python main.py
    asyncio.run(main())
```
