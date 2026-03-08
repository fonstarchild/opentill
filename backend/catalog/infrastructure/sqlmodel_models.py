from typing import Optional
from sqlmodel import Field, SQLModel


class ProductTable(SQLModel, table=True):
    """SQLModel persistence model for products."""
    __tablename__ = "product"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sku: str = Field(unique=True, index=True)
    barcode: str = Field(default="", index=True)
    price: float
    cost: float = Field(default=0.0)
    tax_rate: float = Field(default=0.21)
    stock: int = Field(default=0)
    category: str = Field(default="")
    description: str = Field(default="")
    active: bool = Field(default=True)
    currency: str = Field(default="EUR")
