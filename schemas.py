"""
Database Schemas for Ayurvedic Cosmetics E-commerce

Each Pydantic model represents a collection in your database.
Collection name is lowercase of the class name.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Detailed description")
    price: float = Field(..., ge=0, description="Price in currency units")
    category: str = Field(..., description="Category e.g. Face Care, Hair Care, Body Care")
    ingredients: List[str] = Field(default_factory=list, description="Key Ayurvedic ingredients")
    image_url: Optional[str] = Field(None, description="Primary image URL")
    gallery: List[str] = Field(default_factory=list, description="Additional image URLs")
    in_stock: bool = Field(True, description="Stock availability")
    stock_count: int = Field(10, ge=0, description="Units available")
    rating: float = Field(4.5, ge=0, le=5, description="Average rating")
    reviews_count: int = Field(0, ge=0, description="Number of reviews")
    popularity: int = Field(0, ge=0, description="Popularity score for sorting")
    tags: List[str] = Field(default_factory=list, description="Search tags")

class User(BaseModel):
    name: str
    email: str
    password_hash: str
    role: str = Field("customer", description="customer or admin")
    is_active: bool = True

class OrderItem(BaseModel):
    product_id: str
    title: str
    price: float
    quantity: int
    image_url: Optional[str] = None

class Order(BaseModel):
    user_id: Optional[str] = None
    items: List[OrderItem]
    total_amount: float
    status: str = Field("pending")
    shipping_address: Optional[dict] = None
