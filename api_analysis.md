# Signal CLI REST API Analysis

This document outlines the structure of the Signal CLI REST API based on the provided swagger.json file.

## General

- `GET /v1/about`: Lists general information about the API.
- `GET /v1/configuration`: List the REST API configuration.
- `POST /v1/configuration`: Set the REST API configuration.
- `GET /v1/configuration/{number}/settings`: List account specific settings.
- `POST /v1/configuration/{number}/settings`: Set account specific settings.
- `GET /v1/health`: API Health Check.

## Devices

- `GET /v1/devices/{number}`: List linked devices.
- `POST /v1/devices/{number}`: Links another device to this device.
- `GET /v1/qrcodelink`: Link device and generate QR code.
- `POST /v1/register/{number}`: Register a phone number.
- `POST /v1/register/{number}/verify/{token}`: Verify a registered phone number.
- `POST /v1/unregister/{number}`: Unregister a phone number.

## Accounts

- `GET /v1/accounts`: List all accounts.
- `POST /v1/accounts/{number}/pin`: Set Pin.
- `DELETE /v1/accounts/{number}/pin`: Remove Pin.
- `POST /v1/accounts/{number}/rate-limit-challenge`: Lift rate limit restrictions by solving a captcha.
- `PUT /v1/accounts/{number}/settings`: Update the account settings.
- `POST /v1/accounts/{number}/username`: Set a username.
- `DELETE /v1/accounts/{number}/username`: Remove a username.

## Groups

- `GET /v1/groups/{number}`: List all Signal Groups.
- `POST /v1/groups/{number}`: Create a new Signal Group.
- `GET /v1/groups/{number}/{groupid}`: List a Signal Group.
- `PUT /v1/groups/{number}/{groupid}`: Update the state of a Signal Group.
- `DELETE /v1/groups/{number}/{groupid}`: Delete a Signal Group.
- `POST /v1/groups/{number}/{groupid}/admins`: Add one or more admins to an existing Signal Group.
- `DELETE /v1/groups/{number}/{groupid}/admins`: Remove one or more admins from an existing Signal Group.
- `GET /v1/groups/{number}/{groupid}/avatar`: Returns the avatar of a Signal Group.
- `POST /v1/groups/{number}/{groupid}/block`: Block a Signal Group.
- `POST /v1/groups/{number}/{groupid}/join`: Join a Signal Group.
- `POST /v1/groups/{number}/{groupid}/members`: Add one or more members to an existing Signal Group.
- `DELETE /v1/groups/{number}/{groupid}/members`: Remove one or more members from an existing Signal Group.
- `POST /v1/groups/{number}/{groupid}/quit`: Quit a Signal Group.

## Messages

- `GET /v1/receive/{number}`: Receive Signal Messages.
- `DELETE /v1/remote-delete/{number}`: Delete a signal message.
- `POST /v1/send`: Send a signal message (deprecated).
- `PUT /v1/typing-indicator/{number}`: Show Typing Indicator.
- `DELETE /v1/typing-indicator/{number}`: Hide Typing Indicator.
- `POST /v2/send`: Send a signal message.

## Attachments

- `GET /v1/attachments`: List all attachments.
- `GET /v1/attachments/{attachment}`: Serve Attachment.
- `DELETE /v1/attachments/{attachment}`: Remove attachment.

## Profiles

- `PUT /v1/profiles/{number}`: Update Profile.

## Identities

- `GET /v1/identities/{number}`: List Identities.
- `PUT /v1/identities/{number}/trust/{numberToTrust}`: Trust Identity.

## Reactions

- `POST /v1/reactions/{number}`: Send a reaction.
- `DELETE /v1/reactions/{number}`: Remove a reaction.

## Receipts

- `POST /v1/receipts/{number}`: Send a receipt.

## Search

- `GET /v1/search/{number}`: Check if one or more phone numbers are registered with the Signal Service.

## Sticker Packs

- `GET /v1/sticker-packs/{number}`: List Installed Sticker Packs.
- `POST /v1/sticker-packs/{number}`: Add Sticker Pack.
