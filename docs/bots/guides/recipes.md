# Recipes

## Send a structured reply

```python
@bot.command("deploy")
async def deploy(context, payload):
    await context.reply("Deployment queued", metadata={"service": payload.service})
```

## Forward alerts

```python
from signal_client.infrastructure.alerts import Dispatcher

dispatcher = Dispatcher()
await dispatcher.send(channel="ops", text="CPU high", severity="warning")
```

Add more recipes as we formalize modules. Use tabs when steps differ for pip vs Poetry deployments.
