import hashlib
import logging
import os
import re
import shutil
from pathlib import Path
from subprocess import PIPE, Popen

from mkdocs import exceptions

from mkdoxy.doxy_config import MkDoxyConfig, MkDoxyConfigProject

log: logging.Logger = logging.getLogger("mkdocs")


class DoxygenGenerator:
    """! Class for running Doxygen.
    @details This class is used to run Doxygen and parse the XML output.
    """

    def __init__(
        self,
        doxy_config: MkDoxyConfig,
        project_config: MkDoxyConfigProject,
        temp_doxy_folder: Path,
    ):
        """! Constructor.
        @details
        @param doxy_config: (MkDoxyConfig) Doxygen configuration.
        @param project_config: (MkDoxyConfigProject) Project configuration.
        @param temp_doxy_folder: (Path) Temporary Doxygen folder.
        """
        self.doxy_config = doxy_config
        self.project_config = project_config
        self.temp_doxy_folder = temp_doxy_folder

        if not self.is_doxygen_valid_path(doxy_config.doxygen_bin_path):
            raise DoxygenBinPathNotValid(
                f"Invalid Doxygen binary path: {doxy_config.doxygen_bin_path}\n"
                f"Make sure Doxygen is installed and the path is correct.\n"
                f"Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/#configure-custom-doxygen-binary."
            )

    @staticmethod
    def get_doxy_format_config() -> dict:
        """
        @brief Get the default Doxygen format configuration.
        @details Default Doxygen configuration options:
        @details - GENERATE_XML: YES
        @details - GENERATE_HTML: NO
        @details - GENERATE_LATEX: NO
        """
        return {
            "GENERATE_XML": True,
            "GENERATE_HTML": False,
            "GENERATE_LATEX": False,
        }

    @staticmethod
    def get_doxy_default_config() -> dict:
        """
        @brief Get the default Doxygen configuration.
        @details Default Doxygen configuration options:
        @details - DOXYFILE_ENCODING: UTF-8
        @details - RECURSIVE: YES
        @details - EXAMPLE_PATH: examples
        @details - SHOW_NAMESPACES: YES
        """
        return {
            "DOXYFILE_ENCODING": "UTF-8",
            "RECURSIVE": True,
            "EXAMPLE_PATH": "examples",
            "SHOW_NAMESPACES": True,
        }

    def get_doxy_diagrams_config(self) -> dict:
        """
        @brief Get the Doxygen diagrams configuration.
        @details Doxygen diagrams configuration options:
        @details - HAVE_DOT: YES
        @details - DOT_IMAGE_FORMATS: <generate_diagrams_format>
        @details - UML_LOOK: YES if <generate_diagrams_type> is "uml", NO otherwise
        @details - DOT_CLEANUP: NO
        @details - GENERATE_LEGEND: NO
        @details - SEARCHENGINE: NO
        @details - GENERATE_HTML: YES (required for diagrams)
        """
        return {
            "HAVE_DOT": True,
            "DOT_IMAGE_FORMATS": self.doxy_config.generate_diagrams_format,
            "UML_LOOK": self.doxy_config.generate_diagrams_type == "uml",
            "DOT_CLEANUP": False,
            "GENERATE_LEGEND": False,
            "SEARCHENGINE": False,
            "GENERATE_HTML": True,
        }

        # have to be tested
        # doxy_config["CLASS_DIAGRAMS"] = "YES"
        # doxy_config["COLLABORATION_GRAPH"] = "YES"
        # doxy_config["INCLUDE_GRAPH"] = "YES"
        # doxy_config["GRAPHICAL_HIERARCHY"] = "YES"
        # doxy_config["CALL_GRAPH"] = "YES"
        # doxy_config["CALLER_GRAPH"] = "YES"

    def get_doxy_config_file(self):
        """! Get the Doxygen configuration from the provided file.
        @details
        @return: (dict) Doxygen configuration from the provided file.
        """
        return self.str2dox_dict(self.get_doxy_config_file_raw(), self.project_config.doxy_config_file)

    def get_doxy_config_file_raw(self):
        """! Get the Doxygen configuration from the provided file.
        @details
        @return: (str) Doxygen configuration from the provided file.
        """
        try:
            with open(self.project_config.doxy_config_file, "r") as file:
                return file.read()
        except FileNotFoundError as e:
            raise DoxygenCustomConfigNotFound(
                f"Custom Doxygen config file not found\n"
                f"Make sure the path is correct."
                f"Loaded path: '{self.project_config.doxy_config_file}'\n"
                f"Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/#configure-custom-doxygen-configuration-file.\n"
            ) from e

    def get_merged_doxy_dict(self) -> dict:
        """! Get the merged Doxygen configuration.
        @details The merged Doxygen configuration is created by merging multiple configurations.
        @details The hierarchy is as follows:
        @details - If a Doxygen config file is provided, it is used.
        @details - If not, the default Doxygen configuration is used.
        @details - Merge the INPUT directories from the mkdocs.yml file with the Doxygen configuration.
        @details - Add the OUTPUT_DIRECTORY to the temporary Doxygen folder.
        @details - Update configuration with the project format configuration.
        @details - Update configuration with the default configuration.
        @details - Update configuration with the project configuration.
        @details - Update configuration with the diagrams configuration if enabled.
        @return: (dict) Merged Doxygen configuration.
        """
        doxy_dict = {}

        # Update with Doxygen config file if provided
        if self.project_config.doxy_config_file:
            doxy_dict.update(self.get_doxy_config_file())
        else:
            doxy_dict.update(self.get_doxy_default_config())

        # Merge INPUT directories from the mkdocs.yml file with the Doxygen configuration
        doxy_dict["INPUT"] = self.merge_doxygen_input(
            self.project_config.src_dirs, doxy_dict.get("INPUT", ""), self.get_doxygen_run_folder()
        )

        # OUTPUT_DIRECTORY is always the temporary Doxygen folder
        doxy_dict["OUTPUT_DIRECTORY"] = str(self.temp_doxy_folder)

        # Update with the project format configuration
        doxy_dict.update(self.get_doxy_format_config())

        # Update with the default configuration
        doxy_dict.update(self.doxy_config.doxy_config_dict)

        # Update with the project configuration
        doxy_dict.update(self.project_config.doxy_config_dict)

        if self.doxy_config.generate_diagrams:
            doxy_dict.update(self.get_doxy_diagrams_config())

        if doxy_dict["INPUT"] == "":
            raise exceptions.PluginError(
                "No INPUT directories provided for Doxygen.\n"
                "Make sure to provide at least one source directory."
                "Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/#configure-custom-doxygen-configuration-file."
            )

        log.debug(f"- Doxygen INPUT: {doxy_dict['INPUT']}")

        return doxy_dict

    @staticmethod
    def merge_doxygen_input(src_dirs: str, doxy_input: str, doxygen_run_folder: Path) -> str:
        """! Merge the INPUT directories from the mkdocs.yml file with the Doxygen configuration.

        @details Both `src_dirs` and `doxy_input` should be space-separated strings.
        Each path is resolved relative to `doxygen_run_folder`.
        The function returns a space-separated string of unique relative paths.

        @param src_dirs: (str) Source directories from the mkdocs.yml file.
        @param doxy_input: (str) Doxygen INPUT directories.
        @param doxygen_run_folder: (Path) The folder to execute
        @return: (str) Merged INPUT directories.
        """
        # If either input is empty, return the other.
        if not src_dirs:
            return doxy_input
        if not doxy_input:
            return src_dirs

        base_dir = doxygen_run_folder.resolve()

        abs_paths = {(base_dir / path_str).resolve() for path_str in src_dirs.split()}
        for path_str in doxy_input.split():
            abs_paths.add((base_dir / path_str).resolve())

        # Convert absolute paths back to relative ones and sort for consistency
        relative_paths = sorted(os.path.relpath(p, base_dir) for p in abs_paths)

        return " ".join(relative_paths)

    @staticmethod
    def is_doxygen_valid_path(doxygen_bin_path: Path) -> bool:
        """! Check if the Doxygen binary path is valid.
        @details Accepts a full path or just 'doxygen' if it exists in the system's PATH.
        @param doxygen_bin_path: (str) The path to the Doxygen binary or just 'doxygen'.
        @return: (bool) True if the Doxygen binary path is valid, False otherwise.
        """
        # If the path is just 'doxygen', search for it in the system's PATH
        if str(doxygen_bin_path) == "doxygen":
            return shutil.which("doxygen") is not None

        # Use pathlib to check if the provided full path is a file and executable
        return doxygen_bin_path.is_file() and os.access(doxygen_bin_path, os.X_OK)

    # Source of dox_dict2str: https://xdress-fabio.readthedocs.io/en/latest/_modules/xdress/doxygen.html#XDressPlugin

    @staticmethod
    def str2dox_dict(dox_str: str, config_file: str = "???") -> dict:
        """! Convert a string from a doxygen config file to a dictionary.
        @details
        @param dox_str: (str) String from a doxygen config file.
        @return: (dict) Dictionary.
        """
        dox_dict = {}
        dox_str = re.sub(r"\\\s*\n\s*", "", dox_str)
        pattern = r"^\s*([^=\s]+)\s*(=|\+=)\s*(.*)$"

        try:
            for line in dox_str.split("\n"):
                if line.strip() == "" or line.startswith("#"):
                    continue
                match = re.match(pattern, line)
                if not match:
                    raise DoxygenCustomConfigNotValid(
                        f"Invalid line: '{line}'"
                        f"In custom Doxygen config file: {config_file}\n"
                        f"Make sure the file is in standard Doxygen format."
                        f"Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/."
                    )
                key, operator, value = match.groups()
                value = value.strip()
                if operator == "=":
                    if value == "YES":
                        dox_dict[key] = True
                    elif value == "NO":
                        dox_dict[key] = False
                    else:
                        dox_dict[key] = value
                if operator == "+=":
                    dox_dict[key] = f"{dox_dict[key]} {value}"
        except ValueError as e:
            raise DoxygenCustomConfigNotValid(
                f"Invalid custom Doxygen config file: {config_file}\n"
                f"Make sure the file is in standard Doxygen format."
                f"Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/."
            ) from e
        return dox_dict

    @staticmethod
    def dox_dict2str(dox_dict: dict) -> str:
        """! Convert a dictionary to a string that can be written to a doxygen config file.
        @details
        @param dox_dict: (dict) Dictionary to convert.
        @return: (str) String that can be written to a doxygen config file.
        """
        string = ""
        new_line = "{option} = {value}\n"
        items = sorted(dox_dict.items())
        for key, value in items:
            if value is True:
                value_transformed = "YES"
            elif value is False:
                value_transformed = "NO"
            else:
                value_transformed = value

            string += new_line.format(option=key.upper(), value=value_transformed)

        # Don't need an empty line at the end
        return string.strip()

    @staticmethod
    def hash_write(file_name: Path, hash_key: str):
        """! Write the hash to the file.
        @details
        @param file_name: (Path) Path to the file where the hash will be saved.
        @param hash_key: (str) Hash.
        """
        with open(file_name, "w") as hash_file:
            hash_file.write(hash_key)

    @staticmethod
    def hash_read(file_name: Path) -> str:
        """! Read the hash from the file.
        @details
        @param file_name: (Path) Path to the file with the hash.
        @return: (str) Hash.
        """
        with open(file_name, "r") as hash_file:
            return str(hash_file.read())

    def has_changes(self) -> bool:
        """! Check if the source files have changed since the last run.
        @details
        @return: (bool) True if the source files have changed since the last run.
        """
        sha1 = hashlib.sha1()
        sources = self.project_config.src_dirs.split(" ")
        # Code from https://stackoverflow.com/a/22058673/15411117
        BUF_SIZE = 65536  # let's read stuff in 64kb chunks!
        for source in sources:
            for path in Path(source).rglob("*.*"):
                if path.is_file():
                    with open(path, "rb") as file:
                        while True:
                            data = file.read(BUF_SIZE)
                            if not data:
                                break
                            sha1.update(data)

        hash_new = sha1.hexdigest()
        hash_file_name: Path = Path("mkdoxy_hash.txt")
        hash_file_path = Path.joinpath(self.temp_doxy_folder, hash_file_name)
        if hash_file_path.is_file():
            hash_old = self.hash_read(hash_file_path)
            if hash_new == hash_old:
                return False  # No changes in the source files

        self.hash_write(hash_file_path, hash_new)
        return True

    def run(self) -> None:
        """! Run Doxygen with the current configuration using the Popen class.
        @details
        """
        doxy_builder = Popen(
            [self.doxy_config.doxygen_bin_path, "-"],
            stdout=PIPE,
            stdin=PIPE,
            stderr=PIPE,
        )

        if self.project_config.doxy_config_file_force:
            doxy_str = self.get_doxy_config_file_raw()
        else:
            doxy_str = self.dox_dict2str(self.get_merged_doxy_dict())
        stdout_data, stderr_data = doxy_builder.communicate(input=doxy_str.encode("utf-8"))
        if doxy_builder.returncode != 0:
            error_message = (
                f"Error running Doxygen (exit code {doxy_builder.returncode}): {stderr_data.decode('utf-8')}"
            )
            raise exceptions.PluginError(error_message)

    def get_output_xml_folder(self) -> Path:
        """! Get the path to the XML output folder.
        @details
        @return: (Path) Path to the XML output folder.
        """
        return Path.joinpath(self.temp_doxy_folder, Path("xml"))

    def get_output_html_folder(self) -> Path:
        """! Get the path to the HTML output folder.
        @details
        @return: (Path) Path to the HTML output folder.
        """
        return Path.joinpath(self.temp_doxy_folder, Path("html"))

    def get_doxygen_run_folder(self):
        """! Get the working directory to execute Doxygen in. Important to resolve relative paths.
        @details When a doxygen config file is provided, this is its containing directory. Otherwise, it's the current
          working directory.
        @return: (Path) Path to the folder to execute Doxygen in.
        """
        if not self.project_config.doxy_config_file:
            return Path.cwd()

        return Path(self.project_config.doxy_config_file).parent


# not valid path exception
class DoxygenBinPathNotValid(exceptions.PluginError):
    pass


class DoxygenCustomConfigNotFound(exceptions.PluginError):
    pass


class DoxygenCustomConfigNotValid(exceptions.PluginError):
    pass
