"""
scada/tag_database.py
In-memory process tag database (process historian backbone).
Each tag holds the current value + timestamp + quality code.
"""

import time
import logging
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TagQuality(IntEnum):
    GOOD    = 192   # OPC-UA / DA standard codes
    BAD     = 0
    UNCERTAIN = 64


@dataclass
class Tag:
    tag_id: str
    description: str
    unit: str
    value: Any = None
    quality: TagQuality = TagQuality.GOOD
    timestamp: float = field(default_factory=time.time)
    lo_lo: Optional[float] = None
    lo:    Optional[float] = None
    hi:    Optional[float] = None
    hi_hi: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update(self, value: Any, quality: TagQuality = TagQuality.GOOD):
        self.value = value
        self.quality = quality
        self.timestamp = time.time()

    @property
    def alarm_state(self) -> str:
        if self.value is None or not isinstance(self.value, (int, float)):
            return "UNKNOWN"
        v = float(self.value)
        if self.hi_hi is not None and v >= self.hi_hi:
            return "HI_HI"
        if self.lo_lo is not None and v <= self.lo_lo:
            return "LO_LO"
        if self.hi is not None and v >= self.hi:
            return "HI"
        if self.lo is not None and v <= self.lo:
            return "LO"
        return "NORMAL"


class TagDatabase:
    """Central process variable store."""

    def __init__(self):
        self._tags: Dict[str, Tag] = {}

    def register(self, tag: Tag) -> Tag:
        self._tags[tag.tag_id] = tag
        return tag

    def write(self, tag_id: str, value: Any, quality: TagQuality = TagQuality.GOOD):
        if tag_id in self._tags:
            self._tags[tag_id].update(value, quality)
        else:
            self.register(Tag(tag_id=tag_id, description=f"Auto-registered tag {tag_id}", unit=""))
            self._tags[tag_id].update(value, quality)

    def read(self, tag_id: str) -> Optional[Tag]:
        return self._tags.get(tag_id)

    def read_value(self, tag_id: str, default=None) -> Any:
        tag = self._tags.get(tag_id)
        return tag.value if tag else default

    def all_tags(self) -> Dict[str, Tag]:
        return dict(self._tags)

    def alarming_tags(self) -> Dict[str, Tag]:
        return {tid: t for tid, t in self._tags.items() if t.alarm_state != "NORMAL"}

    def snapshot(self) -> dict:
        """Return a JSON-serialisable snapshot of all tag values."""
        return {
            tid: {
                "value": t.value,
                "unit": t.unit,
                "quality": t.quality.name,
                "alarm": t.alarm_state,
                "ts": t.timestamp,
            }
            for tid, t in self._tags.items()
        }
