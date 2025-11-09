---
title: Recipes
summary: Step-by-step playbooks for common Signal Client automations.
order: 210
---

## Encrypted attachments broadcast

[=25% "Upload media"]

1. Use the attachments client to upload files and capture a handle.
2. Store the handle in your data store keyed by incident ID.
3. Send a templated message to your broadcast groups with the handle.

```python
# Upload attachment and send to groups
handle = await context.attachments.upload(path="outage.pdf")
await context.send_attachment(handle=handle, caption="Incident report")
```

/// details | Deep dive
- Validate recipients against an allowlist before sending.
- Rotate attachments after each incident so outdated data is not reused.
///

[=100% "Customers notified"]{: .success}

## Group escalation workflow

[=20% "Acknowledge alert"]

1. Command acknowledges the incoming alert and posts to the escalation group.
2. Secondary command pings on-call personnel until someone reacts with ✅.
3. Use the groups client to manage group membership for incident handoffs.

```python
# Acknowledge alert and manage group membership
await context.reply("Alert acknowledged ✅")
await context.groups.remove_member(group_id="escalation", number="+1234567890")
```

/// details | Deep dive
- Track active responders in SQLite with expiry timestamps.
- Use Prometheus alerts to trigger fallback channels if no acknowledgement is received.
///

## Compliance survey

[=40% "Survey deployed"]

1. Schedule APScheduler job that enqueues a `compliance_survey` command daily.
2. Command sends a multiple-choice message and stores selections in SQLite.
3. Export aggregate results via webhook to your BI system.

/// details | Deep dive
- Provide a REST endpoint for manual resends when employees miss the window.
- Map responses to employee IDs using dependency-injected HR data.
///

## Story campaign

[=50% "Story ready"]

1. Render campaign artwork and upload via REST `/v1/stories` endpoint.
2. Command schedules a series of story releases using APScheduler.
3. Monitor `signal_client_story_events_total` for delivery success.

/// details | Deep dive
- Use a staging device to preview stories before publishing.
- Sync schedule with marketing calendar to avoid conflicting pushes.
///

## Incident postmortem reminder

[=30% "Reminder scheduled"]

1. After incident closure, enqueue delayed job with due timestamp.
2. Command pings the incident owner with structured checklist and link to runbook.
3. If no response after 24 hours, escalate to the team's manager via broadcast.

/// details | Deep dive
- Implement metrics tracking through dependency injection for monitoring repeated misses.
- Store incident metadata in your data store to avoid duplicate reminders.
///

> **Next step** · Reference the sample scripts in the project's `scripts/` directory for more end-to-end automation examples.
