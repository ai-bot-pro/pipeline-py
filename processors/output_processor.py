import logging
import asyncio
from abc import ABC, abstractmethod

from frames.base import Frame
from frames.data_frames import AudioRawFrame, DataFrame, ImageRawFrame
from frames.sys_frames import CancelFrame, MetricsFrame, StartFrame, StartInterruptionFrame, StopInterruptionFrame, SystemFrame
from frames.control_frames import EndPipeFrame
from processors.async_frame_processor import AsyncFrameProcessor
from processors.frame_processor import FrameDirection


class OutputProcessor(AsyncFrameProcessor, ABC):

    @abstractmethod
    async def start(self, frame: StartFrame):
        raise NotImplementedError

    @abstractmethod
    async def stop(self):
        raise NotImplementedError

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
        elif isinstance(frame, AudioRawFrame):
            await self._handle_audio(frame)
        else:
            await self._sink_queue.put(frame)

        # If we are finishing, wait here until we have stopped, otherwise we might
        # close things too early upstream. We need this event because we don't
        # know when the internal threads will finish.
        if isinstance(frame, CancelFrame) or isinstance(frame, EndPipeFrame):
            await self._stopped_event.wait()

    #
    # sink frames task
    #
    def _create_sink_task(self):
        loop = self.get_event_loop()
        self._sink_queue = asyncio.Queue()
        self._sink_task = loop.create_task(self._sink_task_handler())

    async def _sink_task_handler(self):
        # Audio accumlation buffer
        buffer = bytearray()
        while True:
            try:
                frame = await self._sink_queue.get()
                if isinstance(frame, DataFrame):
                    await self.sink(frame)
                else:
                    await self.queue_frame(frame)

                if isinstance(frame, EndPipeFrame):
                    await self.stop()

                self._sink_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as ex:
                logging.exception(f"{self} error processing sink queue: {ex}")

    @abstractmethod
    async def sink(self, frame: DataFrame):
        #  Multimoding(text,audio,image) Sink
        raise NotImplementedError
