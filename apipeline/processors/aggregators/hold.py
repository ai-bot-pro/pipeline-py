import asyncio
from typing import Type

from apipeline.frames import CancelFrame, EndFrame, Frame, StartFrame
from apipeline.processors.async_frame_processor import AsyncFrameProcessor
from apipeline.processors.frame_processor import FrameDirection, FrameProcessor
from apipeline.notifiers.base import BaseNotifier


class HoldFramesAggregator(AsyncFrameProcessor):
    """
    This aggregator keeps the specified frames,
    it doesn't let the frames through until the notifier is notified.
    """

    def __init__(self,
                 notifier: BaseNotifier,
                 hold_frame_classes: tuple[Type[Frame]],
                 **kwargs):
        super().__init__(**kwargs)
        self._notifier = notifier
        self._hold_frame_classes = hold_frame_classes
        self._hold_frames = []

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
            await self.push_frame(frame)
            await self._start()
        if isinstance(frame, (EndFrame, CancelFrame)):
            await self.push_frame(frame, direction)
            await self._stop()
        elif isinstance(frame, self._hold_frame_classes):
            self._hold_frames.append(frame)
        else:
            await self.push_frame(frame, direction)

    async def _start(self):
        self._gate_task = self.get_event_loop().create_task(self._gate_task_handler())

    async def _stop(self):
        self._gate_task.cancel()
        await self._gate_task

    async def _gate_task_handler(self):
        while True:
            try:
                await self._notifier.wait()
                for frame in self._hold_frames:
                    await self.queue_frame(frame)
                self._hold_frames = []
            except asyncio.CancelledError:
                break


class HoldLastFrameAggregator(AsyncFrameProcessor):
    """
    This aggregator keeps the specified last frame,
    it doesn't let the frame through until the notifier is notified.
    """

    def __init__(self,
                 notifier: BaseNotifier,
                 hold_frame_classes: tuple[Type[Frame]],
                 **kwargs):
        super().__init__(**kwargs)
        self._notifier = notifier
        self._hold_frame_classes = hold_frame_classes
        self._hold_last_frame = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
            await self.push_frame(frame)
            await self._start()
        if isinstance(frame, (EndFrame, CancelFrame)):
            await self._stop()
            await self.push_frame(frame, direction)
        elif isinstance(frame, self._hold_frame_classes):
            self._hold_last_frame = frame
        else:
            await self.push_frame(frame, direction)

    async def _start(self):
        self._gate_task = self.get_event_loop().create_task(self._gate_task_handler())

    async def _stop(self):
        self._gate_task.cancel()
        await self._gate_task

    async def _gate_task_handler(self):
        while True:
            try:
                await self._notifier.wait()
                if self._hold_last_frame:
                    await self.queue_frame(self._hold_last_frame)
                self._hold_last_frame = None
            except asyncio.CancelledError:
                break
