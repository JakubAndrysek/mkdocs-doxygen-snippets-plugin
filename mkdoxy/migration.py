import logging
import re
import shutil
from pathlib import Path

log = logging.getLogger("mkdoxy.migration")


def update_new_config(yaml_file: Path, backup: bool, backup_file_name: str) -> None:
    """
    Migrate MkDoxy configuration to the new version by replacing legacy keys
    directly in the text file—preserving comments and structure.

    Legacy keys are replaced only on non-comment lines.

    :param yaml_file: Path to the mkdocs YAML configuration file.
    :param backup: If True, a backup of the original file is created.
    :param backup_file_name: The filename to use for the backup.
    """
    if backup:
        backup_path = yaml_file.parent / backup_file_name
        shutil.copy2(yaml_file, backup_path)
        log.info(f"Backup created at {backup_path}")

    text = yaml_file.read_text(encoding="utf-8")

    # Merge global and project legacy mappings.
    legacy_mapping = {}
    legacy_mapping.update(
        {
            "full-doc": "full_doc",
            "ignore-errors": "ignore_errors",
            "save-api": "custom_api_folder",
            "doxygen-bin-path": "doxygen_bin_path",
        }
    )
    legacy_mapping.update(
        {
            "src-dirs": "src_dirs",
            "full-doc": "full_doc",
            "ignore-errors": "ignore_errors",
            "doxy-cfg": "doxy_config_dict",
            "doxy-cfg-file": "doxy_config_file",
            "template-dir": "custom_template_dir",
        }
    )

    # Replace each legacy key only on lines that are not comments.
    for old_key, new_key in legacy_mapping.items():
        # Pattern matches lines that do not start with a comment (after optional whitespace),
        # then the legacy key followed by optional spaces and a colon.
        pattern = re.compile(rf"(?m)^(?!\s*#)(\s*){re.escape(old_key)}(\s*:)", re.UNICODE)
        text = pattern.sub(rf"\1{new_key}\2", text)

    yaml_file.write_text(text, encoding="utf-8")
    log.info("Migration completed successfully")
