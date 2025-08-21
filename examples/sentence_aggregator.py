import asyncio
from apipeline.frames.control_frames import EndFrame
from apipeline.frames.data_frames import TextFrame
from apipeline.pipeline.pipeline import Pipeline
from apipeline.pipeline.runner import PipelineRunner
from apipeline.pipeline.task import PipelineParams, PipelineTask
from apipeline.processors.aggregators.sentence import SentenceAggregator
from apipeline.processors.output_processor import OutputFrameProcessor


async def main():
    aggregator = SentenceAggregator()
    out_processor = OutputFrameProcessor(cb=lambda x: print(f"sink_callback print frame: {x}"))
    pipeline = Pipeline([aggregator, out_processor])
    task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))

    await task.queue_frame(TextFrame("你好，hello. hi"))
    await task.queue_frame(TextFrame("你叫什么？"))
    await task.queue_frame(TextFrame("Hello, "))
    await task.queue_frame(TextFrame("world."))
    await task.queue_frame(TextFrame("hi"))
    await task.queue_frame(EndFrame())

    runner = PipelineRunner()
    await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())
