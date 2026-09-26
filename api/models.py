from datetime import datetime

from pydantic import BaseModel


class Reading(BaseModel):
    pod_id: str
    timestamp: datetime
    co2_ppm: float
    temperature_c: float
    rh_pct: float
    water_ph: float
    light_ppfd: float


class ReadingsResponse(BaseModel):
    items: list[Reading]
    count: int
    truncated: bool
