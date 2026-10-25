from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for response schemas that are built from SQLAlchemy objects."""

    model_config = ConfigDict(from_attributes=True)
