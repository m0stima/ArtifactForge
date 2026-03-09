from commands.parser import CommandParser


def test_cli_parser_basic():
    parsed = CommandParser().parse('filter name contains "cmd"')
    assert parsed.command == "filter"
    assert parsed.args == ["name", "contains", "cmd"]
