from typing import List, Optional

from apipeline.frames.sys_frames import Frame
from apipeline.processors.frame_processor import FrameDirection, FrameProcessor


class FrameFilter(FrameProcessor):

    def __init__(self,
                 ignored_frame_types: Optional[list] = [],
                 include_frame_types: Optional[list] = None):
        super().__init__()
        self._ignored_frame_types = tuple(
            ignored_frame_types) if ignored_frame_types is not None else None
        self._include_frame_types = tuple(include_frame_types) if include_frame_types else None

    def _should_passthrough_frame(self, frame):
        if self._ignored_frame_types is not None \
                and not isinstance(frame, self._ignored_frame_types):
            if not self._include_frame_types \
                or (self._include_frame_types
                    and isinstance(frame, self._include_frame_types)):
                return False
        return True

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if self._should_passthrough_frame(frame):
            await self.push_frame(frame, direction)
