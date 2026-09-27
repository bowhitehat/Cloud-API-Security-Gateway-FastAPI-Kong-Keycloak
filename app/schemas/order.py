from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    item_name: str = Field(min_length=2, max_length=120)
    amount: float = Field(gt=0)
    status: str = "pending"


class OrderRead(BaseModel):
    id: int
    item_name: str
    amount: float
    status: str
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
