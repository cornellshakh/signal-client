"""Tests for the logging observability module."""

import structlog

from signal_client.observability.logging import (
    PIIRedactingProcessor,
    ensure_structlog_configured,
    reset_structlog_configuration_guard,
)


def test_pii_redacting_processor():
    """Test the PII redacting processor."""
    processor = PIIRedactingProcessor()
    event_dict = {
        "message": "This is a test message",
        "body": "This is the body",
        "text": "This is the text",
        "name": "This is the name",
        "other": "This should not be redacted",
    }
    result = processor(None, "", event_dict)
    assert result == {
        "message": "[REDACTED]",
        "body": "[REDACTED]",
        "text": "[REDACTED]",
        "name": "[REDACTED]",
        "other": "This should not be redacted",
    }


def test_ensure_structlog_configured_with_redaction_enabled():
    """Test that structlog is configured with PII redaction enabled."""
    reset_structlog_configuration_guard()
    ensure_structlog_configured(redaction_enabled=True)
    assert any(
        isinstance(p, PIIRedactingProcessor)
        for p in structlog.get_config()["processors"]
    )
    structlog.configure(processors=[])


def test_ensure_structlog_configured_with_redaction_disabled():
    """Test that structlog is configured with PII redaction disabled."""
    reset_structlog_configuration_guard()
    ensure_structlog_configured(redaction_enabled=False)
    assert not any(
        isinstance(p, PIIRedactingProcessor)
        for p in structlog.get_config()["processors"]
    )
    structlog.configure(processors=[])
