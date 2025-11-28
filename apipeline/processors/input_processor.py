import logging
from abc import abstractmethod

from apipeline.frames.base import Frame
from apipeline.frames.sys_frames import (
    CancelFrame,
    SystemFrame,
    StartInterruptionFrame,
    InterruptionFrame,
)
from apipeline.frames.control_frames import EndFrame, StartFrame, ControlFrame
from apipeline.frames.data_frames import DataFrame
from apipeline.processors.async_frame_processor import AsyncFrameProcessor
from apipeline.processors.frame_processor import FrameDirection


class InputProcessor(AsyncFrameProcessor):
    """
    base inpurt processor
    """

    @abstractmethod
    async def start(self, frame: StartFrame):
        pass

    @abstractmethod
    async def stop(self):
        pass

    async def process_sys_frame(self, frame: Frame, direction: FrameDirection):
        logging.debug(
            f"f{self.__class__.__name__} process_sys_frame {frame} direction:{direction} doing"
        )
        await self.queue_frame(frame, direction)

    async def process_control_frame(self, frame: Frame, direction: FrameDirection):
        logging.debug(
            f"f{self.__class__.__name__} process_control_frame {frame} direction:{direction} doing"
        )
        await self.queue_frame(frame, direction)

    async def process_data_frame(self, frame: Frame, direction: FrameDirection):
        logging.debug(
            f"f{self.__class__.__name__} process_data_frame {frame} direction:{direction} doing"
        )
        await self.queue_frame(frame, direction)

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # System frames
        if isinstance(frame, CancelFrame):
            # We don't queue a CancelFrame since we want to stop ASAP.
            await self.push_frame(frame, direction)
            await self.stop()
        elif isinstance(frame, (StartInterruptionFrame, InterruptionFrame)):
            pass
        # all other system frames
        elif isinstance(frame, SystemFrame):
            await self.process_sys_frame(frame, direction)
        # Control frames
        elif isinstance(frame, StartFrame):
            await self.queue_frame(frame, direction)
            await self.start(frame)
        elif isinstance(frame, EndFrame):
            await self.queue_frame(frame, direction)
            await self.stop()
        # all other control frames
        elif isinstance(frame, ControlFrame):
            await self.process_control_frame(frame, direction)
        # Data frames
        elif isinstance(frame, DataFrame):
            await self.process_data_frame(frame, direction)
        # Other frames
        else:
            await self.queue_frame(frame, direction)
