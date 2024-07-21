
from abc import ABC, abstractmethod
import asyncio

from frames.base import Frame
from frames.sys_frames import CancelFrame, StartFrame
from frames.control_frames import EndPipeFrame
from processors.async_frame_processor import AsyncFrameProcessor
from processors.frame_processor import FrameDirection


class InputProcessor(AsyncFrameProcessor, ABC):
    """
    base inpurt processor
    """

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


class InputFrameProcessor(InputProcessor):
    """
    consume input asyncio.Queue, push to next processor;
    if input queue is None, use queue_frame method to push frame to next processor with direction
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
                print(frame)
                await self.push_frame(frame)
                running = not isinstance(frame, EndPipeFrame)
            except asyncio.CancelledError:
                break

    async def start(self, frame: Frame):
        if self._in_task is not None and self._in_task.cancelled:
            self._create_input_task()

    async def stop(self):
        if self._in_task is not None and self._in_task and not self._in_task.cancelled:
            self._in_task.cancel()
            await self._in_task

    async def cleanup(self):
        await self.stop()
        super().cleanup()
