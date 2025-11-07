# Production Secrets Management

## 1. Introduction

This document provides guidance on best practices for managing secrets in production environments. While `.env` files are convenient for local development, they are not suitable for production due to security risks.

## 2. Recommended Tools

We recommend using a dedicated secrets management tool for production environments. Some popular options include:

- **HashiCorp Vault:** A powerful, open-source tool for managing secrets and protecting sensitive data.
- **Cloud-Native Solutions:**
  - **AWS Secrets Manager:** A fully managed secrets management service for AWS environments.
  - **Google Cloud Secret Manager:** A secure and convenient storage system for API keys, passwords, certificates, and other sensitive data.
  - **Azure Key Vault:** A cloud service for securely storing and accessing secrets.

## 3. Best Practices

- **Do not commit secrets to version control.** This includes `.env` files, API keys, and other sensitive information.
- **Use environment variables to inject secrets into your application.** This is a more secure approach than hardcoding secrets in your code.
- **Rotate secrets regularly.** This helps to minimize the impact of a potential breach.
- **Audit access to secrets.** This will help you to identify and investigate any suspicious activity.
- **Coordinate rotations with operations runbooks.** See [Operations](./operations.md) for credential rotation steps and post-rotation validation.
