"""@package mkdoxy.plugin
MkDoxy → MkDocs + Doxygen = easy documentation generator with code snippets

MkDoxy is a MkDocs plugin for generating documentation from Doxygen XML files.
"""

import logging
from pathlib import Path

from mkdocs.config import Config
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from mkdoxy.cache import Cache
from mkdoxy.doxygen import Doxygen
from mkdoxy.doxygen_generator import DoxygenGenerator
from mkdoxy.generatorAuto import GeneratorAuto
from mkdoxy.generatorBase import GeneratorBase
from mkdoxy.generatorSnippets import GeneratorSnippets
from mkdoxy.xml_parser import XmlParser
from mkdoxy.doxy_config import MkDoxyConfig

log: logging.Logger = logging.getLogger("mkdocs")
plugin_name: str = "MkDoxy"


class MkDoxy(BasePlugin[MkDoxyConfig]):
    """! MkDocs plugin for generating documentation from Doxygen XML files."""

    def __init__(self):
        self.generator_base: dict[str, GeneratorBase] = {}
        self.doxygen: dict[str, Doxygen] = {}
        self.default_template_config = {
            "indent_level": 0,
        }
        # check deprecated config here

    def is_enabled(self) -> bool:
        """! Checks if the plugin is enabled
        @details
        @return: (bool) True if the plugin is enabled.
        """
        return self.config.get("enabled")

    def on_files(self, files: Files, config: Config) -> Files:
        """! Called after files have been gathered by MkDocs.
        @details generate automatic documentation and append files in the list of files to be processed by mkdocs

        @param files: (Files) The files gathered by MkDocs.
        @param config: (Config) The global configuration object.
        @return: (Files) The files gathered by MkDocs.
        """
        for project_name, project_config in self.config.projects.items():
            log.info(f"-> Processing project '{project_name}'")

            # Generate Doxygen and MD files to user defined folder or default temp folder
            if self.config.custom_api_folder:
                temp_doxy_folder = Path.joinpath(Path(self.config.custom_api_folder), Path(project_name))
            else:
                temp_doxy_folder = Path.joinpath(Path(config["site_dir"]), Path("assets/.doxy"), Path(project_name))

            # Create temp dir for Doxygen if not exists
            temp_doxy_folder.mkdir(parents=True, exist_ok=True)

            # Check src changes -> run Doxygen
            doxygen = DoxygenGenerator(
                self.config,
                project_config,
                temp_doxy_folder,
            )
            if doxygen.has_changes():
                log.info("  -> Generating Doxygen files started")
                doxygen.run()
                log.info("  -> Doxygen files generated")
            else:
                log.info("  -> skip generating Doxygen files (nothing seems to have changed)")

            # Parse XML to basic structure
            cache = Cache()
            parser = XmlParser(cache=cache, debug=self.config.debug)

            # Parse basic structure to recursive Nodes
            # TODO: Doxygen index_path should be Path object
            self.doxygen[project_name] = Doxygen(str(doxygen.get_output_xml_folder()), parser=parser, cache=cache)

            # Print parsed files
            if self.config.debug:
                self.doxygen[project_name].printStructure()

            # Prepare generator for future use (GeneratorAuto, SnippetGenerator)
            self.generator_base[project_name] = GeneratorBase(
                project_config.custom_template_dir,
                False,  # ignore_errors=self.config.ignore_errors,
                debug=self.config.debug,
            )

            if self.config.full_doc and project_config.full_doc:
                generatorAuto = GeneratorAuto(
                    generatorBase=self.generator_base[project_name],
                    tempDoxyDir=str(temp_doxy_folder),
                    siteDir=config["site_dir"],
                    apiPath=project_name,
                    doxygen=self.doxygen[project_name],
                    useDirectoryUrls=config["use_directory_urls"],
                )

                template_config = self.default_template_config.copy()

                # Generate full documentation
                generatorAuto.fullDoc(template_config)

                # Generate summary pages
                generatorAuto.summary(template_config)

                # Append files to be processed by MkDocs
                for file in generatorAuto.fullDocFiles:
                    files.append(file)
        return files

    def on_page_markdown(self, markdown: str, page: Page, config: Config, files: Files) -> str:
        """! Generate snippets and append them to the markdown.
        @details
        @param markdown: (str) The markdown content of the page.
        @param page: (Page) The page object.
        @param config: (Config) The global configuration object.
        @param files: (Files) The files gathered by MkDocs.
        @return: (str) The markdown content of the page.
        """

        # update default template config with page meta tags
        page_config = self.default_template_config.copy()
        page_config.update(page.meta)

        generator_snippets = GeneratorSnippets(
            markdown=markdown,
            generatorBase=self.generator_base,
            doxygen=self.doxygen,
            projects=self.config.projects,
            useDirectoryUrls=config["use_directory_urls"],
            page=page,
            config=page_config,
            debug=self.config.debug,
        )

        return generator_snippets.generate()


# def on_serve(self, server):
#     return server
#
# def on_files(self, files: files.Files, config):
#     return files

# def on_nav(self, nav, config, files):
#     return nav
#
# def on_env(self, env, config, files):
#     return env
#
# def on_config(self, config):
#     return config
#
# def on_pre_build(self, config: base.Config):
#     return
# def on_post_build(self, config):
#     return
#
# def on_pre_template(self, template, template_name, config):
#     return template
#
# def on_template_context(self, context, template_name, config):
#     return context
#
# def on_post_template(self, output_content, template_name, config):
#     return output_content
#
# def on_pre_page(self, page: pages.Page, config, files: files.Files):
#     return page
#
# def on_page_read_source(self, page: pages.Page, config):
#     return
#
# def on_page_markdown(self, markdown, page, config, files):
#     return markdown
#
# def on_page_content(self, html, page, config, files):
#     return html
#
# def on_page_context(self, context, page, config, nav):
#     return context
#
# def on_post_page(self, output_content, page, config):
#     return output_content
