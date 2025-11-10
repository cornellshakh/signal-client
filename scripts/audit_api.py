# scripts/audit_api.py
import inspect
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

# Add the project root's 'src' directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


from signal_client.infrastructure.api_clients import (  # noqa: E402
    accounts_client,
    attachments_client,
    contacts_client,
    devices_client,
    general_client,
    groups_client,
    identities_client,
    messages_client,
    profiles_client,
    reactions_client,
    receipts_client,
    search_client,
    sticker_packs_client,
)

# Swagger spec published by the upstream signal-cli REST API project.
SWAGGER_URL = "https://bbernhard.github.io/signal-cli-rest-api/src/docs/swagger.json"
SWAGGER_REQUEST_TIMEOUT = 30
ALLOWED_SWAGGER_SCHEMES = frozenset({"https"})

# A mapping from the client module to the tag used in the swagger spec.
CLIENT_TAG_MAPPING = {
    "accounts_client": "Accounts",
    "attachments_client": "Attachments",
    "contacts_client": "Contacts",
    "devices_client": "Devices",
    "general_client": "General",
    "groups_client": "Groups",
    "identities_client": "Identities",
    "messages_client": "Messages",
    "profiles_client": "Profiles",
    "reactions_client": "Reactions",
    "receipts_client": "Receipts",
    "search_client": "Search",
    "sticker_packs_client": "Sticker packs",
}


class SwaggerSpecDownloadError(RuntimeError):
    """Raised when downloading the swagger spec fails."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Failed to download swagger spec from {url}")
        self.url = url


def _validate_swagger_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in ALLOWED_SWAGGER_SCHEMES:
        message = (
            f"Unsupported URL scheme '{parsed.scheme}' for swagger spec. "
            f"Allowed schemes: {sorted(ALLOWED_SWAGGER_SCHEMES)}"
        )
        raise ValueError(message)


def snake_to_camel(snake_case_string: str) -> str:
    """Converts a snake_case string to camelCase."""
    parts = snake_case_string.split("_")
    return parts[0] + "".join(x.title() for x in parts[1:])


def get_swagger_spec() -> dict[str, Any]:
    """Loads the swagger specification from the upstream hosted location."""
    _validate_swagger_url(SWAGGER_URL)
    try:
        with urlopen(  # noqa: S310 - scheme validated in _validate_swagger_url
            SWAGGER_URL, timeout=SWAGGER_REQUEST_TIMEOUT
        ) as response:
            payload = response.read().decode("utf-8")
    except URLError as exc:  # pragma: no cover - network error passthrough
        raise SwaggerSpecDownloadError(SWAGGER_URL) from exc
    return json.loads(payload)


def get_client_methods() -> dict[str, set[str]]:
    """
    Inspects the client modules and returns a dictionary of client names
    and their public methods.
    """
    client_methods: dict[str, set[str]] = {}
    client_modules = [
        accounts_client,
        attachments_client,
        contacts_client,
        devices_client,
        general_client,
        groups_client,
        identities_client,
        messages_client,
        profiles_client,
        reactions_client,
        receipts_client,
        search_client,
        sticker_packs_client,
    ]

    for module in client_modules:
        client_name = module.__name__.split(".")[-1]
        methods = {
            name
            for name, func in inspect.getmembers(module, inspect.isfunction)
            if not name.startswith("_")
        }
        client_methods[client_name] = methods

    return client_methods


def get_swagger_operations() -> dict[str, set[str]]:
    """
    Parses the swagger spec and returns a dictionary of tags (clients)
    and their operationIds.
    """
    spec = get_swagger_spec()
    swagger_operations: dict[str, set[str]] = {}

    for path_data in spec["paths"].values():
        for operation_data in path_data.values():
            tags = operation_data.get("tags", [])
            operation_id = operation_data.get("operationId")
            if tags and operation_id:
                for tag in tags:
                    if tag not in swagger_operations:
                        swagger_operations[tag] = set()
                    swagger_operations[tag].add(operation_id)

    return swagger_operations


def audit_api_parity() -> bool:
    """
    Compares the client methods with the swagger operations and prints
    any discrepancies.
    """
    print("Starting API parity audit...")
    client_methods = get_client_methods()
    swagger_operations = get_swagger_operations()
    discrepancies_found = False

    # Invert the mapping for easier lookup
    tag_to_client_mapping = {v: k for k, v in CLIENT_TAG_MAPPING.items()}

    for tag, operations in swagger_operations.items():
        client_name = tag_to_client_mapping.get(tag)
        if not client_name:
            print(f"Warning: No client mapping found for tag '{tag}'")
            continue

        client_ops = {
            snake_to_camel(method) for method in client_methods.get(client_name, set())
        }
        swagger_ops = set(operations)

        missing_in_client = swagger_ops - client_ops
        if missing_in_client:
            discrepancies_found = True
            print(f"\nDiscrepancies found in '{client_name}':")
            print("  Methods missing in the client:")
            for op in sorted(missing_in_client):
                print(f"    - {op}")

        extra_in_client = client_ops - swagger_ops
        if extra_in_client:
            discrepancies_found = True
            print(f"\nDiscrepancies found in '{client_name}':")
            print("  Extra methods in the client (not in swagger spec):")
            for op in sorted(extra_in_client):
                print(f"    - {op}")

    if not discrepancies_found:
        print("\nSuccess! API parity check passed with no discrepancies.")
        return True
    print("\nAPI parity check failed.")
    return False


def main() -> None:
    """
    Runs the API parity audit and exits with the appropriate status code.
    """
    if not audit_api_parity():
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
