from __future__ import annotations

import shlex
from dataclasses import dataclass


@dataclass(slots=True)
class ParsedCommand:
    command: str
    args: list[str]


class CommandParser:
    def parse(self, raw: str) -> ParsedCommand:
        tokens = shlex.split(raw)
        if not tokens:
            return ParsedCommand(command="", args=[])
        return ParsedCommand(command=tokens[0].lower(), args=tokens[1:])
