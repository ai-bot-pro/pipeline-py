import logging

import unittest
from apipeline.frames.control_frames import EndFrame
from apipeline.pipeline.pipeline import Pipeline, FrameDirection
from apipeline.pipeline.sync_parallel_pipeline import SyncParallelPipeline
from apipeline.pipeline.task import PipelineTask, PipelineParams
from apipeline.pipeline.runner import PipelineRunner
from apipeline.frames.data_frames import TextFrame
from apipeline.processors.logger import FrameLogger


"""
python -m unittest tests.pipeline.test_sync_parallel_pipeline
"""


class TestParallelPipeline(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        pass

    async def test_sync_parallel_pipeline(self):
        pipeline = Pipeline(
            [
                FrameLogger(prefix="0"),
                SyncParallelPipeline(
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
