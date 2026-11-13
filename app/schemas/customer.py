from pydantic import BaseModel, Field, ConfigDict


class CustomerCreate(BaseModel):

    name: str = Field(min_length=2, max_length=100)

    phone: str = Field(min_length=10, max_length=20)

    address: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, min_length=10, max_length=20)
    address: str | None = None


class CustomerResponse(BaseModel):

    id: int

    name: str

    phone: str

    address: str | None = None

    model_config = ConfigDict(from_attributes=True)