# Comprehensive Refactoring Plan

This plan outlines a complete refactoring of the `signal-client` library to ensure 100% coverage and correctness of the `signal-cli-rest-api`, as defined in the `swagger.json`.

## 1. Core Refactoring

- [x] **Remove `auth_token`**
  - [x] `src/signal_client/container.py`
  - [x] `src/signal_client/infrastructure/api_clients/base_client.py`
- [x] **Implement `LinkPreview`**
  - [x] `src/signal_client/context.py`
  - [x] `src/signal_client/infrastructure/schemas/requests.py`
  - [x] Delete `src/signal_client/link_previews.py`

## 2. API Endpoint Audit

### 2.1. Accounts

- [x] `POST /v1/accounts/{number}/pin`
- [x] `DELETE /v1/accounts/{number}/pin`
- [x] `POST /v1/accounts/{number}/rate-limit-challenge`
- [x] `PUT /v1/accounts/{number}/settings`
- [x] `POST /v1/accounts/{number}/username`

### 2.2. Attachments

- [x] `DELETE /v1/attachments/{attachment}`

### 2.3. General

- [x] `GET /v1/configuration`
- [x] `POST /v1/configuration`
- [x] `GET /v1/configuration/{number}/settings`
- [x] `GET /v1/health`

### 2.4. Contacts

- [x] `PUT /v1/contacts/{number}`
- [x] `POST /v1/contacts/{number}/sync`
- [x] `GET /v1/contacts/{number}/{uuid}`
- [x] `GET /v1/contacts/{number}/{uuid}/avatar`

### 2.5. Devices

- [x] `POST /v1/devices/{number}`
- [x] `GET /v1/qrcodelink`
- [x] `POST /v1/register/{number}`
- [x] `POST /v1/register/{number}/verify/{token}`
- [x] `POST /v1/unregister/{number}`

### 2.6. Groups

- [x] `PUT /v1/groups/{number}/{groupid}`
- [x] `DELETE /v1/groups/{number}/{groupid}`
- [x] `POST /v1/groups/{number}/{groupid}/admins`
- [x] `DELETE /v1/groups/{number}/{groupid}/admins`
- [x] `GET /v1/groups/{number}/{groupid}/avatar`
- [x] `POST /v1/groups/{number}/{groupid}/block`
- [x] `POST /v1/groups/{number}/{groupid}/join`
- [x] `POST /v1/groups/{number}/{groupid}/members`
- [x] `DELETE /v1/groups/{number}/{groupid}/members`
- [x] `POST /v1/groups/{number}/{groupid}/quit`

### 2.7. Identities

- [x] `PUT /v1/identities/{number}/trust/{numberToTrust}`

### 2.8. Profiles

- [x] `PUT /v1/profiles/{number}`

### 2.9. Messages

- [x] `DELETE /v1/remote-delete/{number}`

Please review this comprehensive plan and let me know if you approve.
