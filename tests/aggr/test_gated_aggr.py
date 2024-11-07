import logging
import asyncio

import os
import unittest

from apipeline.frames import Frame, ImageRawFrame, DataFrame, TextFrame, EndFrame
from apipeline.pipeline.pipeline import Pipeline
from apipeline.pipeline.runner import PipelineRunner
from apipeline.pipeline.task import PipelineParams, PipelineTask
from apipeline.processors.aggregators.gated import GatedAggregator
from apipeline.processors.aggregators.sentence import SentenceAggregator
from apipeline.processors.frame_processor import FrameProcessor
from apipeline.processors.text_transformer import StatelessTextTransformer
from apipeline.processors.input_processor import InputFrameProcessor
from apipeline.processors.output_processor import OutputFrameProcessor


"""
python -m unittest tests.aggr.test_gated_aggr.TestGatedAggregator
"""


class TestGatedAggregator(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(
            level=os.getenv(
                "LOG_LEVEL",
                "info").upper(),
            format='%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s',
            handlers=[
                logging.StreamHandler()],
        )
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    async def asyncSetUp(self):
        pass

    async def asyncTearDown(self):
        pass

    async def test_gated_print(self):
        aggregator = GatedAggregator(
            gate_close_fn=lambda x: isinstance(x, TextFrame),
            gate_open_fn=lambda x: isinstance(x, ImageRawFrame),
            init_start_open=False,
        )
        out_processor = OutputFrameProcessor(cb=lambda x: print(f"sink_callback print frame: {x}"))
        pipeline = Pipeline([aggregator, out_processor])
        task = PipelineTask(pipeline, PipelineParams())

        await task.queue_frame(TextFrame("Hello, "))
        await task.queue_frame(TextFrame("Hello again."))
        await task.queue_frame(ImageRawFrame(
            image=bytes([]),
            size=(0, 0),
            format="JPEG",
            mode="RGB",
        ))
        await task.queue_frame(TextFrame("Goodbye1."))
        await task.queue_frame(TextFrame("Goodbye2."))
        await task.queue_frame(ImageRawFrame(
            image=bytes([]),
            size=(0, 0),
            format="JPEG",
            mode="RGB",
        ))
        await task.queue_frame(EndFrame())

        runner = PipelineRunner()
        await asyncio.gather(runner.run(task))
