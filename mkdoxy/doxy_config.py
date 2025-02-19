import logging
from pathlib import Path

from mkdocs.config import Config
from mkdocs.config import config_options as c

log: logging.Logger = logging.getLogger("mkdocs")

config_scheme_legacy = {
    "full-doc": "full_doc",
    "ignore-errors": "ignore_errors",
    "save-api": "custom_api_folder",
    "doxygen-bin-path": "doxygen_bin_path",
}

config_project_legacy = {
    "src-dirs": "src_dirs",
    "full-doc": "full_doc",
    "ignore-errors": "ignore_errors",
    "doxy-cfg": "doxy_config_dict",
    "doxy-cfg-file": "doxy_config_file",
    "template-dir": "custom_template_dir",
}


class MkDoxyConfigProject(Config):
    """! Configuration for each project in the MkDoxy configuration file.
    @details New type of configuration for each project in the MkDoxy configuration file.
    It will replace the old configuration type.

    @param src_dirs: (str) Source directories for Doxygen - INPUT
    @param full_doc: (bool) Generate full documentation
    @param debug: (bool) Debug mode
    @param ignore_errors: (bool) Ignore errors
    @param doxy_config_dict: (dict) Doxygen additional configuration
    @param doxy_config_default: (bool) Use default MkDoxy Doxygen configuration
    @param doxy_config_file: (str) Doxygen configuration file
    @param doxy_config_file_force: (bool) Do not use default MkDoxy Doxygen configuration, use only Doxygen configuration file
    @param custom_template_dir: (str) Custom template directory
    """

    src_dirs = c.Type(str)
    full_doc = c.Type(bool, default=True)
    debug = c.Type(bool, default=False)
    ignore_errors = c.Type(bool, default=False)
    doxy_config_dict = c.Type(dict, default={})
    doxy_config_default = c.Type(bool, default=True)
    doxy_config_file = c.Optional(c.Type(Path))
    doxy_config_file_force = c.Type(bool, default=False)
    custom_template_dir = c.Optional(c.Type(str))


class MkDoxyConfig(Config):
    """! Global configuration for the MkDoxy plugin.
    @details New type of global configuration for the MkDoxy plugin. It will replace the old configuration type.
    @param projects: (dict) Project configuration - multiple projects
    @param full_doc: (bool) Generate full documentation - global (all projects)
    @param debug: (bool) Debug mode
    @param ignore_errors: (bool) Ignore errors
    @param custom_api_folder: (str) Custom API folder for Doxygen and MD output (default in temp folder)
    @param doxygen_bin_path: (str) Path to Doxygen binary - default "doxygen"
    """

    projects = c.DictOfItems(c.SubConfig(MkDoxyConfigProject), default={})  # project configuration - multiple projects
    full_doc = c.Type(bool, default=True)  # generate full documentation - global (all projects)
    debug = c.Type(bool, default=False)  # debug mode
    ignore_errors = c.Type(bool, default=False)  # ignore errors
    custom_api_folder = c.Optional(c.Type(str))  # custom API folder for Doxygen and MD output (default in temp folder)
    doxy_config_dict = c.Type(
        dict, default={}
    )  # Doxygen additional configuration - it is overwritten by project config
    doxygen_bin_path = c.Type(Path, default=Path("doxygen"))  # path to Doxygen binary (default "doxygen"

    generate_diagrams = c.Type(bool, default=False)  # generate diagrams
    generate_diagrams_format = c.Choice(("svg", "png", "jpg", "gif"), default="svg")  # diagram format
    generate_diagrams_type = c.Choice(("dot", "uml"), default="dot")  # diagram type


# def load_config_by_key(key: str, legacy_key: str, config: Config, legacy: list) -> any:
#     """! Load the configuration value from the global configuration
#     @details Legacy config option is by default None, but if it is not None, it will print a warning and return value.
#     @param key: (str) The new configuration key.
#     @param legacy_key: (str) The legacy configuration key.
#     @param config: (Config) The global configuration object.
#     @param legacy: (list) The list of legacy configuration options.
#     @return: (Optional[str]) The configuration value.
#     """
#     if config.get(legacy_key) is not None:
#         legacy.append(f"Found legacy configuration options: '{legacy_key}' -> replace with '{key}'")
#         return config.get(legacy_key)
#     return config.get(key)
#
#
# def process_configuration(config: Config) -> MkDoxyConfig:
#     """! Process the configuration for the MkDoxy plugin
#     @details Process the configuration for the MkDoxy plugin and validate the configuration.
#     It will try to load new configuration, but it will also check for legacy configuration options.
#     @param config: (Config) The global configuration object.
#     @return: (MkDoxyConfig) The new validated configuration object.
#     @throws ConfigurationError: If the configuration is invalid.
#     """
#     legacy_options = []
#     doxy_config = MkDoxyConfig()
#     doxy_config.full_doc = load_config_by_key("full_doc", "full-doc", config, legacy_options)
#     doxy_config.debug = config.get("debug", False)
#     doxy_config.ignore_errors = load_config_by_key("ignore_errors", "ignore-errors", config, legacy_options)
#     doxy_config.custom_api_folder = load_config_by_key("custom_api_folder", "save-api", config, legacy_options)
#     doxy_config.doxygen_bin_path = load_config_by_key("doxygen_bin_path", "doxygen-bin-path", config, legacy_options)
#
#     doxy_config.generate_diagrams = config.get("generate_diagrams")
#     doxy_config.generate_diagrams_format = config.get("generate_diagrams_format")
#     doxy_config.generate_diagrams_type = config.get("generate_diagrams_type")
#
#     # Validate the global configuration
#     validate_project_config(doxy_config, legacy_options)
#
#     # Validate and load project configuration
#     for project_name, project_cfg in config.get("projects", {}).items():
#         doxy_config.projects[project_name] = load_project_config(project_cfg, project_name)
#
#     return doxy_config
#
#
# def validate_project_config(doxy_cfg: Config, legacy_options: list[str]) -> None:
#     """! Validate the project configuration for the MkDoxy plugin
#     @details Validate the project configuration for the MkDoxy plugin and check for errors and warnings.
#     @param doxy_cfg: (MkDoxyConfig) The project configuration object.
#     @param legacy_options: (list) The list of problems.
#     @return: None
#     @throws ConfigurationError: If the configuration is invalid.
#     """
#     if legacy_options:
#         log.warning("Found some legacy configuration options, please update your configuration!")
#         log.warning("Run command 'mkdoxy migrate mkdocs.yaml' to update your configuration to the new format!")
#         log.warning("More information in the documentation: https://mkdoxy.kubaandrysek.cz/")
#         for problem in legacy_options:
#             log.warning(f"  -> {problem}")
#
#     failed, warnings = doxy_cfg.validate()
#
#     for config_name, warning in warnings:
#         log.warning(f"  -> Config value: '{config_name}'. Warning: {warning}")
#
#     for config_name, error in failed:
#         log.error(f"  -> Config value: '{config_name}'. Error: {error}")
#         raise exceptions.ConfigurationError(f"Config value: '{config_name}'. Error: {error}")
#
#
# def load_project_config_by_key(key: str, legacy_key: str, project_cfg: dict, project_name: str, problems: list) -> any:
#     """! Load the project configuration value from the project configuration
#     @details Legacy project config option is by default None, but if it is not None,
#     it will print a warning and return the value.
#     @param key: (str) The new project configuration key.
#     @param legacy_key: (str) The legacy project configuration key.
#     @param project_cfg: (dict) The project configuration object.
#     @param project_name: (str) The project name.
#     @param problems: (list) The list of problems.
#     @return: (Optional[str]) The project configuration value.
#     """
#     if project_cfg.get(legacy_key) is not None:
#         problems.append(
#             f"Found legacy configuration options: '{legacy_key}' -> replace with '{key}'"
#             f" in project '{project_name}'"
#         )
#         return project_cfg.get(legacy_key)
#     return project_cfg.get(key)
#
#
# def load_project_config(project_cfg: dict, project_name: str) -> MkDoxyConfigProject:
#     """! Load the project configuration for the MkDoxy plugin
#     @details Load the project configuration for the MkDoxy plugin and validate the configuration.
#     @param project_cfg: (dict) The project configuration object.
#     @param project_name: (str) The project name.
#     @return: (MkDoxyConfigProject) The new validated project configuration object.
#     """
#     legacy_options = []
#     doxy_project_cfg = MkDoxyConfigProject()
#     doxy_project_cfg.src_dirs = load_project_config_by_key(
#         "src_dirs", "src-dirs", project_cfg, project_name, legacy_options
#     )
#
#     doxy_project_cfg.full_doc = load_project_config_by_key(
#         "full_doc", "full-doc", project_cfg, project_name, legacy_options
#     )
#     doxy_project_cfg.debug = project_cfg.get("debug", False)
#     doxy_project_cfg.ignore_errors = load_project_config_by_key(
#         "ignore_errors", "ignore-errors", project_cfg, project_name, legacy_options
#     )
#     doxy_project_cfg.doxy_config_dict = load_project_config_by_key(
#         "doxy_config_dict", "doxy-cfg", project_cfg, project_name, legacy_options
#     )
#
#     validate_config_file: Optional[str] = load_project_config_by_key(
#         "doxy_config_file", "doxy-cfg-file", project_cfg, project_name, legacy_options
#     )
#     doxy_project_cfg.doxy_config_file = None if validate_config_file is None else Path(validate_config_file)
#
#     validate_template_dir: Optional[str] = load_project_config_by_key(
#         "custom_template_dir", "template-dir", project_cfg, project_name, legacy_options
#     )
#     doxy_project_cfg.custom_template_dir = None if validate_template_dir is None else Path(validate_template_dir)
#
#     validate_project_config(doxy_project_cfg, legacy_options)
#     return doxy_project_cfg
