from click.testing import CliRunner

from etl.cli import main


def test_cli_basic_invocation():
    runner = CliRunner()
    result = runner.invoke(main, ["--source", "csv", "--target", "sqlite"])
    assert result.exit_code == 0
    assert "source=csv" in result.output


def test_cli_dry_run_flag():
    runner = CliRunner()
    result = runner.invoke(
        main, ["--source", "api", "--target", "postgres", "--dry-run"]
    )
    assert result.exit_code == 0
    assert "DRY RUN" in result.output


def test_cli_validate_only_flag():
    runner = CliRunner()
    result = runner.invoke(
        main, ["--source", "csv", "--target", "sqlite", "--validate-only"]
    )
    assert result.exit_code == 0
    assert "VALIDATE ONLY" in result.output


def test_cli_invalid_source_rejected():
    runner = CliRunner()
    result = runner.invoke(main, ["--source", "excel", "--target", "sqlite"])
    assert result.exit_code != 0
