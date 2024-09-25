#
# Copyright (c) 2024, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

from enum import Enum
import asyncio
import logging
import time


from apipeline.frames.sys_frames import ErrorFrame, Frame, MetricsFrame, StartInterruptionFrame
from apipeline.frames.control_frames import StartFrame
from apipeline.utils.obj import obj_count, obj_id


class FrameDirection(Enum):
    DOWNSTREAM = 1
    UPSTREAM = 2


class FrameProcessorMetrics:
    def __init__(self, name: str):
        self._name = name
        self._start_ttfb_time = 0
        self._start_processing_time = 0
        self._should_report_ttfb = True

    async def start_ttfb_metrics(self, report_only_initial_ttfb):
        if self._should_report_ttfb:
            self._start_ttfb_time = time.time()
            self._should_report_ttfb = not report_only_initial_ttfb

    async def stop_ttfb_metrics(self):
        if self._start_ttfb_time == 0:
            return None

        value = time.time() - self._start_ttfb_time
        logging.debug(f"{self._name} TTFB: {value}")
        ttfb = {
            "processor": self._name,
            "value": value
        }
        self._start_ttfb_time = 0
        return MetricsFrame(ttfb=[ttfb])

    async def start_processing_metrics(self):
        self._start_processing_time = time.time()

    async def stop_processing_metrics(self):
        if self._start_processing_time == 0:
            return None

        value = time.time() - self._start_processing_time
        logging.debug(f"{self._name} processing time: {value}")
        processing = {
            "processor": self._name,
            "value": value
        }
        self._start_processing_time = 0
        return MetricsFrame(processing=[processing])


class FrameProcessor:

    def __init__(
            self,
            *,
            name: str | None = None,
            loop: asyncio.AbstractEventLoop | None = None,
            **kwargs):
        self.id: int = obj_id()
        self.name = name or f"{self.__class__.__name__}#{obj_count(self)}"
        self._parent_pipeline: "FrameProcessor" | None = None
        self._prev: "FrameProcessor" | None = None
        self._next: "FrameProcessor" | None = None
        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_running_loop()

        # Properties
        self._allow_interruptions = False
        self._enable_metrics = False
        self._enable_usage_metrics = False
        self._report_only_initial_ttfb = False

        # Metrics
        self._metrics = FrameProcessorMetrics(name=self.name)

        # SkipFrames
        self._skip_frames = []

    @property
    def interruptions_allowed(self):
        return self._allow_interruptions

    @property
    def metrics_enabled(self):
        return self._enable_metrics

    @property
    def usage_metrics_enabled(self):
        return self._enable_usage_metrics

    @property
    def report_only_initial_ttfb(self):
        return self._report_only_initial_ttfb

    def add_skip_frame(self, frame: Frame):
        self._skip_frames.append(frame)

    def can_generate_metrics(self) -> bool:
        return False

    async def start_ttfb_metrics(self):
        if self.can_generate_metrics() and self.metrics_enabled:
            await self._metrics.start_ttfb_metrics(self._report_only_initial_ttfb)

    async def stop_ttfb_metrics(self):
        if self.can_generate_metrics() and self.metrics_enabled:
            frame = await self._metrics.stop_ttfb_metrics()
            if frame:
                await self.push_frame(frame)

    async def start_processing_metrics(self):
        if self.can_generate_metrics() and self.metrics_enabled:
            await self._metrics.start_processing_metrics()

    async def stop_processing_metrics(self):
        if self.can_generate_metrics() and self.metrics_enabled:
            frame = await self._metrics.stop_processing_metrics()
            if frame:
                await self.push_frame(frame)

    async def stop_all_metrics(self):
        await self.stop_ttfb_metrics()
        await self.stop_processing_metrics()

    async def cleanup(self):
        pass

    def link(self, processor: "FrameProcessor"):
        self._next = processor
        processor._prev = self
        logging.debug(f"Linking {self} -> {self._next}")

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def set_parent_pipeline(self, pipeline: "FrameProcessor"):
        self._parent_pipeline = pipeline

    def get_parent_pipeline(self) -> "FrameProcessor":
        return self._parent_pipeline

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if frame in self._skip_frames:
            return

        if isinstance(frame, StartFrame):
            self._allow_interruptions = frame.allow_interruptions
            self._enable_metrics = frame.enable_metrics
            self._enable_usage_metrics = frame.enable_usage_metrics
            self._report_only_initial_ttfb = frame.report_only_initial_ttfb
        elif isinstance(frame, StartInterruptionFrame):
            await self.stop_all_metrics()

    async def push_error(self, error: ErrorFrame):
        await self.push_frame(error, FrameDirection.UPSTREAM)

    async def push_frame(self, frame: Frame, direction: FrameDirection = FrameDirection.DOWNSTREAM):
        try:
            if direction == FrameDirection.DOWNSTREAM and self._next:
                if hasattr(logging, "trace"):
                    logging.trace(f"Pushing {frame} from {self} to {self._next}")
                else:
                    logging.debug(f"Pushing {frame} from {self} to {self._next}")
                await self._next.process_frame(frame, direction)
            elif direction == FrameDirection.UPSTREAM and self._prev:
                if hasattr(logging, "trace"):
                    logging.trace(f"Pushing {frame} from {self} to {self._next}")
                else:
                    logging.debug(f"Pushing {frame} upstream from {self} to {self._prev}")
                await self._prev.process_frame(frame, direction)
        except Exception as e:
            logging.exception(f"Uncaught exception in {self}: {e}")

    def __str__(self):
        return self.name
