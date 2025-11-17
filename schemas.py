"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime as DateTime

# --- Trattoria-specific Schemas ---

class Dish(BaseModel):
    """
    Restaurant dishes
    Collection: "dish"
    """
    name: str = Field(..., description="Dish name")
    description: Optional[str] = Field(None, description="Short description")
    price: float = Field(..., ge=0, description="Price in local currency")
    category: str = Field(..., description="Category: pizza, starter, pasta, main, dessert, drinks")
    image: Optional[str] = Field(None, description="Image URL")
    tags: Optional[List[str]] = Field(default_factory=list, description="Search tags")

class Reservation(BaseModel):
    """
    Table reservations
    Collection: "reservation"
    """
    name: str = Field(..., description="Guest full name")
    phone: str = Field(..., description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    reservation_time: DateTime = Field(..., description="Reservation date and time (ISO 8601)")
    guests: int = Field(..., ge=1, le=20, description="Number of guests")
    requests: Optional[str] = Field(None, description="Special requests")
    source: Optional[str] = Field("website", description="Reservation source")

# Example schemas retained (not used by app but kept for reference)
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
