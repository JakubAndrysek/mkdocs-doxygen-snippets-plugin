import shutil
from pathlib import Path
import pytest
from mkdoxy.migration import update_new_config

# Directory containing test data files.
DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(params=["1", "2"])
def migration_files(request, tmp_path: Path) -> tuple:
    """
    Parameterized fixture that copies the legacy YAML file (<prefix>_old.yaml)
    to a temporary file and loads the expected file text from <prefix>_expect.yaml.

    :returns: A tuple (old_yaml_path, expected_text, prefix)
    """
    prefix = request.param
    # Copy legacy file to a temporary file.
    src = DATA_DIR / f"{prefix}_old.yaml"
    dst = tmp_path / f"test_{prefix}.yaml"
    shutil.copy(src, dst)

    # Load expected configuration text (without parsing YAML).
    expected_text = (DATA_DIR / f"{prefix}_expect.yaml").read_text(encoding="utf-8")
    return dst, expected_text, prefix


def test_migration_without_backup(migration_files):
    """
    Test that migration updates the legacy configuration correctly without creating a backup.
    """
    old_yaml, expected_text, prefix = migration_files
    # Run migration with backup turned off.
    update_new_config(old_yaml, backup=False, backup_file_name="backup.yaml")

    updated_text = old_yaml.read_text(encoding="utf-8")
    assert updated_text == expected_text, f"Test case {prefix} failed: output text does not match expected."


def test_migration_with_backup(migration_files):
    """
    Test that migration creates a backup file and updates the configuration correctly.
    """
    old_yaml, expected_text, prefix = migration_files
    backup_file_name = "backup.yaml"

    # Run migration with backup enabled.
    update_new_config(old_yaml, backup=True, backup_file_name=backup_file_name)

    # Verify that the backup file was created.
    backup_file = old_yaml.parent / backup_file_name
    assert backup_file.exists(), f"Test case {prefix}: Backup file was not created."

    updated_text = old_yaml.read_text(encoding="utf-8")
    assert updated_text == expected_text, f"Test case {prefix} failed: output text does not match expected."
