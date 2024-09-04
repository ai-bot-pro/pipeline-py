import unittest
from apipeline.frames.control_frames import EndFrame
from apipeline.frames.sys_frames import CancelFrame
from apipeline.pipeline.pipeline import Pipeline, FrameDirection
from apipeline.pipeline.task import PipelineTask, PipelineParams
from apipeline.pipeline.runner import PipelineRunner
from apipeline.frames.data_frames import Frame, TextFrame
from apipeline.processors.frame_processor import FrameProcessor


"""
python -m unittest tests.test_simple.TestSimple
"""


class PushProcessor(FrameProcessor):
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        await self.push_frame(TextFrame("你好"))
        print("ok")


class FrameTraceLogger(FrameProcessor):

    async def process_frame(
            self,
            frame: Frame,
            direction: FrameDirection = FrameDirection.DOWNSTREAM):
        await super().process_frame(frame, direction)

        from_to = f"{self._prev} ---> {self}"
        if direction == FrameDirection.UPSTREAM:
            from_to = f"{self} <--- {self._next} "
        elif isinstance(frame, TextFrame):
            print(f"{from_to} get TextFrame: {frame}, text:{len(frame.text)}")


class TestSimple(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):

        pipeline = Pipeline([
            PushProcessor(),
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
        # await self.task.queue_frame(TextFrame("你好"))
        await runner.run(self.task)
