from datetime import date as date_t, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Daily check-in --------------------------------------------------------

# Keep these in sync with lib/checkinOptions.ts on the client.
Activity = Literal[
    "exercise",
    "work",
    "social",
    "outdoors",
    "reading",
    "gaming",
    "meditation",
    "chores",
]
Category = Literal[
    "social",
    "entertainment",
    "productivity",
    "games",
    "communication",
    "other",
]


class DailyCheckinUpsert(BaseModel):
    mood: int = Field(ge=0, le=4)
    energy: int = Field(ge=0, le=4)
    screen_time_minutes: int = Field(ge=0, le=24 * 60)
    top_category: Optional[Category] = None
    activities: list[Activity] = Field(default_factory=list, max_length=8)


class DailyCheckinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date: date_t
    mood: int
    energy: int
    screen_time_minutes: int
    top_category: Optional[str]
    activities: list[str]
    updated_at: datetime


# --- Screen-time breakdown -------------------------------------------------

# Field names match the Category literal above; values are minutes per day.
class ScreentimeUpsert(BaseModel):
    social: int = Field(default=0, ge=0, le=24 * 60)
    entertainment: int = Field(default=0, ge=0, le=24 * 60)
    productivity: int = Field(default=0, ge=0, le=24 * 60)
    games: int = Field(default=0, ge=0, le=24 * 60)
    communication: int = Field(default=0, ge=0, le=24 * 60)
    other: int = Field(default=0, ge=0, le=24 * 60)


class ScreentimeResponse(BaseModel):
    id: UUID
    date: date_t
    social: int
    entertainment: int
    productivity: int
    games: int
    communication: int
    other: int
    updated_at: datetime
