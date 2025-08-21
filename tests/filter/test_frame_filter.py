from asyncio import AbstractEventLoop
import logging
import os
import unittest

from apipeline.frames.control_frames import EndFrame
from apipeline.pipeline.pipeline import Pipeline, FrameDirection
from apipeline.pipeline.task import PipelineTask, PipelineParams
from apipeline.pipeline.runner import PipelineRunner
from apipeline.frames.data_frames import Frame, TextFrame, ImageRawFrame, AudioRawFrame
from apipeline.processors.filters.frame_filter import FrameFilter
from apipeline.processors.frame_processor import FrameProcessor
from apipeline.processors.logger import FrameLogger


"""
python -m unittest tests.filter.test_frame_filter.TestFilter
"""


class CheckFilter(FrameProcessor):
    def __init__(
        self,
        text: str | None = None,
        check_img: bool = False,
        *,
        name: str | None = None,
        loop: AbstractEventLoop | None = None,
        **kwargs,
    ):
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


class TestFilter(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        logging.basicConfig(
            level=os.getenv("LOG_LEVEL", "info").upper(),
            format="%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        self.text = "你好"

        pipeline = Pipeline(
            [
                # FrameLogger(include_frame_types=[TextFrame]),
                FrameFilter(include_frame_types=[TextFrame]),
                # FrameLogger(),
                CheckFilter(text=self.text),
                FrameFilter(include_frame_types=[ImageRawFrame]),
                FrameLogger(),
                CheckFilter(text=self.text, check_img=True),
            ]
        )

        self.task = PipelineTask(pipeline, PipelineParams())

    async def asyncTearDown(self):
        pass

    async def test_run(self):
        runner = PipelineRunner()
        await self.task.queue_frame(TextFrame(self.text))
        await self.task.queue_frame(TextFrame("你好!"))
        await self.task.queue_frame(
            ImageRawFrame(image=bytes([]), size=(0, 0), format="PNG", mode="RGB")
        )
        await self.task.queue_frame(AudioRawFrame(audio=bytes([])))
        await self.task.queue_frame(EndFrame())
        await runner.run(self.task)
