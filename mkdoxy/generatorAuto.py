import logging
import os

from mkdocs.structure import files

from mkdoxy.constants import Kind
from mkdoxy.doxygen import Doxygen
from mkdoxy.generatorBase import GeneratorBase
from mkdoxy.node import Node

log: logging.Logger = logging.getLogger("mkdocs")

ADDITIONAL_FILES = {
    "Namespace ListNamespace List": "namespaces.md",
    "Namespace Members": "namespace_members.md",
    "Namespace Member Functions": "namespace_member_functions.md",
    "Namespace Member Variables": "namespace_member_variables.md",
    "Namespace Member Typedefs": "namespace_member_typedefs.md",
    "Namespace Member Enumerations": "namespace_member_enums.md",
    "Class Index": "classes.md",
    "Class Hierarchy": "hierarchy.md",
    "Class Members": "class_members.md",
    "Class Member Functions": "class_member_functions.md",
    "Class Member Variables": "class_member_variables.md",
    "Class Member Typedefs": "class_member_typedefs.md",
    "Class Member Enumerations": "class_member_enums.md",
}


def generate_link(name, url, end="\n") -> str:
    def normalize(name):
        return "\\" + name if name.startswith("__") else name

    return f"- [{normalize(name)}]({url}){end}"


# def generate_link(name, url) -> str:
# 	return f"\t\t- '{name}': '{url}'\n"


class GeneratorAuto:
    def __init__(
        self,
        generatorBase: GeneratorBase,
        tempDoxyDir: str,
        siteDir: str,
        apiPath: str,
        doxygen: Doxygen,
        useDirectoryUrls: bool,
    ):
        self.generatorBase = generatorBase
        self.tempDoxyDir = tempDoxyDir
        self.siteDir = siteDir
        self.apiPath = apiPath
        self.doxygen = doxygen
        self.useDirectoryUrls = useDirectoryUrls
        self.fullDocFiles = []
        self.debug = generatorBase.debug
        os.makedirs(os.path.join(self.tempDoxyDir, self.apiPath), exist_ok=True)

    def save(self, path: str, output: str):
        pathRel = os.path.join(self.apiPath, path)
        self.fullDocFiles.append(files.File(pathRel, self.tempDoxyDir, self.siteDir, self.useDirectoryUrls))
        with open(os.path.join(self.tempDoxyDir, pathRel), "w", encoding="utf-8") as file:
            file.write(output)

    def save_image(self, path: str, image_source_link: str):
        # copy image from image_source_link to mkdocs
        source = os.path.join(self.tempDoxyDir, "html", image_source_link)
        if not os.path.exists(source):
            return
        destination = os.path.join(self.siteDir, self.apiPath, path, image_source_link)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(source, "rb") as fsrc:
            with open(destination, "wb") as fdst:
                fdst.write(fsrc.read())

    def fullDoc(self, defaultTemplateConfig: dict):
        self.annotated(self.doxygen.root.children, defaultTemplateConfig)
        self.fileindex(self.doxygen.files.children, defaultTemplateConfig)
        self.members(self.doxygen.root.children, defaultTemplateConfig)
        self.members(self.doxygen.groups.children, defaultTemplateConfig)
        self.files(self.doxygen.files.children, defaultTemplateConfig)
        self.namespaces(self.doxygen.root.children, defaultTemplateConfig)
        self.classes(self.doxygen.root.children, defaultTemplateConfig)
        self.hierarchy(self.doxygen.root.children, defaultTemplateConfig)
        self.modules(self.doxygen.groups.children, defaultTemplateConfig)
        self.pages(self.doxygen.pages.children, defaultTemplateConfig)
        # self.examples(self.doxygen.examples.children) # TODO examples
        self.relatedpages(self.doxygen.pages.children)
        self.index(
            self.doxygen.root.children,
            [Kind.FUNCTION, Kind.VARIABLE, Kind.TYPEDEF, Kind.ENUM],
            [Kind.CLASS, Kind.STRUCT, Kind.INTERFACE],
            "Class Members",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.root.children,
            [Kind.FUNCTION],
            [Kind.CLASS, Kind.STRUCT, Kind.INTERFACE],
            "Class Member Functions",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.root.children,
            [Kind.VARIABLE],
            [Kind.CLASS, Kind.STRUCT, Kind.INTERFACE],
            "Class Member Variables",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.root.children,
            [Kind.TYPEDEF],
            [Kind.CLASS, Kind.STRUCT, Kind.INTERFACE],
            "Class Member Typedefs",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.root.children,
            [Kind.ENUM],
            [Kind.CLASS, Kind.STRUCT, Kind.INTERFACE],
            "Class Member Enums",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.root.children,
            [Kind.FUNCTION, Kind.VARIABLE, Kind.TYPEDEF, Kind.ENUM],
            [Kind.NAMESPACE],
            "Namespace Members",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.root.children,
            [Kind.FUNCTION],
            [Kind.NAMESPACE],
            "Namespace Member Functions",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.root.children,
            [Kind.VARIABLE],
            [Kind.NAMESPACE],
            "Namespace Member Variables",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.root.children,
            [Kind.TYPEDEF],
            [Kind.NAMESPACE],
            "Namespace Member Typedefs",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.root.children,
            [Kind.ENUM],
            [Kind.NAMESPACE],
            "Namespace Member Enums",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.files.children,
            [Kind.FUNCTION],
            [Kind.FILE],
            "Functions",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.files.children,
            [Kind.DEFINE],
            [Kind.FILE],
            "Macros",
            defaultTemplateConfig,
        )
        self.index(
            self.doxygen.files.children,
            [Kind.VARIABLE, Kind.UNION, Kind.TYPEDEF, Kind.ENUM],
            [Kind.FILE],
            "Variables",
            defaultTemplateConfig,
        )

    def annotated(self, nodes: [Node], config: dict = None):
        path = "annotated.md"
        output = self.generatorBase.annotated(nodes, config)
        self.save(path, output)

    def programlisting(self, node: [Node], config: dict = None):
        path = f"{node.refid}_source.md"

        output = self.generatorBase.programlisting(node, config)
        self.save(path, output)

    def fileindex(self, nodes: [Node], config: dict = None):
        path = "files.md"

        output = self.generatorBase.fileindex(nodes, config)
        self.save(path, output)

    def namespaces(self, nodes: [Node], config: dict = None):
        path = "namespaces.md"

        output = self.generatorBase.namespaces(nodes, config)
        self.save(path, output)

    def page(self, node: Node, config: dict = None):
        path = f"{node.name}.md"

        output = self.generatorBase.page(node, config)
        self.save(path, output)

    def pages(self, nodes: [Node], config: dict = None):
        for node in nodes:
            self.page(node, config)

    def relatedpages(self, nodes: [Node], config: dict = None):
        path = "pages.md"

        output = self.generatorBase.relatedpages(nodes)
        self.save(path, output)

    def example(self, node: Node, config: dict = None):
        path = f"{node.refid}.md"

        output = self.generatorBase.example(node, config)
        self.save(path, output)

    def examples(self, nodes: [Node], config: dict = None):
        for node in nodes:
            if node.is_example:
                if node.has_programlisting:
                    print(f"Generating example {node.name}...")
                self.example(node, config)

        path = "examples.md"

        output = self.generatorBase.examples(nodes, config)
        self.save(path, output)

    def classes(self, nodes: [Node], config: dict = None):
        path = "classes.md"

        output = self.generatorBase.classes(nodes, config)
        self.save(path, output)

    def modules(self, nodes: [Node], config: dict = None):
        path = "modules.md"

        output = self.generatorBase.modules(nodes, config)
        self.save(path, output)

    def hierarchy(self, nodes: [Node], config: dict = None):
        path = "hierarchy.md"

        output = self.generatorBase.hierarchy(nodes, config)
        self.save(path, output)

    def member(self, node: Node, config: dict = None):
        path = node.filename
        refid = node.refid

        if node.has_inheritance_graph:
            self.save_image(refid, node.inheritance_graph)
        if node.has_collaboration_graph:
            self.save_image(refid, node.collaboration_graph)
        # if node.has_directory_dependency:
        #     self.save_image(refid, node.directory_dependency)

        output = self.generatorBase.member(node, config)
        self.save(path, output)

        if node.is_language or node.is_group or node.is_file or node.is_dir:
            self.members(node.children, config)

    def file(self, node: Node, config: dict = None):
        path = node.filename

        output = self.generatorBase.file(node, config)
        self.save(path, output)

        if node.is_file and node.has_programlisting:
            self.programlisting(node, config)

        if node.is_file or node.is_dir:
            self.files(node.children, config)

    def members(self, nodes: [Node], config: dict = None):
        for node in nodes:
            if node.is_parent or node.is_group or node.is_file or node.is_dir:
                self.member(node, config)

    def files(self, nodes: [Node], config: dict = None):
        for node in nodes:
            if node.is_file or node.is_dir:
                self.file(node, config)

    def index(
        self,
        nodes: [Node],
        kind_filters: Kind,
        kind_parents: [Kind],
        title: str,
        config: dict = None,
    ):
        path = title.lower().replace(" ", "_") + ".md"

        output = self.generatorBase.index(nodes, kind_filters, kind_parents, title, config)
        self.save(path, output)

    def _generate_recursive(self, output_summary: str, node: Node, level: int):
        if node.kind.is_parent():
            output_summary += str(" " * level + generate_link(f"{node.kind.value} {node.name}", f"{node.refid}.md"))
            for child in node.children:
                self._generate_recursive(output_summary, child, level + 2)

    def _generate_recursive_files(self, output_summary: str, node: Node, level: int, config: dict = None):
        if config is None:
            config = []
        if node.kind.is_file() or node.kind.is_dir():
            output_summary += str(" " * int(level + 2) + generate_link(node.name, f"{node.refid}.md", end=""))

            if node.kind.is_file():
                output_summary += f" [[source code]]({node.refid}_source.md) \n"
            else:
                output_summary += "\n"

            for child in node.children:
                self._generate_recursive_files(output_summary, child, level + 2, config)

    def _generate_recursive_examples(self, output_summary: str, node: Node, level: int):
        if node.kind.is_example():
            output_summary += str(" " * level + generate_link(node.name, f"{node.refid}.md"))
            for child in node.children:
                self._generate_recursive_examples(output_summary, child, level + 2)

    def _generate_recursive_groups(self, output_summary: str, node: Node, level: int):
        if node.kind.is_group():
            output_summary += str(" " * level + generate_link(node.title, f"{node.refid}.md"))
            for child in node.children:
                self._generate_recursive_groups(output_summary, child, level + 2)

    def _generate_recursive_pages(self, output_summary: str, node: Node, level: int):
        if node.kind.is_page():
            output_summary += str(" " * level + generate_link(node.title, f"{node.refid}.md"))
            for child in node.children:
                self._generate_recursive_pages(output_summary, child, level + 2)

    def summary(self, defaultTemplateConfig: dict):
        offset = 0
        output_summary = "" + str(" " * (offset + 2) + generate_link("Related Pages", "pages.md"))
        for node in self.doxygen.pages.children:
            self._generate_recursive_pages(output_summary, node, offset + 4)

        output_summary += str(" " * (offset + 2) + generate_link("Modules", "modules.md"))
        for node in self.doxygen.groups.children:
            self._generate_recursive_groups(output_summary, node, offset + 4)

        output_summary += str(" " * (offset + 2) + generate_link("Class List", "annotated.md"))
        for node in self.doxygen.root.children:
            self._generate_recursive(output_summary, node, offset + 4)

        for key, val in ADDITIONAL_FILES.items():
            output_summary += str(" " * (offset + 2) + generate_link(key, val))

        output_summary += str(" " * (offset + 2) + generate_link("Files", "files.md", end="\n"))
        for node in self.doxygen.files.children:
            self._generate_recursive_files(output_summary, node, offset + 4, defaultTemplateConfig)

        # output_summary += str(' ' * (offset + 2) + generate_link('Examples', 'examples.md'))
        # for node in self.doxygen.examples.children:
        # 	self._generate_recursive_examples(node, offset + 4)

        output_summary += str(" " * (offset + 2) + generate_link("File Variables", "variables.md"))
        output_summary += str(" " * (offset + 2) + generate_link("File Functions", "functions.md"))
        output_summary += str(" " * (offset + 2) + generate_link("File Macros", "macros.md"))

        self.save("links.md", output_summary)
