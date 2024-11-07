#
# Copyright (c) 2024, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

from typing import Callable, List, Tuple
import logging

from apipeline.frames.sys_frames import Frame, SystemFrame
from apipeline.processors.frame_processor import FrameDirection, FrameProcessor


class GatedAggregator(FrameProcessor):
    """Accumulate frames, with custom functions to start and stop accumulation.
    Yields gate-opening frame before any accumulated frames, then ensuing frames
    until and not including the gate-closed frame.
    """

    def __init__(
        self,
        gate_open_fn: Callable[["Frame"], bool],
        gate_close_fn: Callable[["Frame"], bool],
        init_start_open: bool = False,
        direction: FrameDirection = FrameDirection.DOWNSTREAM,
    ):
        super().__init__()
        self._gate_open_fn = gate_open_fn
        self._gate_close_fn = gate_close_fn
        self._gate_open = init_start_open
        self._direction = direction
        self._accumulator: List[Tuple[Frame, FrameDirection]] = []

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # We must not block system frames.
        if isinstance(frame, SystemFrame):
            await self.push_frame(frame, direction)
            return

        # Ignore frames that are not following the direction of this gate.
        if direction != self._direction:
            await self.push_frame(frame, direction)
            return

        old_state = self._gate_open
        if self._gate_open:
            self._gate_open = not self._gate_close_fn(frame)
        else:
            self._gate_open = self._gate_open_fn(frame)

        if old_state != self._gate_open:
            state = "open" if self._gate_open else "closed"
            logging.debug(f"Gate is now {state} because of {frame}")

        if self._gate_open:
            await self.push_frame(frame, direction)
            for f, d in self._accumulator:
                await self.push_frame(f, d)
            self._accumulator = []
        else:
            self._accumulator.append((frame, direction))
