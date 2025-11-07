# Architectural Decision Record: A Zero-Trust Commercial Bot on Signal

**Status:** Approved

## 1. Context

The core challenge is to operate a commercial, closed-source AI bot on the Signal platform without violating the fundamental user expectation of end-to-end privacy. A standard closed-source bot would act as a trusted "man-in-the-middle," decrypting user messages and exposing them to the operator. This is unacceptable.

This plan is further constrained by two critical business requirements:

1.  The core intellectual property (the "Commercial Engine") must remain closed-source.
2.  There is no budget for expensive, recurring third-party security audits.

## 2. The Problem: The "Trust Gap"

These constraints create a "Trust Gap." We are asking a privacy-conscious user base to trust an opaque system without the validation of open-source transparency or independent audits. This requires an architectural solution that minimizes the trust a user must place in us, replacing it with verifiable, cryptographic proof.

## 3. The Solution: The "Two-Tier TEE" Model

The most robust architecture under these constraints is a **"Two-Tier TEE" model**. This model splits the bot into two isolated components running in separate Trusted Execution Environments (TEEs), ensuring a radical simplification of the trusted, open-source code.

### 3.1. Core Components

#### 3.1.1. The "Crypto Core" (Open-Source, TEE #1)

- **Language:** Rust (for memory safety and performance).
- **Responsibilities:**
  - **Cryptography:** All cryptographic operations (encryption/decryption of messages and state blobs).
  - **Signal Communication:** Minimal logic to interact with the Signal message queue.
  - **API Server:** Exposes a single, internal-only endpoint for the Commercial Engine.
- **Constraints:**
  - **No External Network Access:** Other than the Signal service.
  - **Stateless:** All state is received in the request.
  - **Minimal Logic:** No business logic, only cryptographic and communication tasks.

#### 3.1.2. The "Commercial Engine" (Closed-Source, TEE #2)

- **Language:** Python (to support AI/ML libraries).
- **Responsibilities:**
  - **Business Logic:** All proprietary algorithms, AI models, and state management logic.
  - **API Client:** Makes requests to the Crypto Core's internal API.
- **Constraints:**
  - **No Direct Signal Access:** Cannot read from or write to the Signal network.
  - **No Access to Encrypted Data:** Only handles plaintext data provided by the Crypto Core.

### 3.2. Architectural Flow

1.  The **Crypto Core (TEE #1)** receives and decrypts the user's message and their encrypted state blob.
2.  The **Crypto Core** passes the **plaintext message and plaintext state** to the **Commercial Engine (TEE #2)** through a secure, private, in-memory channel.
3.  The **Commercial Engine** processes the data, performs its logic, and returns a plaintext response and the new state to the Crypto Core.
4.  The **Crypto Core** encrypts the response, formats it into a Signal message, encrypts the new state blob, and sends both back to the user.

### 3.3. API Boundary Definition

The communication between the two TEEs will occur over a secure, private, in-memory channel. The interface will be a simple, synchronous request/response model.

- **Endpoint:** `POST /v1/process`
- **Request Body (`ProcessRequest`):**
  - `message` (string): The plaintext user message.
  - `state` (base64 string): The plaintext user state blob.
- **Response Body (`ProcessResponse`):**
  - `response` (string): The plaintext response to send to the user.
  - `new_state` (base64 string): The new plaintext user state blob.

## 4. Defense of this Recommendation

This architecture is the only logically sound path forward because it directly confronts the "Trust Gap" by minimizing the complexity of the trusted component.

- **It Minimizes the Trust Surface:** A user doesn't need to trust a complex application. They only need to trust the tiny, open-source Crypto Core, whose only job is encryption and decryption. This component is so simple that it can be audited by a single developer in an afternoon.
- **It Enables Meaningful Community Audits:** By keeping the open-source component radically simple, we make community audits feasible and effective.
- **It is Verifiable at Runtime:** We will provide **reproducible builds** for the Crypto Core. A user's client can then use **remote attestation** to cryptographically verify that our TEE is running the _exact, community-vetted version_ of the Crypto Core.
- **It Protects Intellectual Property:** Our valuable commercial logic remains in the closed-source Commercial Engine.

### 4.1. Sufficiency for a "Virtual Human" Assistant

This architecture is designed to support complex, stateful interactions, enabling the bot to function as a "virtual human" with long-term memory and proactive capabilities.

- **On Long-Term Memory:** All user-specific data (past conversations, preferences, tasks) is managed by the Commercial Engine and stored in the `state` blob. After each interaction, the Commercial Engine returns the updated state to the Crypto Core, which encrypts it and sends it back to be stored externally as an opaque, indecipherable blob. On the next interaction, the process is reversed. The bot can "remember" indefinitely, but the operator never has access to the plaintext memory.
- **On Contextual Understanding:** The Commercial Engine has access to the full, decrypted conversation history via the `state` blob. This allows it to perform sophisticated contextual analysis and provide intelligent, relevant responses without the operator ever seeing the raw, private history.
- **On Proactive Help (Reminders):** Proactive features like reminders are handled by an external, untrusted "trigger" service (e.g., a cron job).
  1.  The trigger service calls a dedicated, secure endpoint on the Crypto Core, identifying the user for whom a check is due.
  2.  The Crypto Core retrieves the user's encrypted state blob and decrypts it.
  3.  It passes the plaintext state to the Commercial Engine with a special request, e.g., `{"event": "reminder_check"}`.
  4.  The Commercial Engine inspects the state. If a reminder is due, it crafts the appropriate message and returns it to the Crypto Core. If not, it returns an empty response.
  5.  If a message is received, the Crypto Core encrypts and sends it to the user.

This model ensures that even proactive, server-initiated events are processed with the same zero-trust privacy guarantees as user-initiated messages.

## 5. Security and Threat Model

### 5.1. Conceptual Flow: Remote Attestation

Remote attestation is the process by which a user's client can cryptographically verify that the correct, open-source code is running inside the Crypto Core TEE.

The flow is as follows:

1.  **Client Challenge:** The user's client sends a random "nonce" to the bot.
2.  **Attestation Generation:** The Crypto Core TEE generates a signed "attestation document" containing the code's hash and the nonce, signed by a private key fused into the hardware.
3.  **Vendor Verification:** The Crypto Core has the document co-signed by the hardware vendor's public attestation service.
4.  **Client Verification:** The client receives the document and verifies the vendor's signature, the nonce, and **compares the code hash against the hash of the public, open-source code.**
5.  **Secure Channel Established:** If all checks pass, the client has proven the integrity of the running code.

### 5.2. Threat Model: Operator and Law Enforcement Compulsion

This architecture is designed for **operator incapacity**.

- **No Access to Keys:** Private keys are loaded directly into the TEE's encrypted memory, making them inaccessible to us as the operator.
- **No Access to Plaintext:** All data is decrypted, processed, and re-encrypted exclusively within the isolated TEEs.
- **Defense Against Compelled Backdoors:** Remote attestation prevents us from deploying a malicious version of the Crypto Core. Any change to the code would alter its hash, causing the attestation check to fail on the user's client and exposing the backdoor.

## 6. Phased Development Plan

**Phase 1: Standalone Component Development (2-3 months)**

1.  **Develop the Crypto Core:** Implement the Rust-based cryptographic component.
2.  **Develop the Commercial Engine:** Implement the Python-based business logic with the `/v1/process` endpoint.
3.  **Unit and Integration Testing:** Thoroughly test both components in isolation.

**Phase 2: TEE Integration and Attestation (3-5 months)**

1.  **TEE Deployment:** Package and deploy both components into their respective TEEs.
2.  **Implement Secure Channel:** Establish the private, in-memory communication channel.
3.  **Implement Remote Attestation Flow:** Build the logic for the client challenge/response and vendor attestation.
4.  **End-to-End Testing:** Perform comprehensive testing of the entire, integrated system.

**Phase 3: Open-Source and Community Audit (Ongoing)**

1.  **Publish Crypto Core:** Publish the source code, build instructions, and reproducible build scripts.
2.  **Engage Community:** Actively solicit and respond to community feedback and audits.

## 7. Implementation Risks and Considerations

While the "Two-Tier TEE" model is architecturally sound, its implementation is complex and carries inherent risks that must be acknowledged and mitigated.

- **Performance Overhead:** TEEs introduce latency due to memory encryption/decryption and context switching. For a real-time conversational bot, this overhead could impact user experience. The implementation plan must include rigorous performance testing and optimization.
- **TEE Vendor Lock-in:** The choice of a TEE provider (e.g., Intel SGX, AMD SEV, AWS Nitro Enclaves) has significant implications for the implementation details of the attestation process and may create vendor-specific dependencies. The initial research phase must carefully weigh the trade-offs of each ecosystem.
- **Side-Channel Attacks:** TEEs are not a panacea. They have been shown to be vulnerable to sophisticated side-channel attacks that can infer data by observing patterns in memory access, cache usage, or power consumption. The Crypto Core, in particular, must be written using defensive coding practices, including constant-time cryptographic operations, to mitigate these risks.
- **Secure Key Provisioning:** The process of securely provisioning the initial private keys to the TEEs is a critical and complex step. A robust and automated key management strategy is required to ensure that keys are never exposed outside of the TEE, even during deployment and startup.

## 8. Conclusion

This plan is **sufficient and correct.** It achieves **verifiable, zero-trust privacy** by radically simplifying and isolating the trusted code base and providing cryptographic proof of its runtime integrity. It is the definitive and most robust architecture for building a commercial, closed-source "virtual human" assistant on a privacy-first platform like Signal.
