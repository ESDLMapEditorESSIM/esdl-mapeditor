"""
Profile management commands.
"""

from pathlib import Path

import click
from flask.cli import AppGroup, with_appcontext

from extensions.profiles import Profiles

profiles_group = AppGroup("profiles", help="Manage profiles.")


@profiles_group.command("upload-profile-csv")
@click.option("--drop-measurement", is_flag=True, help="Drop each InfluxDB measurement before uploading it.")
@click.argument(
    "csv_paths", nargs=-1, type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@with_appcontext
def upload_profile_csv(csv_paths: tuple[Path, ...], drop_measurement: bool) -> None:
    """
    Upload profile CSVs as standard profiles.
    """
    if not csv_paths:
        raise click.ClickException("Provide at least one CSV file.")

    profiles_extension = Profiles.get_instance()
    for csv_path in csv_paths:
        profiles_extension.import_profile_csv(
            csv_path.name,
            csv_path.read_text(encoding="utf-8-sig"),
            emit_update=False,
            drop_measurement=drop_measurement,
        )
        click.echo(f"{csv_path}: uploaded")


@profiles_group.command("regen-panels")
@with_appcontext
def regen_panels() -> None:
    """
    Regenerate panel-service panels for all stored InfluxDB profiles.
    """
    profiles_extension = Profiles.get_instance()
    updated, skipped = profiles_extension.regenerate_profile_panels()
    click.echo(f"Regenerated {updated} panel(s), skipped {skipped} profile(s).")
