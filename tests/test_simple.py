import unittest
from apipeline.frames.control_frames import EndFrame
from apipeline.frames.sys_frames import CancelFrame, StopTaskFrame
from apipeline.pipeline.pipeline import Pipeline, FrameDirection
from apipeline.pipeline.task import PipelineTask, PipelineParams
from apipeline.pipeline.runner import PipelineRunner
from apipeline.frames.data_frames import Frame, TextFrame, ImageRawFrame, AudioRawFrame
from apipeline.processors.frame_processor import FrameProcessor


"""
python -m unittest tests.test_simple.TestSimple
"""


class FrameTraceLogger(FrameProcessor):

    async def process_frame(
            self,
            frame: Frame,
            direction: FrameDirection = FrameDirection.DOWNSTREAM):
        await super().process_frame(frame, direction)

        from_to = f"{self._prev} ---> {self}"
        if direction == FrameDirection.UPSTREAM:
            from_to = f"{self} <--- {self._next} "
        print(f"{from_to} get Frame: {frame}")


class TestSimple(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):

        pipeline = Pipeline([
            FrameTraceLogger(),
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
        await self.task.queue_frame(ImageRawFrame(image=bytes([]), size=(0, 0), format="PNG", mode="RGB"))
        await self.task.queue_frame(AudioRawFrame(audio=bytes([])))
        await self.task.queue_frame(EndFrame())
        await runner.run(self.task)
