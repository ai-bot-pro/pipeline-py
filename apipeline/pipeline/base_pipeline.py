from typing import List

from apipeline.processors.frame_processor import FrameProcessor
from apipeline.utils.asyncio.task_manager import BaseTaskManager


class BasePipeline(FrameProcessor):
    def __init__(self):
        super().__init__()
        self._processors: List[FrameProcessor] = []
        self._pipelines: List[BasePipeline] = []

    @property
    def processors(self):
        return self._processors

    @property
    def pipelines(self):
        return self._pipelines

    async def setup(self, task_manager: BaseTaskManager):
        await super().setup(task_manager)
        await self.setup_processors(task_manager)
        await self.setup_pipelines(task_manager)

    async def setup_processors(self, task_manager: BaseTaskManager):
        for p in self._processors:
            await p.setup(task_manager)

    async def setup_pipelines(self, task_manager: BaseTaskManager):
        for p in self._pipelines:
            for processor in p.processors:
                await processor.setup(task_manager)
