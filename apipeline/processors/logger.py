from typing import Optional
import logging

from apipeline.frames.base import Frame
from apipeline.processors.frame_processor import FrameDirection, FrameProcessor


class FrameLogger(FrameProcessor):
    def __init__(
            self,
            prefix="Frame",
            color: Optional[str] = None,
            ignored_frame_types: Optional[list] = [],
            include_frame_types: Optional[list] = None):
        super().__init__()
        self._prefix = prefix
        self._color = color
        self._ignored_frame_types = tuple(
            ignored_frame_types) if ignored_frame_types is not None else None
        self._include_frame_types = tuple(include_frame_types) if include_frame_types else None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if self._ignored_frame_types is not None and not isinstance(
                frame, self._ignored_frame_types):
            if not self._include_frame_types \
                or (self._include_frame_types
                    and isinstance(frame, self._include_frame_types)):
                from_to = f"{self._prev} ---> {self}"
                if direction == FrameDirection.UPSTREAM:
                    from_to = f"{self} <--- {self._next} "
                msg = f"{from_to} {self._prefix}: {frame}"
                if self._color:
                    msg = f"<{self._color}>{msg}</>"
                logging.info(msg)

        await self.push_frame(frame, direction)
