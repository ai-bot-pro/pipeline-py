from typing import Tuple
from dataclasses import dataclass


from .base import Frame


@dataclass
class DataFrame(Frame):
    pass


@dataclass
class TextFrame(DataFrame):
    """A chunk of text. Emitted by LLM services, consumed by TTS services, can
    be used to send text through pipelines.

    """
    text: str

    def __str__(self):
        return f"{self.name}(text: {self.text})"


@dataclass
class AudioRawFrame(DataFrame):
    """A chunk of audio. Will be played by the transport if the transport's
    microphone has been enabled.

    """
    audio: bytes
    sample_rate: int = 16000
    num_channels: int = 1
    sample_width: int = 2

    def __post_init__(self):
        super().__post_init__()
        self.num_frames = int(len(self.audio) / (self.num_channels * self.sample_width))

    def __str__(self):
        return f"{self.name}(size: {len(self.audio)}, frames: {self.num_frames}, sample_rate: {self.sample_rate},sample_width: {self.sample_width}, channels: {self.num_channels})"


@dataclass
class ImageRawFrame(DataFrame):
    """An image. Will be shown by the transport if the transport's camera is
    enabled.

    e.g.: image info from PIL.Image
    """
    image: bytes
    size: Tuple[int, int]
    format: str | None
    # https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
    mode: str | None

    def __str__(self):
        return f"{self.name}(size: {self.size}, format: {self.format}, mode: {self.mode})"
