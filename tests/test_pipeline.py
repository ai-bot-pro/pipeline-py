import asyncio

import unittest

from frames.control_frames import EndPipeFrame
from frames.data_frames import DataFrame, TextFrame
from pipeline.pipeline import Pipeline
from pipeline.runner import PipelineRunner
from pipeline.task import PipelineParams, PipelineTask
from processors.aggregators.sentence import SentenceAggregator
from processors.frame_processor import FrameProcessor
from processors.text_transformer import StatelessTextTransformer
from processors.input_processor import InputFrameProcessor
from processors.output_processor import OutputFrameProcessor


"""
python -m unittest  tests.test_pipeline.TestSentenceAggregatorPipeline.test_pipeline_simple
"""


class TestSentenceAggregatorPipeline(unittest.IsolatedAsyncioTestCase):

    async def test_pipeline_simple(self):
        aggregator = SentenceAggregator()

        def sink_callback(frame: DataFrame):
            print(f"sink_callback print frame: {frame}")
            # note: if assert false, wait for a while
            self.assertEqual(frame.text, 'Hello, world.')
        out_processor = OutputFrameProcessor(cb=sink_callback)
        # out_processor = OutputFrameProcessor(cb=lambda x: print(f"sink_callback print frame: {x}"))

        pipeline = Pipeline([aggregator, out_processor])
        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))

        await task.queue_frame(TextFrame("Hello, "))
        await task.queue_frame(TextFrame("world."))
        await task.queue_frame(EndPipeFrame())

        runner = PipelineRunner()

        await asyncio.gather(runner.run(task))

    async def test_pipeline_multiple_stages(self):
        sentence_aggregator = SentenceAggregator()
        to_upper = StatelessTextTransformer(lambda x: x.upper())
        add_space = StatelessTextTransformer(lambda x: x + " ")

        outgoing_queue = asyncio.Queue()
        incoming_queue = asyncio.Queue()
        pipeline = Pipeline(
            [add_space, sentence_aggregator, to_upper],
            incoming_queue,
            outgoing_queue
        )

        sentence = "Hello, world. It's me, a pipeline."
        for c in sentence:
            await incoming_queue.put(TextFrame(c))
        await incoming_queue.put(EndPipeFrame())

        await pipeline.run_pipeline()

        self.assertEqual(
            await outgoing_queue.get(), TextFrame("H E L L O ,   W O R L D .")
        )
        self.assertEqual(
            await outgoing_queue.get(),
            TextFrame("   I T ' S   M E ,   A   P I P E L I N E ."),
        )
        # leftover little bit because of the spacing
        self.assertEqual(
            await outgoing_queue.get(),
            TextFrame(" "),
        )
        self.assertIsInstance(await outgoing_queue.get(), EndPipeFrame)
