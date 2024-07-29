import logging
import asyncio
from abc import ABC, abstractmethod

from apipeline.frames.base import Frame
from apipeline.frames.data_frames import DataFrame
from apipeline.frames.sys_frames import CancelFrame, MetricsFrame, StartInterruptionFrame, StopInterruptionFrame, SystemFrame
from apipeline.frames.control_frames import EndFrame, StartFrame
from apipeline.processors.async_frame_processor import AsyncFrameProcessor
from apipeline.processors.frame_processor import FrameDirection


class OutputProcessor(AsyncFrameProcessor, ABC):

    def __init__(
            self,
            *,
            name: str | None = None,
            loop: asyncio.AbstractEventLoop | None = None,
            **kwargs):
        super().__init__(name=name, loop=loop, **kwargs)

        self._stopped_event = asyncio.Event()
        self._sink_event = asyncio.Event()

        # Create sink frame task. This is the task that will actually write
        # audio or video frames. We write audio/video in a task so we can keep
        # generating frames upstream while, for example, the audio is playing.
        self._create_sink_task()

    async def start(self, frame: StartFrame):
        if self._sink_task.cancelled():
            self._create_sink_task()

    async def stop(self):
        self._stopped_event.set()

    async def cleanup(self):
        self._sink_task.cancel()
        await self._sink_task
        await super().cleanup()

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        #
        # Out-of-band frames like (CancelFrame or StartInterruptionFrame) are
        # pushed immediately. Other frames require order so they are put in the
        # sink queue.
        #
        if isinstance(frame, StartFrame):
            await self.start(frame)
            await self.push_frame(frame, direction)
        # EndFrame is managed in the sink queue handler.
        elif isinstance(frame, CancelFrame):
            await self.stop()
            await self.push_frame(frame, direction)
        elif isinstance(frame, StartInterruptionFrame) or isinstance(frame, StopInterruptionFrame):
            await self._handle_interruptions(frame)
            await self.push_frame(frame, direction)
        elif isinstance(frame, MetricsFrame):
            await self.send_metrics(frame)
            await self.push_frame(frame, direction)
        elif isinstance(frame, SystemFrame):
            await self.push_frame(frame, direction)
        else:
            await self._sink_queue.put(frame)

        # If we are finishing, wait here until we have stopped, otherwise we might
        # close things too early upstream. We need this event because we don't
        # know when the internal threads will finish.
        if isinstance(frame, CancelFrame) or isinstance(frame, EndFrame):
            await self._stopped_event.wait()

    async def send_metrics(self, frame: MetricsFrame):
        pass

    async def _handle_interruptions(self, frame: Frame):
        if not self.interruptions_allowed():
            return

        if isinstance(frame, StartInterruptionFrame):
            # Stop sink task.
            self._sink_task.cancel()
            await self._sink_task
            self._create_sink_task()
            # Stop push task.
            self._push_frame_task.cancel()
            await self._push_frame_task
            self._create_push_task()

    #
    # sink frames task
    #

    def _create_sink_task(self):
        loop = self.get_event_loop()
        self._sink_queue = asyncio.Queue()
        self._sink_task = loop.create_task(self._sink_task_handler())

    async def _sink_task_handler(self):
        while True:
            try:
                frame = await self._sink_queue.get()
                # print(f"_sink_queue.get: {frame}")
                if isinstance(frame, DataFrame):
                    await self.sink(frame)
                    # if sink is async put to queue, need wait sink task done
                    await self._sink_event.wait()
                    self._sink_event.clear()
                else:
                    await self.queue_frame(frame)

                if isinstance(frame, EndFrame):
                    await self.stop()

                self._sink_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as ex:
                logging.exception(f"{self} error processing sink queue: {ex}")

    @abstractmethod
    async def sink(self, frame: DataFrame):
        """
        Multimoding(text,audio,image) Sink, use _sink_event to set
        """
        raise NotImplementedError


class OutputFrameProcessor(OutputProcessor):
    """
    sink data frames to asyncio.Queue
    if have callback, use out push task handler to consume the queue ;
    else user can get the out_queue to consume;
    """

    def __init__(self, *, cb=None, name: str | None = None,
                 loop: asyncio.AbstractEventLoop | None = None, **kwargs):
        super().__init__(name=name, loop=loop, **kwargs)
        self._out_queue = asyncio.Queue()
        self._cb = cb
        self._out_task = None
        if self._cb:
            self._create_output_task()

    @property
    def out_queue(self):
        if self._cb:
            return None
        return self._out_queue

    def set_sink_event(self):
        if self._cb:
            return
        self._sink_event.set()

    async def sink(self, frame: DataFrame):
        await self._out_queue.put(frame)

    def _create_output_task(self):
        self._out_task = self.get_event_loop().create_task(self._out_push_task_handler())

    async def _out_push_task_handler(self):
        running = True
        while running:
            try:
                frame = await self._out_queue.get()
                # print(f"_out_queue.get: {frame}")
                if asyncio.iscoroutinefunction(self._cb):
                    await self._cb(frame)
                else:
                    self._cb(frame)
                self._sink_event.set()
            except asyncio.CancelledError:
                break

    async def start(self, frame: Frame):
        if self._out_task is None or self._out_task.cancelled():
            self._create_output_task()

    async def stop(self):
        if self._out_task and self._out_task.cancelled() is False:
            self._out_task.cancel()
            await self._out_task
            self._out_task = None
        await super().stop()

    async def cleanup(self):
        await self.stop()
        await super().cleanup()
