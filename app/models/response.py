from typing import Generic, TypeVar, Optional, Any, Dict, List
from pydantic import BaseModel

# Generic type for response data
T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """Standard API response model with success, data, and message fields"""
    success: bool
    data: Optional[T] = None
    message: str

class StandardListResponse(BaseModel, Generic[T]):
    """Standard API response model for list endpoints"""
    success: bool
    data: Dict[str, List[T]]
    message: str

class StandardPaginatedResponse(BaseModel, Generic[T]):
    """Standard API response model for paginated endpoints"""
    success: bool
    data: Dict[str, Any]  # Contains items, total, page, page_size, etc.
    message: str

def success_response(data: T = None, message: str = "Operation completed successfully") -> StandardResponse[T]:
    """Create a successful response"""
    return StandardResponse(success=True, data=data, message=message)

def success_list_response(items: List[T], message: str = None) -> StandardListResponse[T]:
    """Create a successful list response"""
    if message is None:
        message = f"Retrieved {len(items)} items"
    return StandardListResponse(success=True, data={"items": items}, message=message)

def success_paginated_response(
    items: List[T], 
    total: int, 
    page: int, 
    page_size: int, 
    total_pages: int, 
    has_next: bool, 
    has_previous: bool,
    message: str = None
) -> StandardPaginatedResponse[T]:
    """Create a successful paginated response"""
    if message is None:
        message = f"Retrieved {len(items)} items (page {page} of {total_pages})"
    
    return StandardPaginatedResponse(
        success=True,
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous
        },
        message=message
    )

def error_response(message: str, data: T = None) -> StandardResponse[T]:
    """Create an error response"""
    return StandardResponse(success=False, data=data, message=message)
