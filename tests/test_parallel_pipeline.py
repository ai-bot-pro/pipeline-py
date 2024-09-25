import logging

from asyncio import AbstractEventLoop
import asyncio
import unittest
from apipeline.frames.control_frames import EndFrame
from apipeline.frames.sys_frames import CancelFrame, StopTaskFrame
from apipeline.pipeline.parallel_pipeline import ParallelPipeline
from apipeline.pipeline.pipeline import Pipeline, FrameDirection
from apipeline.pipeline.task import PipelineTask, PipelineParams
from apipeline.pipeline.runner import PipelineRunner
from apipeline.frames.data_frames import Frame, TextFrame, ImageRawFrame, AudioRawFrame
from apipeline.processors.frame_processor import FrameProcessor


"""
python -m unittest tests.test_parallel_pipeline.TestParallelPipeline
"""


class FrameTraceLogger(FrameProcessor):

    def __init__(
            self,
            tag: str,
            *,
            name: str | None = None,
            loop: AbstractEventLoop | None = None,
            **kwargs):
        super().__init__(name=name, loop=loop, **kwargs)
        self._tag = tag

    async def process_frame(
            self,
            frame: Frame,
            direction: FrameDirection = FrameDirection.DOWNSTREAM):
        await super().process_frame(frame, direction)

        from_to = f"{self._prev} ---> {self}"
        if direction == FrameDirection.UPSTREAM:
            from_to = f"{self} <--- {self._next} "
        if self._tag == "1.0":
            await asyncio.sleep(1)
        logging.info(f"Tag: {self._tag}; {from_to} get Frame: {frame}")
        await self.push_frame(frame, direction)


class TestParallelPipeline(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

        pipeline = Pipeline([
            FrameTraceLogger(tag="0"),
            ParallelPipeline(
                [FrameTraceLogger(tag="1.0"), FrameTraceLogger(tag="1.1")],
                [FrameTraceLogger(tag="2.0"), FrameTraceLogger(tag="2.1")],
            ),
            FrameTraceLogger(tag="3"),
        ])

        self.task = PipelineTask(
            pipeline,
            PipelineParams()
        )

    async def asyncTearDown(self):
        pass

    async def test_run(self):
        runner = PipelineRunner()
        await self.task.queue_frame(TextFrame("你好"))
        # await self.task.queue_frame(ImageRawFrame(image=bytes([]), size=(0, 0), format="PNG", mode="RGB"))
        # await self.task.queue_frame(AudioRawFrame(audio=bytes([])))
        await self.task.queue_frame(EndFrame())
        await runner.run(self.task)
