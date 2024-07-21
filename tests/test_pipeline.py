import asyncio

import unittest

from frames.control_frames import EndPipeFrame
from frames.data_frames import TextFrame
from pipeline.pipeline import Pipeline
from pipeline.runner import PipelineRunner
from pipeline.task import PipelineParams, PipelineTask
from processors.aggregators.sentence import SentenceAggregator
from processors.frame_processor import FrameProcessor
from processors.text_transformer import StatelessTextTransformer
from processors.input_processor import InputFrameProcessor
from processors.output_processor import OutputFrameProcessor


class TestSentenceAggregatorPipeline(unittest.IsolatedAsyncioTestCase):

    async def test_pipeline_simple(self):
        aggregator = SentenceAggregator()

        incoming_queue = asyncio.Queue()
        in_processor = InputFrameProcessor(
            in_queue=incoming_queue,
            name="input_frame_processor"
        )
        outgoing_queue = asyncio.Queue()
        out_processor = OutputFrameProcessor(
            out_queue=outgoing_queue,
            cb=lambda frame: print(frame),
            name="output_frame_processor"
        )

        pipeline = Pipeline([in_processor, aggregator, out_processor])
        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))

        await incoming_queue.put(TextFrame("Hello, "))
        await incoming_queue.put(TextFrame("world."))
        await incoming_queue.put(EndPipeFrame())

        runner = PipelineRunner()
        await runner.run(task)

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
