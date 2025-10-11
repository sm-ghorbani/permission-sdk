"""Subject-related data models.

This module contains models for subject management operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Subject(BaseModel):
    """A subject in the permission system.

    Subjects represent entities that can be granted permissions, such as
    users, roles, groups, or API clients.

    Attributes:
        id: Internal database ID
        identifier: Subject identifier (format: 'type:id')
        subject_type: Type of subject (user, role, group, etc.)
        subject_id: ID portion of the identifier
        display_name: Human-readable name
        tenant_id: Optional tenant identifier for multi-tenancy
        metadata: Optional additional metadata
        created_at: When subject was created
        updated_at: When subject was last updated

    Example:
        >>> subject = Subject(
        ...     id="123",
        ...     identifier="user:john.doe",
        ...     subject_type="user",
        ...     subject_id="john.doe",
        ...     display_name="John Doe",
        ...     tenant_id="org:acme",
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
    """

    id: str = Field(..., description="Internal ID")
    identifier: str = Field(..., description="Subject identifier")
    subject_type: str = Field(..., description="Subject type")
    subject_id: str = Field(..., description="Subject ID portion")
    display_name: str | None = Field(default=None, description="Display name")
    tenant_id: str | None = Field(default=None, description="Tenant identifier")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SubjectCreate(BaseModel):
    """Request to create or update a subject.

    Attributes:
        identifier: Subject identifier (format: 'type:id')
        display_name: Optional human-readable name
        tenant_id: Optional tenant identifier
        metadata: Optional additional metadata

    Example:
        >>> create_req = SubjectCreate(
        ...     identifier="user:jane.doe",
        ...     display_name="Jane Doe",
        ...     tenant_id="org:acme",
        ...     metadata={"email": "jane@acme.com"}
        ... )
    """

    identifier: str = Field(..., min_length=3, max_length=255, description="Subject identifier")
    display_name: str | None = Field(default=None, max_length=255, description="Display name")
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class SubjectFilter(BaseModel):
    """Filter criteria for listing subjects.

    All filter fields are optional and will be combined with AND logic.

    Attributes:
        subject_type: Filter by subject type (user, role, group, etc.)
        tenant_id: Filter by tenant identifier
        search: Search in display names
        include_inactive: Include deactivated subjects
        limit: Number of results per page (1-1000)
        offset: Pagination offset

    Example:
        >>> filters = SubjectFilter(
        ...     subject_type="user",
        ...     tenant_id="org:acme",
        ...     search="john",
        ...     limit=50
        ... )
        >>> subjects = client.list_subjects(filters)
    """

    subject_type: str | None = Field(default=None, description="Filter by subject type")
    tenant_id: str | None = Field(default=None, description="Filter by tenant")
    search: str | None = Field(default=None, description="Search in display names")
    include_inactive: bool = Field(default=False, description="Include inactive subjects")
    limit: int = Field(default=100, ge=1, le=1000, description="Results per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
