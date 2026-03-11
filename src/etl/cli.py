import click

VALID_ENVS = ["dev", "test", "prod"]
VALID_SOURCES = ["csv", "json", "api", "sqlite"]
VALID_TARGETS = ["sqlite", "postgres"]


@click.command()
@click.option(
    "--source",
    required=True,
    type=click.Choice(VALID_SOURCES),
    help="Input source type.",
)
@click.option(
    "--target",
    required=True,
    type=click.Choice(VALID_TARGETS),
    help="Output target type.",
)
@click.option(
    "--env",
    default="dev",
    show_default=True,
    type=click.Choice(VALID_ENVS),
    help="Runtime environment.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Run pipeline without writing output.",
)
@click.option(
    "--validate-only",
    is_flag=True,
    default=False,
    help="Validate input records only — no transform or load.",
)
@click.option(
    "--config",
    default="config/pipeline.yaml",
    show_default=True,
    type=click.Path(exists=False),
    help="Path to YAML pipeline config.",
)
def main(source, target, env, dry_run, validate_only, config):
    """ETL CLI — Extract, validate, transform, and load data."""
    click.echo(f"[etl] source={source} target={target} env={env}")
    click.echo(f"[etl] dry_run={dry_run} validate_only={validate_only}")
    click.echo(f"[etl] config={config}")

    if dry_run:
        click.echo("[etl] DRY RUN — no data will be written.")

    if validate_only:
        click.echo("[etl] VALIDATE ONLY — pipeline will stop after validation.")


if __name__ == "__main__":
    main()
