---
title: Security & Credential Management
summary: Complete guide to securing Signal Client deployments, managing credentials, and implementing security best practices.
order: 301
---

# Security & Credential Management

This guide covers the critical security considerations for deploying Signal Client in production, including credential management, threat modeling, and security best practices.

!!! danger "Security Warning"
    Signal Client handles sensitive cryptographic credentials that provide access to your Signal account. Improper handling can lead to account compromise, message interception, or unauthorized access to private communications.

## Understanding Signal Credentials

### What's in the Credential Bundle

When you link a Signal device, several critical files are created in the secrets directory:

```bash
# Default location: ~/.local/share/signal-api/
├── data/
│   └── +1234567890/           # Your phone number
│       ├── account.json       # Account configuration
│       ├── identity.json      # Identity keys (CRITICAL)
│       ├── sessions/          # Session keys for contacts
│       ├── groups/            # Group membership data
│       └── attachments/       # Cached attachments
└── logs/                      # signal-cli logs
```

**Critical Files:**
- `identity.json`: Contains your Signal identity keys. **Loss = permanent account lockout**
- `account.json`: Account metadata and configuration
- `sessions/`: Encrypted session keys for all your contacts

### Security Implications

!!! danger "Credential Compromise Scenarios"
    **If credentials are compromised, attackers can:**
    - Read all your Signal messages (past and future)
    - Send messages as you to any contact
    - Join/leave groups on your behalf
    - Access message history and attachments
    - Impersonate you in Signal conversations

## Secure Storage Strategy

### Development Environment

For development and testing:

```bash
# Create secure directory
mkdir -p ~/.local/share/signal-api
chmod 700 ~/.local/share/signal-api

# Set restrictive permissions on credential files
find ~/.local/share/signal-api -type f -exec chmod 600 {} \;
find ~/.local/share/signal-api -type d -exec chmod 700 {} \;

# Verify permissions
ls -la ~/.local/share/signal-api/
# Should show: drwx------ (700) for directories
# Should show: -rw------- (600) for files
```

### Production Environment

#### Option 1: Kubernetes Secrets

```yaml
# signal-credentials-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: signal-credentials
  namespace: signal-bot
type: Opaque
data:
  # Base64 encoded credential files
  account.json: <base64-encoded-content>
  identity.json: <base64-encoded-content>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: signal-bot
spec:
  template:
    spec:
      containers:
      - name: signal-bot
        image: your-signal-bot:latest
        volumeMounts:
        - name: signal-credentials
          mountPath: /app/credentials
          readOnly: true
        env:
        - name: SIGNAL_CLIENT_SECRETS_DIR
          value: "/app/credentials"
      volumes:
      - name: signal-credentials
        secret:
          secretName: signal-credentials
          defaultMode: 0600  # Restrictive permissions
```

#### Option 2: HashiCorp Vault

```bash
# Store credentials in Vault
vault kv put secret/signal-bot/credentials \
  account.json=@account.json \
  identity.json=@identity.json

# Retrieve at runtime
vault kv get -field=account.json secret/signal-bot/credentials > /app/credentials/account.json
vault kv get -field=identity.json secret/signal-bot/credentials > /app/credentials/identity.json
chmod 600 /app/credentials/*.json
```

#### Option 3: AWS Secrets Manager

```python
import boto3
import json
import os
from pathlib import Path

def retrieve_signal_credentials():
    """Retrieve Signal credentials from AWS Secrets Manager."""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    
    try:
        # Retrieve the secret
        response = client.get_secret_value(SecretId='signal-bot/credentials')
        credentials = json.loads(response['SecretString'])
        
        # Create secure directory
        creds_dir = Path('/app/credentials')
        creds_dir.mkdir(mode=0o700, exist_ok=True)
        
        # Write credential files with secure permissions
        for filename, content in credentials.items():
            file_path = creds_dir / filename
            file_path.write_text(content)
            file_path.chmod(0o600)
            
        return str(creds_dir)
        
    except Exception as e:
        print(f"Failed to retrieve credentials: {e}")
        raise

# Use in your bot startup
credentials_dir = retrieve_signal_credentials()
os.environ['SIGNAL_CLIENT_SECRETS_DIR'] = credentials_dir
```

## Access Controls & Permissions

### File System Permissions

```bash
# Secure the entire Signal directory
chmod 700 /path/to/signal/credentials
chown signal-bot:signal-bot /path/to/signal/credentials

# Secure individual files
find /path/to/signal/credentials -type f -exec chmod 600 {} \;
find /path/to/signal/credentials -type d -exec chmod 700 {} \;

# Verify no world-readable files
find /path/to/signal/credentials -perm /o+r -ls
# Should return nothing
```

### Container Security

```dockerfile
# Dockerfile security best practices
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r signal && useradd -r -g signal signal

# Create secure directories
RUN mkdir -p /app/credentials && \
    chown signal:signal /app/credentials && \
    chmod 700 /app/credentials

# Switch to non-root user
USER signal

# Set secure environment
ENV SIGNAL_CLIENT_SECRETS_DIR=/app/credentials
ENV PYTHONPATH=/app

WORKDIR /app
COPY --chown=signal:signal . .

CMD ["python", "bot.py"]
```

### Network Security

```yaml
# Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: signal-bot-network-policy
spec:
  podSelector:
    matchLabels:
      app: signal-bot
  policyTypes:
  - Ingress
  - Egress
  egress:
  # Allow Signal servers
  - to: []
    ports:
    - protocol: TCP
      port: 443
  # Allow signal-cli REST API
  - to:
    - podSelector:
        matchLabels:
          app: signal-cli-rest-api
    ports:
    - protocol: TCP
      port: 8080
  # Deny all other traffic
  ingress: []  # No ingress allowed
```

## Credential Rotation & Lifecycle

### Rotation Schedule

| Credential Type | Rotation Frequency | Trigger Events |
|----------------|-------------------|----------------|
| Signal Device Link | Every 90 days | Personnel changes, suspected compromise |
| REST API Access | Every 30 days | Security incidents, maintenance |
| Container Images | Every release | Code changes, dependency updates |
| TLS Certificates | Every 90 days | Expiration, CA changes |

### Rotation Procedure

#### 1. Signal Device Re-linking

```bash
#!/bin/bash
# signal-rotation.sh - Rotate Signal device credentials

set -euo pipefail

echo "Starting Signal credential rotation..."

# 1. Backup current credentials
BACKUP_DIR="/secure/backups/signal-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r "$SIGNAL_CLIENT_SECRETS_DIR" "$BACKUP_DIR/"

# 2. Stop current bot
kubectl scale deployment signal-bot --replicas=0

# 3. Unlink old device (manual step)
echo "MANUAL STEP: Unlink old device in Signal app"
echo "Go to Signal Settings > Linked devices > Remove old device"
read -p "Press Enter when device is unlinked..."

# 4. Clear old credentials
rm -rf "$SIGNAL_CLIENT_SECRETS_DIR"/*

# 5. Start fresh linking process
echo "Starting new device linking..."
docker run -d --name signal-api-new \
  -p 8080:8080 \
  -v "$SIGNAL_CLIENT_SECRETS_DIR:/home/.local/share/signal-cli" \
  bbernhard/signal-cli-rest-api:latest

# 6. Generate new QR code
echo "Open: http://localhost:8080/v1/qrcodelink?device_name=signal-bot-$(date +%Y%m%d)"
read -p "Scan QR code and press Enter when linked..."

# 7. Verify new credentials
curl -s http://localhost:8080/v1/accounts | jq '.'

# 8. Update secrets in production
kubectl create secret generic signal-credentials-new \
  --from-file="$SIGNAL_CLIENT_SECRETS_DIR" \
  --dry-run=client -o yaml | kubectl apply -f -

# 9. Restart bot with new credentials
kubectl scale deployment signal-bot --replicas=1

echo "Credential rotation complete!"
```

#### 2. Automated Rotation with Vault

```python
import hvac
import schedule
import time
from pathlib import Path

class SignalCredentialRotator:
    def __init__(self, vault_url: str, vault_token: str):
        self.vault_client = hvac.Client(url=vault_url, token=vault_token)
        
    def rotate_credentials(self):
        """Rotate Signal credentials stored in Vault."""
        try:
            # 1. Backup current credentials
            current_creds = self.vault_client.secrets.kv.v2.read_secret_version(
                path='signal-bot/credentials'
            )
            
            backup_path = f'signal-bot/credentials-backup-{int(time.time())}'
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=backup_path,
                secret=current_creds['data']['data']
            )
            
            # 2. Trigger re-linking process
            self.trigger_relink()
            
            # 3. Update Vault with new credentials
            new_creds = self.collect_new_credentials()
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path='signal-bot/credentials',
                secret=new_creds
            )
            
            print("Credential rotation completed successfully")
            
        except Exception as e:
            print(f"Credential rotation failed: {e}")
            # Implement alerting here
            
    def trigger_relink(self):
        """Trigger the Signal device re-linking process."""
        # Implementation depends on your deployment method
        pass
        
    def collect_new_credentials(self) -> dict:
        """Collect new credentials after re-linking."""
        # Implementation depends on your setup
        pass

# Schedule rotation
rotator = SignalCredentialRotator(
    vault_url="https://vault.example.com",
    vault_token=os.environ['VAULT_TOKEN']
)

schedule.every(90).days.do(rotator.rotate_credentials)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check hourly
```

## Threat Modeling & Risk Assessment

### Threat Scenarios

#### 1. Credential Theft
**Risk:** High  
**Impact:** Complete account compromise  
**Mitigations:**
- Encrypted storage at rest
- Restrictive file permissions
- Regular rotation
- Access logging

#### 2. Container Escape
**Risk:** Medium  
**Impact:** Host system compromise  
**Mitigations:**
- Non-root containers
- Read-only filesystems
- Security contexts
- Network policies

#### 3. Supply Chain Attack
**Risk:** Medium  
**Impact:** Code injection, backdoors  
**Mitigations:**
- Dependency scanning
- Image vulnerability scanning
- Signed containers
- Minimal base images

#### 4. Insider Threat
**Risk:** Medium  
**Impact:** Unauthorized access  
**Mitigations:**
- Principle of least privilege
- Audit logging
- Multi-person approval
- Regular access reviews

### Security Checklist

#### Pre-Deployment

- [ ] Credentials stored in secure vault (not filesystem)
- [ ] File permissions set to 600/700
- [ ] Non-root container user configured
- [ ] Network policies restrict traffic
- [ ] TLS enabled for all communications
- [ ] Dependency vulnerabilities scanned
- [ ] Security contexts applied
- [ ] Secrets not in container images
- [ ] Audit logging enabled
- [ ] Backup and recovery tested

#### Runtime Monitoring

- [ ] Failed authentication attempts logged
- [ ] Unusual API usage patterns detected
- [ ] File access monitoring enabled
- [ ] Network traffic anomalies tracked
- [ ] Resource usage monitored
- [ ] Error rates tracked
- [ ] Performance metrics collected

#### Incident Response

- [ ] Incident response plan documented
- [ ] Emergency contacts identified
- [ ] Credential revocation procedures tested
- [ ] Backup restoration procedures verified
- [ ] Communication plan established
- [ ] Post-incident review process defined

## Compliance & Auditing

### Audit Logging

```python
import logging
import json
from datetime import datetime

class SecurityAuditLogger:
    def __init__(self):
        self.logger = logging.getLogger('signal_security_audit')
        handler = logging.FileHandler('/var/log/signal-security.log')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_credential_access(self, action: str, user: str, success: bool):
        """Log credential access attempts."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'credential_access',
            'action': action,
            'user': user,
            'success': success,
            'source_ip': self.get_source_ip()
        }
        self.logger.info(json.dumps(event))
    
    def log_message_operation(self, operation: str, recipient: str, success: bool):
        """Log message operations."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'message_operation',
            'operation': operation,
            'recipient_hash': self.hash_phone_number(recipient),
            'success': success
        }
        self.logger.info(json.dumps(event))
    
    def hash_phone_number(self, phone: str) -> str:
        """Hash phone number for privacy."""
        import hashlib
        return hashlib.sha256(phone.encode()).hexdigest()[:16]
    
    def get_source_ip(self) -> str:
        """Get source IP address."""
        # Implementation depends on your environment
        return "unknown"

# Usage in your bot
audit_logger = SecurityAuditLogger()

async def secure_message_handler(context: Context) -> None:
    try:
        # Your message handling logic
        response = SendMessageRequest(message="Hello!", recipients=[])
        await context.reply(response)
        
        # Log successful operation
        audit_logger.log_message_operation(
            operation="reply",
            recipient=context.message.source,
            success=True
        )
    except Exception as e:
        # Log failed operation
        audit_logger.log_message_operation(
            operation="reply",
            recipient=context.message.source,
            success=False
        )
        raise
```

### Compliance Requirements

#### GDPR Compliance

```python
class GDPRCompliantBot:
    def __init__(self):
        self.data_retention_days = 30
        self.user_consents = {}
    
    async def handle_data_request(self, context: Context) -> None:
        """Handle GDPR data requests."""
        user = context.message.source
        message = context.message.message.lower()
        
        if "delete my data" in message:
            await self.delete_user_data(user)
            response = SendMessageRequest(
                message="Your data has been deleted as requested.",
                recipients=[]
            )
            await context.reply(response)
        
        elif "export my data" in message:
            data_export = await self.export_user_data(user)
            response = SendMessageRequest(
                message=f"Your data export: {data_export}",
                recipients=[]
            )
            await context.reply(response)
    
    async def delete_user_data(self, user: str) -> None:
        """Delete all data for a user."""
        # Implementation depends on your data storage
        pass
    
    async def export_user_data(self, user: str) -> str:
        """Export all data for a user."""
        # Implementation depends on your data storage
        return "Data export would go here"
```

## Emergency Procedures

### Credential Compromise Response

```bash
#!/bin/bash
# emergency-response.sh - Emergency credential compromise response

echo "EMERGENCY: Signal credential compromise detected!"

# 1. Immediately stop all bots
kubectl scale deployment signal-bot --replicas=0

# 2. Revoke compromised device
echo "URGENT: Manually unlink compromised device in Signal app"
echo "Signal Settings > Linked devices > Remove compromised device"

# 3. Rotate all related credentials
./rotate-all-credentials.sh

# 4. Review audit logs
echo "Reviewing audit logs for suspicious activity..."
grep -i "credential_access" /var/log/signal-security.log | tail -100

# 5. Notify security team
curl -X POST https://alerts.example.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"alert": "Signal credential compromise", "severity": "critical"}'

# 6. Generate incident report
echo "Generating incident report..."
./generate-incident-report.sh

echo "Emergency response initiated. Manual intervention required."
```

### Recovery Procedures

1. **Assess the scope** of the compromise
2. **Revoke all affected credentials** immediately
3. **Re-link Signal device** with new credentials
4. **Update all production secrets** in secure storage
5. **Review audit logs** for unauthorized activity
6. **Test all systems** before resuming operations
7. **Document the incident** and lessons learned
8. **Update security procedures** based on findings

## Security Best Practices Summary

### Development
- Use separate Signal accounts for development and production
- Never commit credentials to version control
- Use environment variables for configuration
- Implement proper error handling to avoid credential leaks

### Deployment
- Use non-root containers with minimal privileges
- Implement network segmentation and policies
- Enable comprehensive audit logging
- Use encrypted storage for all credentials

### Operations
- Monitor for unusual activity patterns
- Implement automated credential rotation
- Maintain incident response procedures
- Conduct regular security reviews

### Monitoring
- Track failed authentication attempts
- Monitor file access to credential directories
- Alert on unusual API usage patterns
- Log all administrative actions

!!! warning "Regular Security Reviews"
    Conduct quarterly security reviews of your Signal Client deployment, including:
    - Credential rotation verification
    - Access control audits
    - Vulnerability assessments
    - Incident response testing
    - Compliance validation

---

**Next Steps:**
- [Operations Guide](operations.md) - Production deployment and monitoring
- [Troubleshooting](diagnostics.md) - Common security issues and solutions
- [Architecture](architecture.md) - Understanding the security model
