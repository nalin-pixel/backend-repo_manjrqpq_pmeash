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

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Existing example schemas (kept for reference/testing):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")


# SaaS: Products and License Keys

class ProductSaaS(BaseModel):
    """
    Products for the licensing SaaS
    Collection name: "productsaas"
    """
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    plan: Optional[str] = Field("standard", description="Plan/tier for the product")
    price: Optional[float] = Field(0, ge=0, description="Price in USD")
    status: str = Field("active", description="active | archived")


class License(BaseModel):
    """
    License keys issued for products
    Collection name: "license"
    """
    product_id: str = Field(..., description="ID of the related product")
    key: str = Field(..., description="License key string")
    assigned_to: Optional[str] = Field(None, description="Customer email the key is assigned to")
    status: str = Field("unused", description="unused | active | suspended | expired")
    max_activations: int = Field(1, ge=1, le=100, description="Maximum allowed activations")
    activations: List[str] = Field(default_factory=list, description="List of machine IDs that activated this key")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration timestamp (UTC)")


# Legacy example product (not used by the app UI, kept for compatibility):
class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Add your own schemas above.
# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
