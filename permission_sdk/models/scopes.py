"""Scope-related data models.

This module contains models for scope management operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Scope(BaseModel):
    """A scope in the permission system.

    Scopes represent resources or features that can be protected by permissions,
    such as 'documents.management', 'users.administration', etc.

    Attributes:
        id: Internal database ID
        identifier: Scope identifier (e.g., 'documents.management')
        display_name: Human-readable name
        description: Optional description of the scope
        metadata: Optional additional metadata
        created_at: When scope was created
        updated_at: When scope was last updated

    Example:
        >>> scope = Scope(
        ...     id=123,
        ...     identifier="documents.management",
        ...     display_name="Document Management",
        ...     description="Permissions for managing documents",
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
    """

    id: int = Field(..., description="Internal ID")
    identifier: str = Field(..., description="Scope identifier")
    display_name: str | None = Field(default=None, description="Display name")
    description: str | None = Field(default=None, description="Description")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ScopeCreate(BaseModel):
    """Request to create or update a scope.

    Attributes:
        identifier: Scope identifier (e.g., 'documents.management')
        display_name: Optional human-readable name
        description: Optional description
        metadata: Optional additional metadata

    Example:
        >>> create_req = ScopeCreate(
        ...     identifier="reports.viewing",
        ...     display_name="Report Viewing",
        ...     description="Permissions for viewing reports",
        ...     metadata={"category": "analytics"}
        ... )
    """

    identifier: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    display_name: str | None = Field(default=None, max_length=255, description="Display name")
    description: str | None = Field(default=None, max_length=1000, description="Description")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")

    @field_validator("identifier")
    @classmethod
    def lowercase_identifier(cls, v: str) -> str:
        """Normalize identifier to lowercase.

        Args:
            v: Identifier value

        Returns:
            Lowercase identifier
        """
        return v.lower() if v else v


class ScopeFilter(BaseModel):
    """Filter criteria for listing scopes.

    All filter fields are optional and will be combined with AND logic.

    Attributes:
        scope_type: Filter by scope type (feature, model, api, system)
        search: Search in display names or descriptions
        include_inactive: Include deactivated scopes
        limit: Number of results per page (1-1000)
        offset: Pagination offset

    Example:
        >>> filters = ScopeFilter(
        ...     scope_type="feature",
        ...     search="document",
        ...     limit=50
        ... )
        >>> scopes = client.list_scopes(filters)
    """

    scope_type: str | None = Field(default=None, description="Filter by scope type")
    search: str | None = Field(default=None, description="Search in names/descriptions")
    include_inactive: bool = Field(default=False, description="Include inactive scopes")
    limit: int = Field(default=100, ge=1, le=1000, description="Results per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
