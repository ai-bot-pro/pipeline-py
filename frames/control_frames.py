from dataclasses import dataclass

from .base import Frame

#
# Control frames
#


@dataclass
class ControlFrame(Frame):
    pass


@dataclass
class EndPipeFrame(ControlFrame):
    """Indicates that a pipeline has ended and frame processors and pipelines
    should be shut down. If the transport receives this frame, it will stop
    sending frames to its output channel(s) and close all its threads. Note,
    that this is a control frame, which means it will received in the order it
    was sent (unline system frames).

    """
    pass
