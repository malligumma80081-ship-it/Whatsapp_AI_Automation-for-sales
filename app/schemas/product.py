from decimal import Decimal

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
)


class ProductCreate(BaseModel):

    product_id: str = Field(
        min_length=3,
        max_length=30,
    )

    product_name: str = Field(
        min_length=2,
        max_length=100,
    )

    millet_name: str = Field(
        min_length=2,
        max_length=50,
    )

    size: str = Field(
        min_length=2,
        max_length=30,
    )

    price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    initial_stock: int = Field(
        default=0,
        ge=0,
    )


class ProductUpdate(BaseModel):

    product_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    millet_name: str | None = None

    size: str | None = None

    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    available: bool | None = None


class ProductResponse(BaseModel):

    product_id: str

    product_name: str

    millet_name: str

    size: str

    price: Decimal

    currency: str

    available: bool

    model_config = ConfigDict(
        from_attributes=True
    )