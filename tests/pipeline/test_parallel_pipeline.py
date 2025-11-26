import logging

from asyncio import AbstractEventLoop
import asyncio
import unittest
from apipeline.frames.control_frames import EndFrame
from apipeline.pipeline.parallel_pipeline import ParallelPipeline
from apipeline.pipeline.pipeline import Pipeline, FrameDirection
from apipeline.pipeline.task import PipelineTask, PipelineParams
from apipeline.pipeline.runner import PipelineRunner
from apipeline.frames.data_frames import Frame, TextFrame, ImageRawFrame, AudioRawFrame
from apipeline.processors.frame_processor import FrameProcessor
from apipeline.processors.logger import FrameLogger


"""
python -m unittest tests.pipeline.test_parallel_pipeline.TestParallelPipeline
"""


class FrameTraceLogger(FrameProcessor):
    def __init__(
        self,
        prefix: str,
        *,
        name: str | None = None,
        loop: AbstractEventLoop | None = None,
        **kwargs,
    ):
        super().__init__(name=name, loop=loop, **kwargs)
        self._prefix = prefix

    async def process_frame(
        self, frame: Frame, direction: FrameDirection = FrameDirection.DOWNSTREAM
    ):
        await super().process_frame(frame, direction)

        from_to = f"{self._prev} ---> {self}"
        if direction == FrameDirection.UPSTREAM:
            from_to = f"{self} <--- {self._next} "
        if self._prefix == "1.0":
            await asyncio.sleep(1)
        logging.info(f"prefix: {self._prefix}; {from_to} get Frame: {frame}")
        await self.push_frame(frame, direction)


class TestParallelPipeline(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        pass

    async def test_parallel_pipeline(self):
        pipeline = Pipeline(
            [
                FrameLogger(prefix="0"),
                ParallelPipeline(
                    [
                        FrameLogger(prefix="1.0", sleep_time_s=1),
                        FrameLogger(prefix="1.1"),
                    ],
                    [
                        FrameLogger(prefix="2.0"),
                        FrameLogger(prefix="2.1"),
                    ],
                ),
                FrameLogger(prefix="3"),
            ]
        )
        task = PipelineTask(pipeline, PipelineParams())
        runner = PipelineRunner()
        await task.queue_frame(TextFrame("你好"))
        await task.queue_frame(EndFrame())
        await runner.run(task)

    async def asyncTearDown(self):
        pass
