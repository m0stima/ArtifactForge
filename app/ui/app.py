from __future__ import annotations

from pathlib import Path

from app.cases.service import CaseService
from app.commands.dispatcher import CommandDispatcher
from app.commands.parser import CommandParser
from app.models.case import CaseModel
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.finding_repository import FindingsRepository
from app.repositories.timeline_repository import TimelineRepository
from app.services.discovery import XMLDiscovery
from app.services.indexer import IndexingService
from app.services.workspace import WorkspaceDataService
from app.ui.ascii_logo import COMPACT, SPLASH_BANNER

try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.screen import Screen
    from textual.widgets import Button, DataTable, Footer, Header, Input, Label, ListItem, ListView, RichLog, Static
except Exception:  # pragma: no cover
    class ArtifactForgeApp:  # type: ignore[override]
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def run(self) -> None:
            print("Textual is not available in this environment.")
else:

    class SplashScreen(Screen):
        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static(SPLASH_BANNER)
            yield Label("Loading ArtifactForge...")

        def on_mount(self) -> None:
            self.set_timer(0.8, lambda: self.app.switch_screen(MainMenuScreen()))

    class MainMenuScreen(Screen):
        BINDINGS = [("escape", "quit", "Exit")]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static(SPLASH_BANNER)
            yield Static(COMPACT)
            yield Label("Main Menu (↑/↓ + Enter)")
            yield ListView(
                ListItem(Label("Create New Case"), id="menu_create"),
                ListItem(Label("Open Existing Case"), id="menu_open"),
                ListItem(Label("Settings"), id="menu_settings"),
                ListItem(Label("Help"), id="menu_help"),
                ListItem(Label("Exit"), id="menu_exit"),
                id="main_menu",
            )
            yield Footer()

        def on_mount(self) -> None:
            menu = self.query_one("#main_menu", ListView)
            menu.index = 0
            menu.focus()

        @on(ListView.Selected, "#main_menu")
        def handle_select(self, event: ListView.Selected) -> None:
            action = event.item.id
            if action == "menu_create":
                self.app.push_screen(CreateCaseScreen())
            elif action == "menu_open":
                self.app.push_screen(OpenCaseScreen())
            elif action == "menu_settings":
                self.app.push_screen(SettingsScreen())
            elif action == "menu_help":
                self.app.push_screen(HelpScreen())
            elif action == "menu_exit":
                self.app.exit()

    class CreateCaseScreen(Screen):
        BINDINGS = [("escape", "pop_screen", "Back")]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Label("Create New Case")
            yield Input(placeholder="Case name", id="case_name")
            yield Input(placeholder="Source path (directory with XML)", id="source_path")
            yield Input(placeholder="Description (optional)", id="description")
            yield Input(placeholder="Analyst (optional)", id="analyst")
            yield Static("Storage path: default from configuration", id="storage_hint")
            yield Label("", id="status")
            yield Horizontal(Button("Create & Index", id="create_btn"), Button("Back", id="back_btn"))
            yield Footer()

        @on(Button.Pressed, "#back_btn")
        def back(self) -> None:
            self.app.pop_screen()

        @on(Button.Pressed, "#create_btn")
        def create_case(self) -> None:
            case_name = self.query_one("#case_name", Input).value.strip()
            source_path = self.query_one("#source_path", Input).value.strip()
            description = self.query_one("#description", Input).value.strip()
            analyst = self.query_one("#analyst", Input).value.strip()
            status = self.query_one("#status", Label)

            if not case_name:
                status.update("Case name is required.")
                return
            if not source_path:
                status.update("Source path is required.")
                return
            src = Path(source_path)
            if not src.exists() or not src.is_dir():
                status.update("Invalid source path.")
                return
            xml_files = self.app.discovery.discover(src)
            if not xml_files:
                status.update("No XML files found in source path.")
                return

            case = self.app.case_service.create_case(case_name, src, analyst=analyst, description=description)
            self.app.push_screen(IndexingScreen(case))

    class OpenCaseScreen(Screen):
        BINDINGS = [("escape", "pop_screen", "Back")]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Label("Open Existing Case")
            yield ListView(id="cases_list")
            yield Static("Select a case to see summary.", id="summary")
            yield Horizontal(Button("Open", id="open_btn"), Button("Back", id="back_btn"))
            yield Footer()

        def on_mount(self) -> None:
            self._cases = self.app.case_repo.list_all()
            lv = self.query_one("#cases_list", ListView)
            if not self._cases:
                lv.append(ListItem(Label("No cases found"), disabled=True))
                return
            for case in self._cases:
                lv.append(ListItem(Label(case.name), id=case.id))
            lv.index = 0
            lv.focus()
            self._render_summary(self._cases[0])

        @on(ListView.Highlighted, "#cases_list")
        def on_highlight(self, event: ListView.Highlighted) -> None:
            if not getattr(event.item, "id", None):
                return
            selected = next((c for c in self._cases if c.id == event.item.id), None)
            if selected:
                self._render_summary(selected)

        def _render_summary(self, case: CaseModel) -> None:
            self.query_one("#summary", Static).update(
                f"Name: {case.name}\nSource: {case.source_path}\nCreated: {case.created_at}\nUpdated: {case.updated_at}\nArtifacts: {case.artifact_counts}"
            )

        @on(ListView.Selected, "#cases_list")
        def open_case_enter(self, event: ListView.Selected) -> None:
            case = next((c for c in self._cases if c.id == getattr(event.item, "id", None)), None)
            if case:
                self.app.push_screen(WorkspaceScreen(case))

        @on(Button.Pressed, "#back_btn")
        def back(self) -> None:
            self.app.pop_screen()

        @on(Button.Pressed, "#open_btn")
        def open_case(self) -> None:
            lv = self.query_one("#cases_list", ListView)
            if lv.index is None or not self._cases:
                return
            item = lv.children[lv.index]
            case = next((c for c in self._cases if c.id == getattr(item, "id", None)), None)
            if case:
                self.app.push_screen(WorkspaceScreen(case))

    class HelpScreen(Screen):
        BINDINGS = [("escape", "pop_screen", "Back")]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static(
                "Keyboard:\n"
                "- Main menu/tree: Arrow keys + Enter\n"
                "- Focus cycle: Tab / Shift+Tab\n"
                "- Back: Esc\n"
                "- Quit app: Ctrl+C or Exit menu\n"
                "Commands: help, search <text>, filter <field> <contains|=|!=> <value>, sort <field> <asc|desc>, stats, clear"
            )
            yield Footer()

    class SettingsScreen(Screen):
        BINDINGS = [("escape", "pop_screen", "Back")]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static("Settings (Phase 1): no editable settings yet.")
            yield Footer()

    class IndexingScreen(Screen):
        BINDINGS = [("escape", "noop", "Indexing in progress")]

        def __init__(self, case: CaseModel) -> None:
            super().__init__()
            self.case = case

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Label(f"Indexing case: {self.case.name}")
            yield Label("Starting indexing...", id="index_status")
            yield RichLog(id="index_log", wrap=True)
            yield Footer()

        def on_mount(self) -> None:
            self.run_worker(self._run_indexing(), exclusive=True)

        async def _run_indexing(self):
            status = self.query_one("#index_status", Label)
            log = self.query_one("#index_log", RichLog)

            def cb(done: int, total: int, message: str) -> None:
                status.update(f"Indexing: {done}/{total}")
                log.write(message)

            try:
                cb(0, 0, "Indexing started")
                case = self.app.indexer.index_case(self.case, progress_callback=cb)
                cb(case.indexed_files_count, case.indexed_files_count, "Indexing completed")
                self.app.call_after_refresh(lambda: self.app.switch_screen(WorkspaceScreen(case)))
            except Exception as exc:  # pragma: no cover
                status.update("Indexing failed")
                log.write(f"Error: {exc}")

    class WorkspaceScreen(Screen):
        BINDINGS = [
            ("escape", "pop_screen", "Back"),
            ("tab", "focus_next", "Next Focus"),
            ("shift+tab", "focus_previous", "Prev Focus"),
        ]

        def __init__(self, case: CaseModel) -> None:
            super().__init__()
            self.case = case
            self.parser = CommandParser()
            self.dispatcher = CommandDispatcher()
            self.current_rows: list[dict] = []
            self.current_columns: list[str] = []
            self.current_artifact_type: str | None = None

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Label(f"Workspace - {self.case.name}")
            with Horizontal(id="workspace"):
                with Vertical(id="nav"):
                    yield Label("Case")
                    yield ListView(
                        ListItem(Label("Overview"), id="node_overview"),
                        ListItem(Label("Artifacts"), id="node_artifacts"),
                        ListItem(Label("Timeline"), id="node_timeline"),
                        ListItem(Label("Findings"), id="node_findings"),
                        ListItem(Label("Case Metadata"), id="node_meta"),
                        id="tree",
                    )
                with Vertical(id="analysis"):
                    table = DataTable(id="results")
                    table.cursor_type = "row"
                    yield table
                    yield Label("Ready.", id="status")
            with Vertical(id="cli"):
                yield RichLog(id="log", wrap=True, highlight=True)
                yield Input(placeholder="ArtifactForge CLI >", id="cli_input")
            yield Footer()

        def on_mount(self) -> None:
            self.app.apply_workspace_css(self)
            tree = self.query_one("#tree", ListView)
            tree.index = 0
            tree.focus()
            self._render_overview()
            for at in self.app.workspace_data.artifact_types(self.case.id):
                tree.append(ListItem(Label(f"- {at}"), id=f"artifact::{at}"))

        @on(ListView.Selected, "#tree")
        def on_tree_selected(self, event: ListView.Selected) -> None:
            node_id = event.item.id or ""
            if node_id == "node_overview":
                self._render_overview()
            elif node_id == "node_timeline":
                self._render_timeline()
            elif node_id == "node_findings":
                self._render_findings()
            elif node_id == "node_meta":
                self._render_metadata()
            elif node_id.startswith("artifact::"):
                self.current_artifact_type = node_id.split("::", 1)[1]
                self._render_artifacts(self.current_artifact_type)
            elif node_id == "node_artifacts":
                self.current_artifact_type = None
                self._render_artifacts(None)

        @on(Input.Submitted, "#cli_input")
        def on_cli(self, event: Input.Submitted) -> None:
            raw = event.value.strip()
            if not raw:
                return
            parsed = self.parser.parse(raw)
            output = self._execute_workspace_command(parsed.command, parsed.args)
            self.query_one("#log", RichLog).write(f"> {raw}\n{output}")
            event.input.value = ""

        def _render_table(self, rows: list[dict]) -> None:
            table = self.query_one("#results", DataTable)
            table.clear(columns=True)
            if not rows:
                table.add_columns("Info")
                table.add_row("No data")
                self.current_rows = []
                self.current_columns = ["Info"]
                return
            columns = sorted({k for row in rows for k in row.keys()})
            table.add_columns(*columns)
            for row in rows:
                table.add_row(*[str(row.get(c, "")) for c in columns])
            self.current_rows = rows
            self.current_columns = columns

        def _render_overview(self) -> None:
            rows = [{"field": k, "value": v} for k, v in self.app.workspace_data.overview_rows(self.case)]
            self._render_table(rows)
            self.query_one("#status", Label).update("Overview loaded")

        def _render_artifacts(self, artifact_type: str | None) -> None:
            rows = self.app.workspace_data.artifact_rows(self.case.id, artifact_type=artifact_type)
            self._render_table(rows)
            self.query_one("#status", Label).update(f"Artifacts loaded: {artifact_type or 'all'}")

        def _render_timeline(self) -> None:
            rows = self.app.workspace_data.timeline_rows(self.case.id)
            self._render_table(rows)
            self.query_one("#status", Label).update("Timeline loaded")

        def _render_findings(self) -> None:
            rows = self.app.workspace_data.findings_rows(self.case.id)
            self._render_table(rows)
            self.query_one("#status", Label).update("Findings loaded")

        def _render_metadata(self) -> None:
            rows = [{"field": k, "value": str(v)} for k, v in self.case.__dict__.items()]
            self._render_table(rows)
            self.query_one("#status", Label).update("Case metadata loaded")

        def _execute_workspace_command(self, command: str, args: list[str]) -> str:
            if command == "help":
                return "Commands: help, search <text>, filter <field> <contains|=|!=> <value>, sort <field> <asc|desc>, stats, clear"
            if command == "clear":
                self.query_one("#log", RichLog).clear()
                return "Log cleared."
            if command == "stats":
                return f"rows={len(self.current_rows)} columns={len(self.current_columns)} artifact_scope={self.current_artifact_type or 'all'}"
            if command == "search" and args:
                needle = " ".join(args).lower()
                filtered = [r for r in self.current_rows if needle in str(r).lower()]
                self._render_table(filtered)
                return f"Search applied. {len(filtered)} rows matched."
            if command == "filter" and len(args) >= 3:
                field, op = args[0], args[1]
                value = " ".join(args[2:])
                if op == "contains":
                    filtered = [r for r in self.current_rows if value.lower() in str(r.get(field, "")).lower()]
                elif op == "=":
                    filtered = [r for r in self.current_rows if str(r.get(field, "")) == value]
                elif op == "!=":
                    filtered = [r for r in self.current_rows if str(r.get(field, "")) != value]
                else:
                    return "Unsupported operator. Use contains, =, !="
                self._render_table(filtered)
                return f"Filter applied. {len(filtered)} rows matched."
            if command == "sort" and len(args) >= 2:
                field = args[0]
                direction = args[1].lower()
                reverse = direction == "desc"
                sorted_rows = sorted(self.current_rows, key=lambda r: str(r.get(field, "")), reverse=reverse)
                self._render_table(sorted_rows)
                return f"Sorted by {field} {direction}."
            return self.dispatcher.execute(self.parser.parse(" ".join([command, *args]).strip()))

    class ArtifactForgeApp(App):
        CSS = """
        Screen { layout: vertical; }
        #workspace { height: 1fr; }
        #nav { width: 28%; border: round #666666; }
        #analysis { width: 72%; border: round #666666; }
        #cli { height: 8; border: round #666666; }
        """

        def __init__(
            self,
            case_service: CaseService,
            case_repo: CaseRepository,
            artifact_repo: ArtifactRepository,
            timeline_repo: TimelineRepository,
            findings_repo: FindingsRepository,
            indexer: IndexingService,
            discovery: XMLDiscovery,
        ) -> None:
            super().__init__()
            self.case_service = case_service
            self.case_repo = case_repo
            self.indexer = indexer
            self.discovery = discovery
            self.workspace_data = WorkspaceDataService(artifact_repo, timeline_repo, findings_repo)

        def on_mount(self) -> None:
            self.push_screen(SplashScreen())

        def apply_workspace_css(self, _screen: WorkspaceScreen) -> None:
            return
