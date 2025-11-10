# Schema Compatibility

Signal-client tracks API shapes in `cli_rest_api_swagger.json`.

## Validation

```bash
python -m signal_client.compatibility --strict
```

## When to run

- Before upgrading dependencies that talk to Signal REST
- During CI for deployments

Document breaking changes in [Changelog](../appendix/changelog.md).
