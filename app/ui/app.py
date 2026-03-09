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
    from textual import events, on
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.screen import Screen
    from textual.widgets import Button, DataTable, Footer, Input, Label, ListItem, ListView, OptionList, RichLog, Static
    from textual.widgets.option_list import Option
except Exception:  # pragma: no cover
    class ArtifactForgeApp:  # type: ignore[override]
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def run(self) -> None:
            print("Textual is not available in this environment.")
else:
    class SplashScreen(Screen):
        def compose(self) -> ComposeResult:
            yield Static(SPLASH_BANNER)
            yield Label("Loading ArtifactForge...")

        def on_mount(self) -> None:
            self.set_timer(0.6, lambda: self.app.switch_screen(MainMenuScreen()))

    class MainMenuScreen(Screen):
        BINDINGS = [
            ("up", "menu_up", "Up"),
            ("down", "menu_down", "Down"),
            ("enter", "menu_open", "Open"),
            ("escape", "app.exit", "Exit"),
        ]

        MENU_ITEMS = [
            ("menu_create", "Create New Case"),
            ("menu_open", "Open Existing Case"),
            ("menu_settings", "Settings"),
            ("menu_help", "Help"),
            ("menu_exit", "Exit"),
        ]

        def compose(self) -> ComposeResult:
            yield Static(SPLASH_BANNER)
            yield Static(COMPACT)
            yield Label("Main Menu (↑/↓ + Enter)", id="menu_hint")
            yield OptionList(*[Option(label, id=item_id) for item_id, label in self.MENU_ITEMS], id="main_menu")
            yield Footer()

        def on_mount(self) -> None:
            menu = self.query_one("#main_menu", OptionList)
            if menu.highlighted is None:
                menu.highlighted = 0
            menu.focus()

        def _open_selected(self) -> None:
            menu = self.query_one("#main_menu", OptionList)
            highlighted = menu.highlighted
            if highlighted is None:
                return
            action = menu.get_option_at_index(highlighted).id
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

        @on(OptionList.OptionSelected, "#main_menu")
        def on_selected(self) -> None:
            self._open_selected()

        def action_menu_up(self) -> None:
            self.query_one("#main_menu", OptionList).action_cursor_up()

        def action_menu_down(self) -> None:
            self.query_one("#main_menu", OptionList).action_cursor_down()

        def action_menu_open(self) -> None:
            self._open_selected()


        @on(events.Key)
        def on_main_menu_key(self, event: events.Key) -> None:
            menu = self.query_one("#main_menu", OptionList)
            if self.focused is not menu:
                return
            if event.key == "up":
                self.action_menu_up()
                event.stop()
            elif event.key == "down":
                self.action_menu_down()
                event.stop()
            elif event.key == "enter":
                self.action_menu_open()
                event.stop()

    class CreateCaseScreen(Screen):
        BINDINGS = [
            ("escape", "app.pop_screen", "Back"),
            ("f5", "submit", "Create & Index"),
        ]

        def compose(self) -> ComposeResult:
            yield Label("Create New Case", id="title")
            yield Input(placeholder="Case name", id="case_name")
            yield Input(placeholder="Source path (directory with XML)", id="source_path")
            yield Input(placeholder="Description (optional)", id="description")
            yield Input(placeholder="Analyst (optional)", id="analyst")
            yield Label("Use Tab/Shift+Tab to move between fields. Press F5 to submit.", id="form_help")
            yield Label("", id="status")
            yield Horizontal(Button("Create & Index", id="create_btn", variant="success"), Button("Back", id="back_btn"))
            yield Footer()

        def on_mount(self) -> None:
            self.query_one("#case_name", Input).focus()

        @on(Input.Submitted)
        def on_input_submitted(self, event: Input.Submitted) -> None:
            order = ["case_name", "source_path", "description", "analyst"]
            current = event.input.id or ""
            if current == order[-1]:
                self._submit_form()
                return
            if current in order:
                next_id = order[order.index(current) + 1]
                self.query_one(f"#{next_id}", Input).focus()

        @on(Button.Pressed, "#back_btn")
        def back(self) -> None:
            self.app.pop_screen()

        @on(Button.Pressed, "#create_btn")
        def create_case(self) -> None:
            self._submit_form()

        def action_submit(self) -> None:
            self._submit_form()

        def _submit_form(self) -> None:
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

            status.update(f"Indexing will start. XML detected: {len(xml_files)}")
            case = self.app.case_service.create_case(case_name, src, analyst=analyst, description=description)
            self.app.switch_screen(IndexingScreen(case))

    class OpenCaseScreen(Screen):
        BINDINGS = [
            ("up", "list_up", "Up"),
            ("down", "list_down", "Down"),
            ("enter", "open_selected", "Open"),
            ("escape", "app.pop_screen", "Back"),
        ]

        def compose(self) -> ComposeResult:
            yield Label("Open Existing Case")
            yield OptionList(id="cases_list")
            yield Static("Select a case with arrows and press Enter.", id="summary")
            yield Horizontal(Button("Open", id="open_btn", variant="success"), Button("Back", id="back_btn"))
            yield Footer()

        def on_mount(self) -> None:
            self._cases = self.app.case_repo.list_all()
            lv = self.query_one("#cases_list", OptionList)
            if not self._cases:
                self.query_one("#summary", Static).update("No cases found.")
                return
            for case in self._cases:
                lv.add_option(Option(case.name, id=case.id))
            if lv.highlighted is None:
                lv.highlighted = 0
            lv.focus()
            self._render_summary(self._cases[0])

        def _current_case(self) -> CaseModel | None:
            lv = self.query_one("#cases_list", OptionList)
            highlighted = lv.highlighted
            if highlighted is None or not self._cases:
                return None
            selected_id = lv.get_option_at_index(highlighted).id
            return next((c for c in self._cases if c.id == selected_id), None)

        def _render_summary(self, case: CaseModel) -> None:
            self.query_one("#summary", Static).update(
                f"Name: {case.name}\nSource: {case.source_path}\nCreated: {case.created_at}\nUpdated: {case.updated_at}\nArtifacts: {case.artifact_counts}"
            )

        def action_list_up(self) -> None:
            if not self._cases:
                return
            self.query_one("#cases_list", OptionList).action_cursor_up()
            case = self._current_case()
            if case:
                self._render_summary(case)

        def action_list_down(self) -> None:
            if not self._cases:
                return
            self.query_one("#cases_list", OptionList).action_cursor_down()
            case = self._current_case()
            if case:
                self._render_summary(case)

        def action_open_selected(self) -> None:
            case = self._current_case()
            if case:
                self.app.switch_screen(WorkspaceScreen(case))


        @on(events.Key)
        def on_cases_key(self, event: events.Key) -> None:
            lv = self.query_one("#cases_list", OptionList)
            if self.focused is not lv:
                return
            if event.key == "up":
                self.action_list_up()
                event.stop()
            elif event.key == "down":
                self.action_list_down()
                event.stop()
            elif event.key == "enter":
                self.action_open_selected()
                event.stop()

        @on(OptionList.OptionHighlighted, "#cases_list")
        def list_highlighted(self) -> None:
            case = self._current_case()
            if case:
                self._render_summary(case)

        @on(OptionList.OptionSelected, "#cases_list")
        def list_selected(self) -> None:
            self.action_open_selected()

        @on(Button.Pressed, "#open_btn")
        def open_button(self) -> None:
            self.action_open_selected()

        @on(Button.Pressed, "#back_btn")
        def back_button(self) -> None:
            self.app.pop_screen()

    class HelpScreen(Screen):
        BINDINGS = [("escape", "app.pop_screen", "Back")]

        def compose(self) -> ComposeResult:
            yield Static(
                "Keyboard Navigation\n"
                "- Main menu / case list: Up / Down\n"
                "- Activate selection: Enter\n"
                "- Switch focus in workspace: Tab / Shift+Tab\n"
                "- Back to previous screen: Esc\n"
                "- Create case submit shortcut: F5\n"
            )
            yield Footer()

    class SettingsScreen(Screen):
        BINDINGS = [("escape", "app.pop_screen", "Back")]

        def compose(self) -> ComposeResult:
            yield Static("Settings (Phase 1): no editable settings yet.")
            yield Footer()

    class IndexingScreen(Screen):
        BINDINGS = [("escape", "noop", "Indexing running")]

        def __init__(self, case: CaseModel) -> None:
            super().__init__()
            self.case = case

        def compose(self) -> ComposeResult:
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
                status.update(f"Indexing: {done}/{total}" if total else "Indexing started")
                log.write(message)

            try:
                case = self.app.indexer.index_case(self.case, progress_callback=cb)
                log.write("Case created successfully. Indexing completed.")
                self.app.call_after_refresh(lambda: self.app.switch_screen(WorkspaceScreen(case)))
            except Exception as exc:  # pragma: no cover
                status.update("Indexing failed")
                log.write(f"Error: {exc}")

    class WorkspaceScreen(Screen):
        BINDINGS = [
            ("escape", "app.pop_screen", "Back"),
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
            yield Label(f"Case: {self.case.name}", id="workspace_title")
            with Horizontal(id="workspace"):
                with Vertical(id="nav"):
                    yield Label("Navigation")
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
            tree = self.query_one("#tree", ListView)
            tree.index = 0
            tree.focus()
            self._render_overview()
            for at in self.app.workspace_data.artifact_types(self.case.id):
                tree.append(ListItem(Label(f"- {at}"), id=f"artifact::{at}"))

        @on(ListView.Highlighted, "#tree")
        def on_tree_highlighted(self, event: ListView.Highlighted) -> None:
            self._open_node(event.item.id or "")

        @on(ListView.Selected, "#tree")
        def on_tree_selected(self, event: ListView.Selected) -> None:
            self._open_node(event.item.id or "")

        def _open_node(self, node_id: str) -> None:
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
        #workspace_title { padding: 0 1; background: #303030; }
        #workspace { height: 1fr; }
        #nav { width: 28%; border: round #666666; }
        #analysis { width: 72%; border: round #666666; }
        #cli { height: 8; border: round #666666; }
        #main_menu { border: round #666666; margin: 1 2; }
        #menu_hint { padding: 0 2; }
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
