"""Common data models shared across the SDK.

This module contains base models and utilities used throughout the SDK.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# Type variable for generic paginated response
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    This model wraps paginated API responses and provides convenience methods
    for working with pagination.

    Attributes:
        total: Total number of items across all pages
        limit: Maximum number of items per page
        offset: Offset of the current page
        items: List of items in the current page

    Example:
        >>> response = PaginatedResponse[Permission](
        ...     total=150,
        ...     limit=50,
        ...     offset=0,
        ...     items=[...]
        ... )
        >>> if response.has_more:
        ...     next_page = response.next_offset
    """

    total: int = Field(..., description="Total number of items", ge=0)
    limit: int = Field(..., description="Items per page", ge=1)
    offset: int = Field(..., description="Current page offset", ge=0)
    items: list[T] = Field(..., description="Items in current page")

    @property
    def has_more(self) -> bool:
        """Check if there are more pages available.

        Returns:
            True if more pages exist, False otherwise

        Example:
            >>> while response.has_more:
            ...     # Fetch next page
            ...     response = client.list_permissions(offset=response.next_offset)
        """
        return self.offset + len(self.items) < self.total

    @property
    def next_offset(self) -> int | None:
        """Get the offset for the next page.

        Returns:
            Offset for next page, or None if no more pages

        Example:
            >>> if response.has_more:
            ...     next_offset = response.next_offset
        """
        return self.offset + self.limit if self.has_more else None

    @property
    def current_page(self) -> int:
        """Get the current page number (1-indexed).

        Returns:
            Current page number

        Example:
            >>> print(f"Page {response.current_page} of {response.total_pages}")
        """
        return (self.offset // self.limit) + 1

    @property
    def total_pages(self) -> int:
        """Get the total number of pages.

        Returns:
            Total number of pages

        Example:
            >>> print(f"Showing {response.current_page} of {response.total_pages}")
        """
        return (self.total + self.limit - 1) // self.limit

    model_config = {"arbitrary_types_allowed": True}


class ErrorResponse(BaseModel):
    """Standard error response from the API.

    Attributes:
        detail: Error message
        error_type: Type of error (e.g., "ValidationError")
        field: Optional field that caused the error

    Example:
        >>> error = ErrorResponse(
        ...     detail="Invalid subject identifier",
        ...     error_type="ValidationError",
        ...     field="subject"
        ... )
    """

    detail: str = Field(..., description="Error message")
    error_type: str | None = Field(default=None, description="Error type")
    field: str | None = Field(default=None, description="Field that caused error")


class Metadata(BaseModel):
    """Flexible metadata container.

    Used for storing arbitrary key-value pairs in permission assignments,
    subjects, and scopes.

    Example:
        >>> metadata = Metadata(
        ...     granted_by="admin:123",
        ...     reason="Project access",
        ...     custom_field="custom_value"
        ... )
    """

    model_config = {"extra": "allow"}

    def __init__(self, **data: Any) -> None:
        """Initialize metadata with arbitrary key-value pairs.

        Args:
            **data: Arbitrary metadata fields
        """
        super().__init__(**data)

    def dict(self, **kwargs: Any) -> dict[str, Any]:
        """Convert to dictionary.

        Args:
            **kwargs: Arguments passed to pydantic's dict method

        Returns:
            Dictionary representation
        """
        return super().model_dump(**kwargs)
