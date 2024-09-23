from asyncio import AbstractEventLoop
import logging
import unittest
from apipeline.frames.control_frames import EndFrame
from apipeline.frames.sys_frames import CancelFrame, StopTaskFrame
from apipeline.pipeline.pipeline import Pipeline, FrameDirection
from apipeline.pipeline.task import PipelineTask, PipelineParams
from apipeline.pipeline.runner import PipelineRunner
from apipeline.frames.data_frames import Frame, TextFrame, ImageRawFrame, AudioRawFrame
from apipeline.processors.filters.function_filter import FunctionFilter
from apipeline.processors.frame_processor import FrameProcessor
from apipeline.processors.logger import FrameLogger


"""
python -m unittest tests.test_filter.TestFunctionFilter
"""


class CheckFilter(FrameProcessor):
    def __init__(
            self,
            text: str | None = None,
            check_img: bool = False,
            *,
            name: str | None = None,
            loop: AbstractEventLoop | None = None,
            **kwargs):
        super().__init__(name=name, loop=loop, **kwargs)
        self._text = text
        self._check_img = check_img

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TextFrame):
            if self._text:
                assert frame.text != self._text, f"文本不应为:{self._text}"
        if self._check_img:
            assert not isinstance(frame, ImageRawFrame), "不应包含图像帧"
        await self.push_frame(frame, direction)


class TestFunctionFilter(unittest.IsolatedAsyncioTestCase):
    async def text_filter(self, frame: Frame):
        if isinstance(frame, TextFrame):
            if frame.text == self.text:
                return False
        return True

    async def image_filter(self, frame: Frame):
        if isinstance(frame, ImageRawFrame):
            return False
        return True

    async def asyncSetUp(self):
        logging.basicConfig(level="INFO")
        self.text = "你好"

        pipeline = Pipeline([
            FrameLogger(),
            FunctionFilter(filter=self.text_filter),
            CheckFilter(text=self.text),
            FunctionFilter(filter=self.image_filter),
            CheckFilter(text=self.text, check_img=True),
            FrameLogger(),
        ])

        self.task = PipelineTask(
            pipeline,
            PipelineParams()
        )

    async def asyncTearDown(self):
        pass

    async def test_run(self):
        runner = PipelineRunner()
        await self.task.queue_frame(TextFrame(self.text))
        await self.task.queue_frame(TextFrame("你好!"))
        await self.task.queue_frame(ImageRawFrame(image=bytes([]), size=(0, 0), format="PNG", mode="RGB"))
        await self.task.queue_frame(AudioRawFrame(audio=bytes([])))
        await self.task.queue_frame(EndFrame())
        await runner.run(self.task)
