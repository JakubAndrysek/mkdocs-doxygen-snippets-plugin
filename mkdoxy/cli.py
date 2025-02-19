#!/usr/bin/env python
from pathlib import Path
import click
from mkdoxy.migration import update_new_config


@click.group()
def main():
    """mkdoxy - Command line tool for managing Doxygen configuration migration."""
    pass


@click.command()
@click.argument("yaml_file", type=click.Path(exists=True))
@click.option("--no-backup", is_flag=True, help="Do not backup old config to mkdocs.1_old.yaml")
def migrate(yaml_file, no_backup):
    """
    Migrate mkdoxy configuration to a new version.

    :param yaml_file: Path to the mkdocs.yaml file.
    :param no_backup: Do not backup the old config to mkdocs.1_old.yaml.
    """
    backup_file_name = "mkdocs.1_old.yaml"
    update_new_config(Path(yaml_file), not no_backup, backup_file_name)
    click.echo("Migration completed successfully")
    if not no_backup:
        click.echo(f"Old config was backed up as '{backup_file_name}'")


@click.command()
def version():
    """
    Display the version of the mkdoxy package.
    """
    try:
        import importlib.metadata

        package_version = importlib.metadata.version("mkdoxy")
    except Exception:
        package_version = "Unknown"
    click.echo("MkDoxy: https://github.com/JakubAndrysek/MkDoxy")
    click.echo(f"Version: {package_version}")


main.add_command(migrate)
main.add_command(version)

if __name__ == "__main__":
    main()
