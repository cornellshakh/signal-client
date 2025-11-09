---
title: Signal Client
summary: Build Signal bots and automation for your personal projects, groups, and communities.
sidebar_title: Home
order: 0
---

# Build Signal bots that actually work

Signal Client is a Python library that makes it easy to create Signal messaging bots. Whether you want to automate your group chats, get server notifications, or build helpful utilities for your friends and family, Signal Client handles the complexity so you can focus on what your bot does.

[Get started in 5 minutes](quickstart.md){: class="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-primary-foreground" }
[See what you can build](use-cases.md){: class="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2" }

## Why developers love Signal Client

- +heroicons:rocket-launch+ **Quick setup** — Link your Signal device once and start building immediately
- +heroicons:code-bracket+ **Simple API** — Write bot commands with clean, async Python functions  
- +heroicons:shield-check+ **Secure by default** — Built on Signal's end-to-end encryption with proper credential management
- +heroicons:wrench-screwdriver+ **Batteries included** — Message handling, error recovery, and debugging tools out of the box

## What you can build

!!! example "Popular bot ideas"
    - **Group moderator** — Welcome new members, enforce rules, manage spam
    - **Server monitor** — Get alerts when your services go down or deployments finish
    - **Family assistant** — Shared shopping lists, dinner polls, event reminders
    - **Utility bot** — Weather updates, quick calculations, fun commands

## Your bot in 3 steps

1. **[Link your device](quickstart.md#step-3-link-your-signal-device)** — Scan a QR code to connect Signal Client to your account
2. **[Write commands](quickstart.md#step-4-create-your-first-bot)** — Create async functions that respond to messages
3. **[Deploy and enjoy](operations.md)** — Run your bot locally or deploy it anywhere Python runs

/// details | Why not just use signal-cli directly?
Signal Client wraps the excellent [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) with a developer-friendly Python SDK. Instead of wrestling with REST APIs and message parsing, you get:

- **Clean async/await API** — Write bot logic with modern Python patterns
- **Automatic message handling** — Parse incoming messages, route to commands, handle errors
- **Built-in reliability** — Dead letter queues, retry logic, and health checks
- **Production ready** — Logging, metrics, and deployment guidance included

Perfect for developers who want to build bots, not infrastructure.
///

!!! tip "Ready to start?"
    The [quickstart guide](quickstart.md) will have you sending your first bot message in under 10 minutes. No Signal protocol knowledge required!
