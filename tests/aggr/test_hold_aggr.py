import logging
import asyncio

import os
import unittest

from apipeline.frames import Frame, ImageRawFrame, DataFrame, TextFrame, EndFrame, StopTaskFrame
from apipeline.frames.control_frames import ControlFrame, SyncNotifyFrame
from apipeline.frames.sys_frames import CancelFrame, StartInterruptionFrame, StopInterruptionFrame
from apipeline.notifiers.event_notifier import EventNotifier
from apipeline.pipeline.pipeline import Pipeline
from apipeline.pipeline.runner import PipelineRunner
from apipeline.pipeline.task import PipelineParams, PipelineTask
from apipeline.processors.aggregators.hold import HoldFramesAggregator, HoldLastFrameAggregator
from apipeline.processors.filters.function_filter import FunctionFilter
from apipeline.processors.frame_processor import FrameDirection, FrameProcessor
from apipeline.processors.user_idle_processor import UserIdleProcessor


"""
python -m unittest tests.aggr.test_hold_aggr.TestAggregator.test_hold_frames_print
python -m unittest tests.aggr.test_hold_aggr.TestAggregator.test_hold_frame_print
"""


class PrintOutFrameProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        logging.info(f"{frame}")
        if isinstance(frame, TextFrame) and frame.text == "end":
            await self.push_frame(EndFrame(), FrameDirection.UPSTREAM)
            logging.info("End ok")
        if isinstance(frame, TextFrame) and frame.text == "cancel":
            await self.push_frame(CancelFrame(), FrameDirection.UPSTREAM)
            logging.info("Cancel ok")
        if isinstance(frame, TextFrame) and frame.text == "endTask":
            await self.push_frame(StopTaskFrame(), FrameDirection.UPSTREAM)
            logging.info("End Task ok")


class TestAggregator(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(
            level=os.getenv("LOG_LEVEL", "info").upper(),
            format="%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )

    @classmethod
    def tearDownClass(cls):
        pass

    async def asyncSetUp(self):
        self._notifier = EventNotifier()

    async def asyncTearDown(self):
        pass

    async def wake_notifier_filter(self, frame: Frame):
        if isinstance(frame, SyncNotifyFrame):
            # await asyncio.sleep(1)
            await self._notifier.notify()
        return True

    async def test_hold_frames_print(self):
        async def idle_callback(processor: UserIdleProcessor):
            await self._notifier.notify()

        user_idle = UserIdleProcessor(callback=idle_callback, timeout=1.0)

        aggregator = HoldFramesAggregator(
            notifier=self._notifier,
            hold_frame_classes=(TextFrame,),
        )
        pipeline = Pipeline(
            [
                aggregator,
                # user_idle,
                FunctionFilter(filter=self.wake_notifier_filter),
                PrintOutFrameProcessor(),
            ]
        )
        task = PipelineTask(pipeline, PipelineParams())

        await task.queue_frame(TextFrame("Hello many frames, "))
        await task.queue_frame(SyncNotifyFrame())
        await task.queue_frame(
            ImageRawFrame(
                image=bytes([]),
                size=(0, 0),
                format="JPEG",
                mode="RGB",
            )
        )
        await task.queue_frame(TextFrame("Goodbye1."))
        await task.queue_frame(
            ImageRawFrame(
                image=bytes([]),
                size=(0, 0),
                format="PNG",
                mode="RGB",
            )
        )
        # await task.queue_frame(EndFrame())
        # await task.queue_frame(TextFrame("end"))
        await task.queue_frame(StopTaskFrame())

        runner = PipelineRunner()
        await asyncio.gather(runner.run(task))

    async def test_hold_frame_print(self):
        async def idle_callback(processor: UserIdleProcessor):
            await self._notifier.notify()

        user_idle = UserIdleProcessor(callback=idle_callback, timeout=1.0)

        aggregator = HoldLastFrameAggregator(
            notifier=self._notifier,
            hold_frame_classes=(TextFrame,),
        )
        pipeline = Pipeline(
            [
                aggregator,
                # user_idle,
                FunctionFilter(filter=self.wake_notifier_filter),
                PrintOutFrameProcessor(),
            ]
        )
        task = PipelineTask(pipeline, PipelineParams())

        await task.queue_frame(TextFrame("Hello last one frame, "))
        await task.queue_frame(SyncNotifyFrame())
        await task.queue_frame(
            ImageRawFrame(
                image=bytes([]),
                size=(0, 0),
                format="JPEG",
                mode="RGB",
            )
        )
        await task.queue_frame(TextFrame("Goodbye1."))
        await task.queue_frame(
            ImageRawFrame(
                image=bytes([]),
                size=(0, 0),
                format="PNG",
                mode="RGB",
            )
        )
        # await task.queue_frame(EndFrame())
        await task.queue_frame(TextFrame("end"))
        await task.queue_frame(TextFrame("endTask"))
        await task.queue_frame(StopTaskFrame())

        runner = PipelineRunner()
        await asyncio.gather(runner.run(task))
