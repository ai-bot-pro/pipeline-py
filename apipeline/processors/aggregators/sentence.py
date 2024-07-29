#
# Copyright (c) 2024, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import re

from apipeline.frames.control_frames import EndFrame, Frame
from apipeline.frames.data_frames import TextFrame
from apipeline.processors.frame_processor import FrameDirection, FrameProcessor


class SentenceAggregator(FrameProcessor):
    """This frame processor aggregates text frames into complete sentences.

    Frame input/output:
        TextFrame("Hello,") -> None
        TextFrame(" world.") -> TextFrame("Hello world.")

    Doctest:
    >>> async def print_frames(aggregator, frame):
    ...     async for frame in aggregator.process_frame(frame):
    ...         print(frame.text)

    >>> aggregator = SentenceAggregator()
    >>> asyncio.run(print_frames(aggregator, TextFrame("Hello,")))
    >>> asyncio.run(print_frames(aggregator, TextFrame(" world.")))
    Hello, world.
    """

    def __init__(self):
        super().__init__()
        self._aggregation = ""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TextFrame):
            m = re.search("(.*[?.!])(.*)", frame.text)
            if m:
                await self.push_frame(TextFrame(self._aggregation + m.group(1)))
                self._aggregation = m.group(2)
            else:
                self._aggregation += frame.text
        elif isinstance(frame, EndFrame):
            if self._aggregation:
                await self.push_frame(TextFrame(self._aggregation))
            await self.push_frame(frame)
        else:
            await self.push_frame(frame, direction)
