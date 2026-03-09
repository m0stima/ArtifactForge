from __future__ import annotations

from dataclasses import dataclass, field

from commands.parser import ParsedCommand


@dataclass
class CommandDispatcher:
    history: list[str] = field(default_factory=list)

    def execute(self, cmd: ParsedCommand) -> str:
        if not cmd.command:
            return ""
        self.history.append(" ".join([cmd.command, *cmd.args]).strip())

        if cmd.command == "help":
            return "Commands: help clear reset back refresh stats history show open export search grep filter sort group pivot tree children parent suspicious listening remote port"
        if cmd.command == "history":
            return "\n".join(self.history[-20:])
        if cmd.command in {"clear", "reset", "back", "refresh", "stats"}:
            return f"Executed {cmd.command}."
        if cmd.command == "export":
            if cmd.args and cmd.args[0] in {"json", "csv", "md"}:
                return f"Export queued: {cmd.args[0]}"
            return "Usage: export <json|csv|md>"
        if cmd.command in {"show", "open", "search", "grep", "tree", "suspicious", "listening"}:
            return f"Executed analytical command: {cmd.command} {' '.join(cmd.args)}"
        if cmd.command in {"children", "parent", "remote", "port", "pivot", "sort", "group", "filter", "from", "to", "around"}:
            return f"Executed contextual command: {cmd.command} {' '.join(cmd.args)}"
        return f"Unknown command: {cmd.command}"
