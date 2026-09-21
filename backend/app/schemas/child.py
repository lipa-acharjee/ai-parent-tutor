from pydantic import BaseModel, Field
class ChildCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    grade: str = Field(min_length=1, max_length=40)
    language: str = Field(default="English", max_length=40)
class ChildResponse(ChildCreate):
    id: str
    model_config = {"from_attributes": True}
