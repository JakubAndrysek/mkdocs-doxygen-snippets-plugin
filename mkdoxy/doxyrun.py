import hashlib
import logging
import os
import shutil
import re

from pathlib import Path, PurePath
from subprocess import PIPE, Popen
from typing import Optional

log: logging.Logger = logging.getLogger("mkdocs")


class DoxygenRun:
    """! Class for running Doxygen.
    @details This class is used to run Doxygen and parse the XML output.
    """

    def __init__(
        self,
        doxygenBinPath: str,
        doxygenSource: str,
        tempDoxyFolder: str,
        doxyCfgNew,
        doxyConfigFile: Optional[str] = None,
    ):
        """! Constructor.
        Default Doxygen config options:

        - INPUT: <doxygenSource>
        - OUTPUT_DIRECTORY: <tempDoxyFolder>
        - DOXYFILE_ENCODING: UTF-8
        - GENERATE_XML: YES
        - RECURSIVE: YES
        - EXAMPLE_PATH: examples
        - SHOW_NAMESPACES: YES
        - GENERATE_HTML: NO
        - GENERATE_LATEX: NO

        @details
        @param doxygenBinPath: (str) Path to the Doxygen binary.
        @param doxygenSource: (str) Source files for Doxygen.
        @param tempDoxyFolder: (str) Temporary folder for Doxygen.
        @param doxyConfigFile: (str) Path to a Doxygen config file.
        @param doxyCfgNew: (dict) New Doxygen config options that will be added to the default config (new options will overwrite default options)
        """  # noqa: E501

        if not self.is_doxygen_valid_path(doxygenBinPath):
            raise DoxygenBinPathNotValid(
                f"Invalid Doxygen binary path: {doxygenBinPath}\n"
                f"Make sure Doxygen is installed and the path is correct.\n"
                f"Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/#configure-custom-doxygen-binary."
            )

        self.doxygenBinPath: str = doxygenBinPath
        self.doxygenSource: str = doxygenSource
        self.tempDoxyFolder: str = tempDoxyFolder
        self.doxyConfigFile: Optional[str] = doxyConfigFile
        self.hashFileName: str = "hashChanges.yaml"
        self.hashFilePath: PurePath = PurePath.joinpath(Path(self.tempDoxyFolder), Path(self.hashFileName))
        self.doxyCfg: dict = self.setDoxyCfg(doxyCfgNew)

    def setDoxyCfg(self, doxyCfgNew: dict) -> dict:
        """! Set the Doxygen configuration.
        @details If a custom Doxygen config file is provided, it will be used. Otherwise, default options will be used.
        @details Order of application of parameters:
        @details 1. Custom Doxygen config file
        @details 2. If not provided, default options - in documentation
        @details 3. New Doxygen config options from mkdocs.yml
        @details 3. Overwrite INPUT and OUTPUT_DIRECTORY with the provided values for correct plugin operation.

        @details Overwrite options description:
        @details - INPUT: <doxygenSource>
        @details - OUTPUT_DIRECTORY: <tempDoxyFolder>

        @details Default Doxygen config options:
        @details - DOXYFILE_ENCODING: UTF-8
        @details - GENERATE_XML: YES
        @details - RECURSIVE: YES
        @details - EXAMPLE_PATH: examples
        @details - SHOW_NAMESPACES: YES
        @details - GENERATE_HTML: NO
        @details - GENERATE_LATEX: NO
        @param doxyCfgNew: (dict) New Doxygen config options that will be
         added to the default config (new options will overwrite default options)
        @return: (dict) Doxygen configuration.
        """
        doxyCfg = {}

        if self.doxyConfigFile is not None and self.doxyConfigFile != "":
            try:
                with open(self.doxyConfigFile, "r") as file:
                    doxyCfg.update(self.str2dox_dict(file.read()))
            except FileNotFoundError as e:
                raise DoxygenCustomConfigNotFound(
                    f"Custom Doxygen config file not found: {self.doxyConfigFile}\n"
                    f"Make sure the path is correct."
                    f"Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/#configure-custom-doxygen-configuration-file."
                ) from e
        else:
            doxyCfg = {
                "DOXYFILE_ENCODING": "UTF-8",
                "GENERATE_XML": "YES",
                "RECURSIVE": "YES",
                "EXAMPLE_PATH": "examples",
            }

        # MkDoxy only cares about the XML output. Always override these.
        overrides = {
            "GENERATE_XML": "YES",
            "GENERATE_HTML": "NO",
            "GENERATE_LATEX": "NO",
        }

        doxyCfg.update(overrides)
        doxyCfg["INPUT"] = self.merge_doxygen_input(doxyCfg)
        doxyCfg["OUTPUT_DIRECTORY"] = self.tempDoxyFolder
        doxyCfg.update(doxyCfgNew)

        if self.doxygenSource and self.doxyConfigFile:
            log.info(f"Merged `src-dirs` and `INPUT` from `doxy-cfg-file`:\n  INPUT = {doxyCfg['INPUT']}")

        return doxyCfg

    def merge_doxygen_input(self, doxyCfg):
        """! Merge `src-dirs` (if any) with the "INPUT" paths from the `doxy-cfg-file` (if any). Paths are de-duplicated.
        @details
        @param doxyCfg: (dict) the current doxygen configuration to merge with.
        @return: (str) A string containing the relative paths to be set as "INPUT", separated by " ".
        """
        doxycfg_input = doxyCfg.get("INPUT", "")

        if not self.doxygenSource or self.doxygenSource == "":
            return doxycfg_input

        if not doxycfg_input or doxycfg_input == "":
            return self.doxygenSource

        # `src-dirs` is always relative to the directory containing the `doxy-cfg-file`.
        abs_run_dir = self.getDoxygenRunFolder().resolve()

        # Make all paths absolute and deduplicate them by pushing into a dictionary.

        # First paths from `src-dirs`. They are relative to the current working directory.
        abs_path_dict = dict.fromkeys(Path(src_dir).resolve() for src_dir in self.doxygenSource.split(" "))
        # Now paths from the config file. They are relative to `abs_run_dir`
        abs_path_dict |= dict.fromkeys(
            Path.joinpath(abs_run_dir, input_item).resolve() for input_item in doxycfg_input.split(" ")
        )

        return " ".join(os.path.relpath(abs_path, abs_run_dir) for abs_path in abs_path_dict.keys())



    def is_doxygen_valid_path(self, doxygen_bin_path: str) -> bool:
        """! Check if the Doxygen binary path is valid.
        @details Accepts a full path or just 'doxygen' if it exists in the system's PATH.
        @param doxygen_bin_path: (str) The path to the Doxygen binary or just 'doxygen'.
        @return: (bool) True if the Doxygen binary path is valid, False otherwise.
        """
        # If the path is just 'doxygen', search for it in the system's PATH
        if doxygen_bin_path.lower() == "doxygen":
            return shutil.which("doxygen") is not None

        # Use pathlib to check if the provided full path is a file and executable
        path = Path(doxygen_bin_path)
        return path.is_file() and os.access(path, os.X_OK)

    # Source of dox_dict2str: https://xdress-fabio.readthedocs.io/en/latest/_modules/xdress/doxygen.html#XDressPlugin
    def dox_dict2str(self, dox_dict: dict) -> str:
        """! Convert a dictionary to a string that can be written to a doxygen config file.
        @details
        @param dox_dict: (dict) Dictionary to convert.
        @return: (str) String that can be written to a doxygen config file.
        """
        s = ""
        new_line = "{option} = {value}\n"
        for key, value in dox_dict.items():
            if value is True:
                _value = "YES"
            elif value is False:
                _value = "NO"
            else:
                _value = value

            s += new_line.format(option=key.upper(), value=_value)

        # Don't need an empty line at the end
        return s.strip()

    def str2dox_dict(self, dox_str: str) -> dict:
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
                        f"In custom Doxygen config file: {self.doxyConfigFile}\n"
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
                f"Invalid custom Doxygen config file: {self.doxyConfigFile}\n"
                f"Make sure the file is in standard Doxygen format."
                f"Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/."
            ) from e
        return dox_dict

    def hasChanged(self) -> bool:
        """! Check if the source files have changed since the last run.
        @details
        @return: (bool) True if the source files have changed since the last run.
        """

        def hashWrite(filename: PurePath, hash: str):
            with open(filename, "w") as file:
                file.write(hash)

        def hashRead(filename: PurePath) -> str:
            with open(filename, "r") as file:
                return str(file.read())

        sha1 = hashlib.sha1()
        srcs = self.doxyCfg["INPUT"].split(" ")
        for src in srcs:
            for path in Path(src).rglob("*.*"):
                # # Code from https://stackoverflow.com/a/22058673/15411117
                # # BUF_SIZE is totally arbitrary, change for your app!
                BUF_SIZE = 65536  # let's read stuff in 64kb chunks!
                if path.is_file():
                    with open(path, "rb") as f:
                        while True:
                            data = f.read(BUF_SIZE)
                            if not data:
                                break
                            sha1.update(data)
                # print(f"{path}: {sha1.hexdigest()}")

        hashNew = sha1.hexdigest()
        if Path(self.hashFilePath).is_file():
            hashOld = hashRead(self.hashFilePath)
            if hashNew == hashOld:
                return False

        hashWrite(self.hashFilePath, hashNew)
        return True

    def run(self):
        """! Run Doxygen with the current configuration using the Popen class.
        @details
        """
        doxyBuilder = Popen(
            [self.doxygenBinPath, "-"],
            stdout=PIPE,
            stdin=PIPE,
            stderr=PIPE,
            cwd=self.getDoxygenRunFolder(),
        )
        (doxyBuilder.communicate(self.dox_dict2str(self.doxyCfg).encode("utf-8"))[0].decode().strip())
        # log.info(self.destinationDir)
        # log.info(stdout_data)

    def checkAndRun(self):
        """! Check if the source files have changed since the last run and run Doxygen if they have.
        @details
        @return: (bool) True if Doxygen was run.
        """
        if self.hasChanged():
            self.run()
            return True
        else:
            return False

    def getOutputFolder(self) -> PurePath:
        """! Get the path to the XML output folder.
        @details
        @return: (PurePath) Path to the XML output folder.
        """
        return Path.joinpath(Path(self.tempDoxyFolder), Path("xml"))

    def getDoxygenRunFolder(self):
        """! Get the working directory to execute Doxygen in. Important to resolve releative paths.
        @details When a doxygen config file is provided, this is its containing directory. Otherwise it's the current
          working directory.
        @return: (Path) Path to the folder to execute Doxygen in.
        """
        if not self.doxyConfigFile:
            return Path.cwd()

        return Path(self.doxyConfigFile).parent


# not valid path exception
class DoxygenBinPathNotValid(Exception):
    pass


class DoxygenCustomConfigNotFound(Exception):
    pass


class DoxygenCustomConfigNotValid(Exception):
    pass
