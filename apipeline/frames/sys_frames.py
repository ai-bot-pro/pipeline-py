from typing import Any, Mapping, List
from dataclasses import dataclass


from .base import Frame

#
# System frames
#


@dataclass
class SystemFrame(Frame):
    pass


@dataclass
class CancelFrame(SystemFrame):
    """Indicates that a pipeline needs to stop right away."""
    pass


@dataclass
class ErrorFrame(SystemFrame):
    """This is used notify upstream that an error has occurred downstream the
    pipeline."""
    error: str
    fatal: bool = False

    def __str__(self):
        return f"{self.name}(error: {self.error}, fatal: {self.fatal})"


@dataclass
class StopTaskFrame(SystemFrame):
    """Indicates that a pipeline task should be stopped but that the pipeline
    processors should be kept in a running state. This is normally queued from
    the pipeline task.

    """
    pass


@dataclass
class StartInterruptionFrame(SystemFrame):
    """e.g. Emitted by VAD to indicate that a user has started speaking (i.e. is
    interruption). This is similar to UserStartedSpeakingFrame except that it
    should be pushed concurrently with other frames (so the order is not
    guaranteed).

    """
    pass


@dataclass
class StopInterruptionFrame(SystemFrame):
    """e.g. Emitted by VAD to indicate that a user has stopped speaking (i.e. no more
    interruptions). This is similar to UserStoppedSpeakingFrame except that it
    should be pushed concurrently with other frames (so the order is not
    guaranteed).

    """
    pass


@dataclass
class MetricsFrame(SystemFrame):
    """Emitted by processor that can compute metrics like latencies.
    """
    ttfb: List[Mapping[str, Any]] | None = None
    processing: List[Mapping[str, Any]] | None = None
    tokens: List[Mapping[str, Any]] | None = None
    characters: List[Mapping[str, Any]] | None = None

    def __str__(self):
        p_str = f"{self.name} ttfb:{self.ttfb} | processing:{self.processing} | tokens:{self.tokens} | characters:{self.characters}"
        return p_str
