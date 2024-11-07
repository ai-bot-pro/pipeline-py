
from apipeline.processors.frame_processor import FrameProcessor


class NullFilter(FrameProcessor):
    """This filter doesn't allow passing any frames up or downstream."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
