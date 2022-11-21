import argparse

import pytest

from cotainr.cli import CotainrCLI, Info


class TestExecute:
    def test_not_implemented_message(self, capsys):
        Info().execute()
        stdout = capsys.readouterr().out
        assert (
            stdout.strip()
            == "Sorry, no information about your system is available at this time."
        )


class TestAddArguments:
    def test_no_arguments_added(self):
        parser = argparse.ArgumentParser()
        Info.add_arguments(parser=parser)
        args = parser.parse_args(args=[])
        assert not vars(args)


class TestHelpMessage:
    def test_CLI_subcommand_help_message(self, argparse_options_line, capsys):
        with pytest.raises(SystemExit):
            CotainrCLI(args=["info", "--help"])
        stdout = capsys.readouterr().out
        assert stdout == (
            # Capsys apparently assumes an 80 char terminal (?) - thus extra '\n'
            "usage: cotainr info [-h]\n\n"
            "Obtain info about the state of all required dependencies for building a\n"
            "container.\n\n"
            f"{argparse_options_line}"
            "  -h, --help  show this help message and exit\n"
        )
