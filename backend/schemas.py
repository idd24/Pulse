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


class DailyCheckinUpsert(BaseModel):
    mood: int = Field(ge=0, le=4)
    energy: int = Field(ge=0, le=4)
    activities: list[Activity] = Field(default_factory=list, max_length=8)


class DailyCheckinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date: date_t
    mood: int
    energy: int
    activities: list[str]
    updated_at: datetime


# --- Screen-time breakdown -------------------------------------------------


class ScreentimeUpsert(BaseModel):
    social: int = Field(default=0, ge=0, le=24 * 60)
    entertainment: int = Field(default=0, ge=0, le=24 * 60)
    productivity: int = Field(default=0, ge=0, le=24 * 60)


class ScreentimeResponse(BaseModel):
    id: UUID
    date: date_t
    social: int
    entertainment: int
    productivity: int
    updated_at: datetime


# --- Dashboard summary -----------------------------------------------------


class DashboardWeekMetrics(BaseModel):
    start_date: date_t
    end_date: date_t
    # Null when the week had zero check-ins — distinguishes "no data" from 0.
    avg_mood: Optional[float]
    avg_energy: Optional[float]
    checkin_count: int
    total_screen_time_minutes: int


class DashboardSummaryResponse(BaseModel):
    current: DashboardWeekMetrics
    previous: DashboardWeekMetrics


# --- Dashboard trends ------------------------------------------------------


TrendsRange = Literal["7d", "30d", "90d"]


class TrendsResponse(BaseModel):
    range: TrendsRange
    start_date: date_t
    end_date: date_t
    dates: list[date_t]
    # null marks days without a check-in / breakdown — distinguishes "no data" from 0.
    mood: list[Optional[int]]
    energy: list[Optional[int]]
    screen_time_minutes: list[Optional[int]]
