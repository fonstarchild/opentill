from typing import Optional
from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    """A product or item for sale."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sku: str = Field(unique=True, index=True)
    barcode: str = Field(default="", index=True)
    price: float
    cost: float = Field(default=0.0)
    tax_rate: float = Field(default=0.21, description="VAT rate e.g. 0.21 = 21%")
    stock: int = Field(default=0)
    category: str = Field(default="")
    description: str = Field(default="")
    active: bool = Field(default=True)


class ProductCreate(SQLModel):
    name: str
    sku: str
    barcode: str = ""
    price: float
    cost: float = 0.0
    tax_rate: float = 0.21
    stock: int = 0
    category: str = ""
    description: str = ""


class ProductUpdate(SQLModel):
    name: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    tax_rate: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class StockAdjustment(SQLModel):
    delta: int  # positive = restock, negative = remove
    reason: str = ""
