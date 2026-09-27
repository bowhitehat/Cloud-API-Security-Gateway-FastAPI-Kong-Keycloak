from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    role: str = "user"


class UserRead(BaseModel):
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)
