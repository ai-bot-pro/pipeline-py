import logging
import asyncio
from abc import ABC, abstractmethod

from apipeline.frames.base import Frame
from apipeline.frames.data_frames import DataFrame
from apipeline.frames.sys_frames import CancelFrame, MetricsFrame, StartInterruptionFrame, StopInterruptionFrame, SystemFrame
from apipeline.frames.control_frames import ControlFrame, EndFrame, StartFrame
from apipeline.processors.async_frame_processor import AsyncFrameProcessor
from apipeline.processors.frame_processor import FrameDirection


class OutputProcessor(AsyncFrameProcessor, ABC):
    r"""
    output processor with start, stop control frames and cancel sys frames
    sink data frame and control frames
    """

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

    async def stop(self, frame: EndFrame):
        # Wait for the push frame and sink tasks to finish. They will finish when
        # the EndFrame is actually processed.
        await self._push_frame_task
        await self._sink_task

    async def cancel(self, frame: CancelFrame):
        # Cancel all the tasks and wait for them to finish.
        self._push_frame_task.cancel()
        await self._push_frame_task

        self._sink_task.cancel()
        await self._sink_task

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        #
        # System frames (like StartInterruptionFrame) are pushed immediately.
        # Other frames require order so they are put in the sink queue.
        #
        if isinstance(frame, CancelFrame):
            await self.push_frame(frame, direction)
            await self.cancel(frame)
        elif isinstance(frame, StartInterruptionFrame) or isinstance(frame, StopInterruptionFrame):
            await self.push_frame(frame, direction)
            await self._handle_interruptions(frame)
        elif isinstance(frame, MetricsFrame):
            await self.push_frame(frame, direction)
            await self.send_metrics(frame)
        elif isinstance(frame, SystemFrame):
            await self.push_frame(frame, direction)
        # Control frames.
        elif isinstance(frame, StartFrame):
            await self._sink_queue.put(frame)
            await self.start(frame)
        elif isinstance(frame, EndFrame):
            await self._sink_queue.put(frame)
            await self.stop(frame)
        else:
            await self._sink_queue.put(frame)

    async def send_metrics(self, frame: MetricsFrame):
        pass

    async def _handle_interruptions(self, frame: Frame):
        if not self.interruptions_allowed:
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
        running = True
        while running:
            try:
                frame = await self._sink_queue.get()
                # print(f"_sink_queue.get: {frame}")
                # sink data frame
                if isinstance(frame, DataFrame):
                    await self.sink(frame)
                    # subclass need wait sink task done
                    await self._sink_event.wait()
                    self._sink_event.clear()
                # sink control frame
                elif isinstance(frame, ControlFrame):
                    await self.sink_control_frame(frame)
                else:
                    await self.queue_frame(frame)

                running = not isinstance(frame, EndFrame)

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

    async def sink_control_frame(self, frame: ControlFrame):
        """
        flow stream to control frame start, end, e.g. until await task future is finished
        """
        logging.debug(
            f"{self.__class__.__name__} process_control_frame {frame} doing")
        await self.queue_frame(frame)


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
            self._running = True
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

    async def sink_control_frame(self, frame: ControlFrame):
        self._running = not isinstance(frame, EndFrame)
        return await super().sink_control_frame(frame)

    def _create_output_task(self):
        self._out_task = self.get_event_loop().create_task(self._out_push_task_handler())

    async def _out_push_task_handler(self):
        while self._running:
            try:
                frame = await asyncio.wait_for(self._out_queue.get(), 0.1)
                # print(f"_out_queue.get: {frame}")
                if asyncio.iscoroutinefunction(self._cb):
                    await self._cb(frame)
                else:
                    self._cb(frame)
                self._out_queue.task_done()
                self._sink_event.set()
            except TimeoutError:
                continue
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logging.warning("Output push task was cancelled.")
                break
            except Exception as ex:
                logging.exception(f"Unexpected error in _out_push_task_handler: {ex}")

    async def start(self, frame: StartFrame):
        if self._out_task is None or self._out_task.cancelled():
            self._create_output_task()
        await super().start(frame)

    async def stop(self, frame: EndFrame):
        self._out_task and await self._out_task
        await super().stop(frame)

    async def cancel(self, frame: CancelFrame):
        if self._out_task and self._out_task.cancelled() is False:
            self._out_task.cancel()
            await self._out_task
            self._out_task = None
        await super().cancel(frame)
