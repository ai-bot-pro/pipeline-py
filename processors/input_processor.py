
from abc import ABC, abstractmethod

from frames.base import Frame
from frames.sys_frames import CancelFrame, StartFrame
from frames.control_frames import EndPipeFrame
from processors.async_frame_processor import AsyncFrameProcessor
from processors.frame_processor import FrameDirection


class InputProcessor(AsyncFrameProcessor, ABC):

    @abstractmethod
    async def start(self, frame: StartFrame):
        raise NotImplementedError

    @abstractmethod
    async def stop(self):
        raise NotImplementedError

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, CancelFrame):
            await self.stop()
            # We don't queue a CancelFrame since we want to stop ASAP.
            await self.push_frame(frame, direction)
        elif isinstance(frame, StartFrame):
            await self.start(frame)
            await self.queue_frame(frame, direction)
        elif isinstance(frame, EndPipeFrame):
            await self.queue_frame(frame, direction)
            await self.stop()
        else:
            await self.queue_frame(frame, direction)
