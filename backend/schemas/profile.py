import uuid

from pydantic import BaseModel, ConfigDict, Field


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    headline: str | None
    bio: str | None
    target_roles: list[str]


class ProfileUpdate(BaseModel):
    headline: str | None = Field(default=None, max_length=160)
    bio: str | None = Field(default=None, max_length=1000)
    target_roles: list[str] | None = Field(default=None, max_length=10)
