import logging
import asyncio
from typing import Coroutine, Optional

from apipeline.frames.sys_frames import ErrorFrame, Frame, StartInterruptionFrame, InterruptionFrame
from apipeline.frames.control_frames import EndFrame
from apipeline.processors.frame_processor import FrameDirection, FrameProcessor
from apipeline.utils.asyncio.task_manager import BaseTaskManager


class AsyncFrameProcessor(FrameProcessor):
    def __init__(
        self,
        *,
        name: str | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
        use_upstream_task: bool = True,
        **kwargs,
    ):
        super().__init__(name=name, loop=loop, **kwargs)

        self._push_frame_task = None
        self._push_up_frame_task = None
        self._is_use_upstream_task = use_upstream_task

    async def setup(self, task_manager: BaseTaskManager):
        await super().setup(task_manager)
        self._create_push_task()
        if self._is_use_upstream_task:
            self._create_upstream_push_task()

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, (StartInterruptionFrame, InterruptionFrame)):
            await self._handle_interruptions(frame)

    async def cleanup(self):
        if self._push_frame_task:
            await self._task_manager.cancel_task(self._push_frame_task, timeout=1.0)
            self._push_frame_task = None
        if self._push_up_frame_task:
            await self._task_manager.cancel_task(self._push_up_frame_task, timeout=1.0)
            self._push_up_frame_task = None
        logging.info(f"{self.name} AsyncFrameProcessor cleanup done")

    #
    # Handle interruptions
    #
    async def _handle_interruptions(self, frame: Frame):
        """
        NOTE: push interruptions frame, don't push again
        """
        try:
            await self.cleanup()
            # Push an out-of-band frame (i.e. not using the ordered push
            # frame task).
            await self.push_frame(frame)

            # Create a new queue and task.
            self._create_push_task()
            if self._is_use_upstream_task:
                self._create_upstream_push_task()
        except Exception as e:
            logging.exception(f"Uncaught exception in {self} when handle_interruptions: {e}")
            await self.push_error(ErrorFrame(str(e)))

    #
    # Push frames task
    #

    def create_task(self, coroutine: Coroutine, name: Optional[str] = None) -> asyncio.Task:
        if name:
            name = f"{self}::{name}"
        else:
            name = f"{self}::{coroutine.cr_code.co_name}"
        return self._task_manager.create_task(coroutine, name)

    def _create_push_task(self):
        self._push_queue = asyncio.Queue()
        self._push_frame_task = self.create_task(self._push_frame_task_handler())
        logging.info(f"{self.name} create push_frame_task")

    def _create_upstream_push_task(self):
        self._push_up_queue = asyncio.Queue()
        self._push_up_frame_task = self.create_task(self._push_up_frame_task_handler())
        logging.info(f"{self.name} create push_up_frame_task")

    async def queue_frame(
        self, frame: Frame, direction: FrameDirection = FrameDirection.DOWNSTREAM
    ):
        if self._is_use_upstream_task and direction == FrameDirection.UPSTREAM:
            await self._push_up_queue.put((frame, direction))
        else:
            await self._push_queue.put((frame, direction))

    async def _push_frame_task_handler(self):
        running = True
        while running:
            frame, direction = await self._push_queue.get()
            await self.push_frame(frame, direction)
            running = not isinstance(frame, EndFrame)
            self._push_queue.task_done()

    async def _push_up_frame_task_handler(self):
        running = True
        while running:
            frame, direction = await self._push_up_queue.get()
            await self.push_frame(frame, direction)
            running = not isinstance(frame, EndFrame)
            self._push_up_queue.task_done()
