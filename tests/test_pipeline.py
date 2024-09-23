import logging
import asyncio

import unittest

from apipeline.frames.control_frames import EndFrame
from apipeline.frames.data_frames import DataFrame, TextFrame
from apipeline.pipeline.pipeline import Pipeline
from apipeline.pipeline.runner import PipelineRunner
from apipeline.pipeline.task import PipelineParams, PipelineTask
from apipeline.processors.aggregators.sentence import SentenceAggregator
from apipeline.processors.frame_processor import FrameProcessor
from apipeline.processors.text_transformer import StatelessTextTransformer
from apipeline.processors.input_processor import InputFrameProcessor
from apipeline.processors.output_processor import OutputFrameProcessor


"""
python -m unittest tests.test_pipeline.TestSentenceAggregatorPipeline.test_pipeline_simple
python -m unittest tests.test_pipeline.TestSentenceAggregatorPipeline.test_pipeline_multiple_stages
"""


class TestSentenceAggregatorPipeline(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    async def asyncSetUp(self):
        pass

    async def asyncTearDown(self):
        pass

    async def test_pipeline_simple(self):
        aggregator = SentenceAggregator()

        self.text = []

        async def sink_callback(frame: DataFrame):
            print(f"sink_callback print frame: {frame}")
            self.text.append(frame.text)
            # note: if assert false, wait for a while
            # self.assertEqual(frame.text, 'Hello, world.')
        out_processor = OutputFrameProcessor(cb=sink_callback)
        # out_processor = OutputFrameProcessor(cb=lambda x: print(f"sink_callback print frame: {x}"))

        pipeline = Pipeline([aggregator, out_processor])
        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))

        await task.queue_frame(TextFrame("Hello, "))
        await task.queue_frame(TextFrame("world."))
        await task.queue_frame(TextFrame("hi"))
        await task.queue_frame(EndFrame())

        runner = PipelineRunner()

        await asyncio.gather(runner.run(task))
        self.assertEqual(self.text, ["Hello, world.", "hi"])

    async def test_pipeline_multiple_stages(self):
        sentence_aggregator = SentenceAggregator()

        def to_upper(x: str):
            return x.upper()
        to_upper_processor = StatelessTextTransformer(to_upper)
        add_space_processor = StatelessTextTransformer(lambda x: x + " ")

        self.text = []

        async def sink_callback(frame: DataFrame):
            print(f"sink_callback print frame: {frame}")
            self.text.append(frame.text)
        out_processor = OutputFrameProcessor(cb=sink_callback)

        pipeline = Pipeline([
            add_space_processor,
            sentence_aggregator,
            to_upper_processor,
            out_processor,
        ])
        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))

        sentence = "Hello, world. It's me, a pipeline."
        for c in sentence:
            await task.queue_frame(TextFrame(c))
        await task.queue_frame(EndFrame())

        runner = PipelineRunner()

        await asyncio.gather(runner.run(task))

        print(self.text)
        self.assertEqual(self.text, [
            "H E L L O ,   W O R L D . ",
            "  I T ' S   M E ,   A   P I P E L I N E . ",
        ])
