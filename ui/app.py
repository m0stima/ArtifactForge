from __future__ import annotations

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, RichLog, Static, DataTable
except Exception:  # pragma: no cover
    App = object
    ComposeResult = object

    class ArtifactForgeApp:  # type: ignore[override]
        def run(self) -> None:
            print("Textual is not available in this environment.")
else:
    from commands.dispatcher import CommandDispatcher
    from commands.parser import CommandParser
    from ui.ascii_logo import COMPACT, SPLASH_BANNER

    class ArtifactForgeApp(App):
        CSS = """
        #root { layout: vertical; }
        #workspace { height: 1fr; }
        #nav { width: 28%; border: round #666666; }
        #analysis { width: 72%; border: round #666666; }
        #cli { height: 8; border: round #666666; }
        """

        def __init__(self) -> None:
            super().__init__()
            self.command_parser = CommandParser()
            self.dispatcher = CommandDispatcher()

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static(SPLASH_BANNER, id="splash")
            yield Static(COMPACT)
            yield Static("Main Menu: Create New Case | Open Existing Case | Settings | Help | Exit")
            with Container(id="root"):
                with Horizontal(id="workspace"):
                    with Vertical(id="nav"):
                        yield Label("Case")
                        yield ListView(
                            ListItem(Label("Overview")),
                            ListItem(Label("Artifacts")),
                            ListItem(Label("Timeline")),
                            ListItem(Label("Findings")),
                            ListItem(Label("Case Metadata")),
                        )
                    with Vertical(id="analysis"):
                        yield Label("Analysis")
                        table = DataTable()
                        table.add_columns("Field", "Value")
                        table.add_row("Status", "Ready")
                        table.add_row("Hint", "Use CLI for analytics commands")
                        yield table
                with Vertical(id="cli"):
                    yield RichLog(id="log", wrap=True, highlight=True)
                    yield Input(placeholder="ArtifactForge CLI >", id="cli_input")
            yield Footer()

        def on_input_submitted(self, event: Input.Submitted) -> None:
            if event.input.id != "cli_input":
                return
            cmd = self.command_parser.parse(event.value)
            output = self.dispatcher.execute(cmd)
            self.query_one("#log", RichLog).write(f"> {event.value}\n{output}")
            event.input.value = ""
