import logging
from abc import abstractmethod
import asyncio

from apipeline.frames.base import Frame
from apipeline.frames.sys_frames import CancelFrame, SystemFrame
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
            f"f{self.__class__.__name__} process_sys_frame {frame} direction:{direction} doing")
        await self.queue_frame(frame, direction)

    async def process_control_frame(self, frame: Frame, direction: FrameDirection):
        logging.debug(
            f"f{self.__class__.__name__} process_control_frame {frame} direction:{direction} doing")
        await self.queue_frame(frame, direction)

    async def process_data_frame(self, frame: Frame, direction: FrameDirection):
        logging.debug(
            f"f{self.__class__.__name__} process_data_frame {frame} direction:{direction} doing")
        await self.queue_frame(frame, direction)

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # System frames
        if isinstance(frame, CancelFrame):
            # We don't queue a CancelFrame since we want to stop ASAP.
            await self.push_frame(frame, direction)
            await self.stop()
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


class InputFrameProcessor(InputProcessor):
    """
    consume input asyncio.Queue, push to next processor;
    if input queue is None, use queue_frame method to push frame to next processor with direction

    WARNNING: dont to use it if use pipeline task, just use pipeline task queue_frame to input frame
    """

    def __init__(self, *, in_queue: asyncio.Queue | None = None, name: str | None = None,
                 loop: asyncio.AbstractEventLoop | None = None, **kwargs):
        super().__init__(name=name, loop=loop, **kwargs)
        if in_queue is not None:
            self._in_queue = in_queue
            self._create_input_task()

    def _create_input_task(self):
        self._in_task = self.get_event_loop().create_task(self._in_push_task_handler())

    async def _in_push_task_handler(self):
        running = True
        while running:
            try:
                frame = await self._in_queue.get()
                await self.push_frame(frame)
                running = not isinstance(frame, EndFrame)
            except asyncio.CancelledError:
                break

    async def start(self, frame: Frame):
        if self._in_task is not None and self._in_task.cancelled():
            self._create_input_task()

    async def stop(self):
        if self._in_task is not None and self._in_task and not self._in_task.cancelled():
            self._in_task.cancel()
            await self._in_task

    async def cleanup(self):
        await self.stop()
        super().cleanup()
