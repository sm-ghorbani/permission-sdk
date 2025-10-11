"""Utility functions for the Permission SDK.

This module contains helper functions for validation, formatting, and other utilities.
"""

import re
from typing import Any

from permission_sdk.exceptions import ValidationError

# Regular expressions for validation
SUBJECT_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+:[a-zA-Z0-9_@.\-]+$")
SCOPE_PATTERN = re.compile(r"^[a-z0-9_.-]+$")
ACTION_PATTERN = re.compile(r"^[a-z0-9_-]+$")


def validate_subject_identifier(identifier: str) -> None:
    """Validate subject identifier format.

    Subject identifiers must follow the format 'type:id' where:
    - type: alphanumeric, underscore, or hyphen
    - id: alphanumeric, underscore, hyphen, dot, or @ symbol

    Args:
        identifier: Subject identifier to validate

    Raises:
        ValidationError: If identifier format is invalid

    Example:
        >>> validate_subject_identifier("user:john.doe")  # Valid
        >>> validate_subject_identifier("role:editor")    # Valid
        >>> validate_subject_identifier("invalid")        # Raises ValidationError
    """
    if not identifier:
        raise ValidationError("Subject identifier cannot be empty", field="subject")

    if len(identifier) < 3:
        raise ValidationError(
            "Subject identifier must be at least 3 characters long",
            field="subject",
        )

    if not SUBJECT_PATTERN.match(identifier):
        raise ValidationError(
            f"Invalid subject identifier format: '{identifier}'. "
            "Expected format: 'type:id' (e.g., 'user:123', 'role:editor')",
            field="subject",
        )

    # Ensure it contains a colon separator
    if ":" not in identifier:
        raise ValidationError(
            f"Subject identifier must contain ':' separator: '{identifier}'",
            field="subject",
        )


def validate_scope_identifier(identifier: str) -> None:
    """Validate scope identifier format.

    Scope identifiers must be lowercase and contain only:
    - Lowercase letters
    - Numbers
    - Dots (.) for hierarchical scopes
    - Hyphens (-) and underscores (_)

    Args:
        identifier: Scope identifier to validate

    Raises:
        ValidationError: If identifier format is invalid

    Example:
        >>> validate_scope_identifier("documents.management")  # Valid
        >>> validate_scope_identifier("users_admin")           # Valid
        >>> validate_scope_identifier("Invalid.Scope")         # Raises ValidationError
    """
    if not identifier:
        raise ValidationError("Scope identifier cannot be empty", field="scope")

    if not SCOPE_PATTERN.match(identifier):
        raise ValidationError(
            f"Invalid scope identifier format: '{identifier}'. "
            "Scope must be lowercase and contain only letters, "
            "numbers, dots, hyphens, and underscores",
            field="scope",
        )


def validate_action(action: str) -> None:
    """Validate permission action format.

    Actions must be lowercase and contain only:
    - Lowercase letters
    - Numbers
    - Hyphens (-) and underscores (_)

    Args:
        action: Permission action to validate

    Raises:
        ValidationError: If action format is invalid

    Example:
        >>> validate_action("read")       # Valid
        >>> validate_action("edit")       # Valid
        >>> validate_action("delete")     # Valid
        >>> validate_action("Invalid")    # Raises ValidationError
    """
    if not action:
        raise ValidationError("Action cannot be empty", field="action")

    if not ACTION_PATTERN.match(action):
        raise ValidationError(
            f"Invalid action format: '{action}'. "
            "Action must be lowercase and contain only "
            f"letters, numbers, hyphens, and underscores",
            field="action",
        )


def validate_grant_request(
    subject: str,
    scope: str,
    action: str,
    validate: bool = True,
) -> None:
    """Validate all fields of a grant/revoke request.

    Args:
        subject: Subject identifier
        scope: Scope identifier
        action: Permission action
        validate: Whether to perform validation (default: True)

    Raises:
        ValidationError: If any field is invalid

    Example:
        >>> validate_grant_request("user:123", "documents.management", "read")
    """
    if not validate:
        return

    validate_subject_identifier(subject)
    validate_scope_identifier(scope)
    validate_action(action)


def chunk_list(items: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split a list into chunks of specified size.

    This is useful for batch operations that have size limits.

    Args:
        items: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks

    Example:
        >>> items = [1, 2, 3, 4, 5, 6, 7]
        >>> chunks = chunk_list(items, 3)
        >>> print(chunks)  # [[1, 2, 3], [4, 5, 6], [7]]
    """
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def normalize_url(url: str) -> str:
    """Normalize URL by removing trailing slashes.

    Args:
        url: URL to normalize

    Returns:
        Normalized URL

    Example:
        >>> normalize_url("https://api.example.com/")
        'https://api.example.com'
    """
    return url.rstrip("/")


def parse_subject_identifier(identifier: str) -> tuple[str, str]:
    """Parse subject identifier into type and ID components.

    Args:
        identifier: Subject identifier (format: 'type:id')

    Returns:
        Tuple of (type, id)

    Raises:
        ValidationError: If identifier format is invalid

    Example:
        >>> subject_type, subject_id = parse_subject_identifier("user:john.doe")
        >>> print(subject_type)  # "user"
        >>> print(subject_id)    # "john.doe"
    """
    validate_subject_identifier(identifier)

    parts = identifier.split(":", 1)
    if len(parts) != 2:
        raise ValidationError(
            f"Invalid subject identifier format: '{identifier}'",
            field="subject",
        )

    return parts[0], parts[1]
