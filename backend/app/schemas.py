from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Note schemas
class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    tags: Optional[str] = None
    game_date: Optional[str] = None
    is_important: bool = False


class NoteCreate(NoteBase):
    player_id: int


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[str] = None
    game_date: Optional[str] = None
    is_important: Optional[bool] = None


class NoteResponse(NoteBase):
    id: int
    player_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Player schemas
class PlayerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    position: Optional[str] = Field(None, max_length=50)
    team: Optional[str] = Field(None, max_length=100)
    jersey_number: Optional[int] = None
    height: Optional[str] = Field(None, max_length=20)
    weight: Optional[str] = Field(None, max_length=20)
    age: Optional[int] = None


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[str] = Field(None, max_length=50)
    team: Optional[str] = Field(None, max_length=100)
    jersey_number: Optional[int] = None
    height: Optional[str] = Field(None, max_length=20)
    weight: Optional[str] = Field(None, max_length=20)
    age: Optional[int] = None


class PlayerResponse(PlayerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlayerDetailResponse(PlayerResponse):
    notes: List[NoteResponse] = []

    class Config:
        from_attributes = True
