"""Shared Pydantic base and utility types."""

from pydantic import BaseModel, ConfigDict


class AppBaseModel(BaseModel):
    """Base model with ORM mode enabled for all schemas."""

    model_config = ConfigDict(from_attributes=True)
