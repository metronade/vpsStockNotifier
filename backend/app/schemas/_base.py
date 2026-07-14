"""Base model that treats naive datetimes as UTC on serialization.

SQLAlchemy + SQLite stores DateTime columns without timezone information even
when a TZ-aware datetime is written. Pydantic would then serialise the value
back as an ISO string without an offset, and the browser would misinterpret
the timestamp as local time — producing phantom "2 hours ago" gaps for scans
that just ran.

This base reattaches `+00:00` to every naive datetime field before the model
is serialised, so the JSON response always carries the offset. Existing DB
rows written before the timezone fix are covered too — no rescan required.
"""
from datetime import datetime, timezone

from pydantic import BaseModel, model_validator


class VPSBaseModel(BaseModel):
    @model_validator(mode="after")
    def _attach_utc_offset(self) -> "VPSBaseModel":
        for field_name in self.model_fields:
            value = getattr(self, field_name, None)
            if isinstance(value, datetime) and value.tzinfo is None:
                setattr(self, field_name, value.replace(tzinfo=timezone.utc))
        return self
