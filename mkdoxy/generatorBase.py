import logging
import os
import string
from typing import Dict

from jinja2 import BaseLoader, Environment, Template
from jinja2.exceptions import TemplateError
from mkdocs import exceptions
from pprint import pformat

import mkdoxy
from mkdoxy.constants import Kind
from mkdoxy.filters import use_code_language
from mkdoxy.node import DummyNode, Node
from mkdoxy.utils import (
    merge_two_dicts,
    parseTemplateFile,
    recursive_find,
    recursive_find_with_parent,
)

log: logging.Logger = logging.getLogger("mkdocs")


LETTERS = string.ascii_lowercase + "~_@\\"


class GeneratorBase:
    """! Base class for all generators."""

    def __init__(self, templateDir: str = "", ignore_errors: bool = False, debug: bool = False):
        """! Constructor.
        @details
        @param templateDir (str): Path to the directory with custom templates (default: "")
        @param ignore_errors (bool): If True, errors will be ignored (default: False)
        @param debug (bool): If True, debug messages will be printed (default: False)
        """

        self.debug: bool = debug  # if True, debug messages will be printed
        self.templates: Dict[str, Template] = {}
        self.metaData: Dict[str, list[str]] = {}

        environment = Environment(loader=BaseLoader())
        environment.filters["use_code_language"] = use_code_language
        # code from https://github.com/daizutabi/mkapi/blob/master/mkapi/core/renderer.py#L29-L38
        path = os.path.join(os.path.dirname(mkdoxy.__file__), "templates")
        ENDING = (".jinja2", ".j2", ".jinja")
        for fileName in os.listdir(path):
            filePath = os.path.join(path, fileName)

            # accept any case of the file ending
            if fileName.lower().endswith(ENDING):
                with open(filePath, "r") as file:
                    name = os.path.splitext(fileName)[0]
                    fileTemplate, metaData = parseTemplateFile(file.read())
                    self.templates[name] = environment.from_string(fileTemplate)
                    self.metaData[name] = metaData
            else:
                log.error(
                    f"Trying to load unsupported file '{filePath}'. Supported file ends with {ENDING}."
                    f"Look at documentation: https://mkdoxy.kubaandrysek.cz/usage/#custom-jinja-templates."
                )

        # test if templateDir is existing
        if templateDir:
            if not os.path.exists(templateDir):
                raise exceptions.ConfigurationError(f"Custom template directory '{templateDir}' does not exist.")
            # load custom templates and overwrite default templates - if they exist
            for fileName in os.listdir(templateDir):
                filePath = os.path.join(templateDir, fileName)
                if fileName.lower().endswith(ENDING):
                    with open(filePath, "r") as file:
                        name = os.path.splitext(fileName)[0]
                        fileTemplate, metaData = parseTemplateFile(file.read())
                        self.templates[name] = environment.from_string(fileTemplate)
                        self.metaData[name] = metaData
                        log.info(f"Overwriting template '{name}' with custom template.")
                else:
                    log.error(
                        f"Trying to load unsupported file '{filePath}'. Supported file ends with {ENDING}."
                        f"Look at documentation: https://mkdoxy.kubaandrysek.cz/usage/#custom-jinja-templates."
                    )

    @staticmethod
    def shift_each_line(value: str, shift_char: str = "\t") -> str:
        """! Shift each line of a given string for a given character.
        @details It is used to shift the content for Markdown code blocks or other content that should be shifted.
        @param value (str): String to shift.
        @param shift_char (str): Character to shift the string (default: '\t').
        @return (str): Shifted string.
        """
        return "\n".join(shift_char + line for line in value.split("\n"))

    def loadConfigAndTemplate(self, name: str) -> [Template, dict]:
        template = self.templates.get(name)
        if not template:
            raise exceptions.Abort(
                f"Trying to load unexciting template '{name}'. Please create a new template file with name '{name}.jinja2'"  # noqa: E501
            )
        metaData = self.metaData.get(name, {})
        return template, metaData

    def render(self, tmpl: Template, data: dict) -> str:
        """! Render a template with given data.
        @details
        @param tmpl (Template): Template to render.
        @param data (dict): Data to render the template.
        @return (str): Rendered template.
        """

        def print_node_content(node: Node, level=0, max_depth=1):
            if level > max_depth:
                return ""  # Stop recursion when max depth is exceeded

            indent = "\n" + "  " * (level * 4) + "- "  # Indentation for better readability
            # node_representation = f"{indent}Node at Level {level}: {pformat(vars(node))}\n"
            node_representation = f"{indent}Node at Level {level}: {node.name}\n"
            # print all attributes of the node
            for key, value in vars(node).items():
                if key == "children":
                    continue
                node_representation += f"{indent}  {key}: {pformat(value)}\n"

            # Assuming each node has a list or iterable of child nodes in an attribute like `children`
            for child in getattr(node, "children", []):
                node_representation += print_node_content(child, level + 1, max_depth)

            return node_representation

        try:
            # if self.debug:
            # print('Generating', path) # TODO: add path to data
            rendered: str = tmpl.render(data, pformat=pformat, vars=vars, print_node_content=print_node_content)
            return rendered
        except TemplateError as e:
            raise Exception(str(e)) from e

    def error(
        self,
        config: dict,
        title: str,
        description: str,
        code_header: str = "",
        code: str = "",
        code_language: str = "",
        snippet_code: str = "",
    ):
        """! Render an error page.
        @details
        @param config (dict): Config for the template.
        @param title (str): Title of the error.
        @param description (str): Description of the error.
        @param code_header (str): Header of the code (default: "")
        @param code (str): Code (default: "")
        @param code_language (str): Language of the code (default: "")
        @param snippet_code (str): Snippet code (default: "")
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("error")

        data = {
            "title": title,
            "description": description,
            "code": code,
            "code_header": code_header,
            "code_language": code_language,
            "snippet_code": snippet_code,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def annotated(self, nodes: [Node], config: dict = None):
        """! Render an annotated page.
        @details
        @param nodes ([Node]): List of nodes to render.
        @param config (dict): Config for the template (default: None)
        @return (str): Rendered annotated page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("annotated")
        data = {
            "nodes": nodes,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def examples(self, nodes: [Node], config=None):
        """! Render an examples page.
        @details
        @param nodes ([Node]): List of nodes to render.
        @param config (dict): Config for the template (default: None)
        @return (str): Rendered examples page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("examples")
        data = {
            "nodes": nodes,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def programlisting(self, node: [Node], config: dict = None):
        """! Render a programlisting page.
        @details
        @param node ([Node]): Node to render.
        @param config (dict): Config for the template (default: None)
        @return (str): Rendered programlisting page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("programlisting")
        data = {
            "node": node,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def code(self, node: [Node], config: dict = None, code: str = ""):
        """! Render a code page.
        @details
        @param node ([Node]): Node to render.
        @param config (dict): Config for the template (default: None)
        @param code (str): Code to render (default: "")
        @return (str): Rendered code page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("code")
        # newConfig = merge_two_dicts(CODE_CONFIG, config)

        data = {
            "node": node,
            "config": merge_two_dicts(config, metaConfig),
            "code": code,
        }

        return self.render(template, data)

    def fileindex(self, nodes: [Node], config: dict = None):
        """! Render a fileindex page.
        @details
        @param nodes ([Node]): List of nodes to render.
        @param config (dict): Config for the template (default: None)
        @return (str): Rendered fileindex page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("files")
        data = {
            "nodes": nodes,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def namespaces(self, nodes: [Node], config: dict = None):
        """! Render a namespaces page.
        @details
        @param nodes ([Node]): List of nodes to render.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered namespaces page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("namespaces")
        data = {
            "nodes": nodes,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def page(self, node: Node, config: dict = None):
        """! Render a page.
        @details
        @param node (Node): Node to render.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("page")
        data = {
            "node": node,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def example(self, node: Node, config: dict = None):
        """! Render an example page.
        @details
        @param node (Node): Node to render.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered example page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("example")
        data = {
            "node": node,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def relatedpages(self, nodes: [Node], config: dict = None):
        """! Render a related pages page.
        @details
        @param nodes ([Node]): List of nodes to render.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered related pages page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("relatedPages")
        data = {
            "nodes": nodes,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def classes(self, nodes: [Node], config: dict = None):
        """! Render a classes page.
        @details
        @param nodes ([Node]): List of nodes to render.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered classes page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("classes")

        classes = recursive_find(nodes, Kind.CLASS)
        classes.extend(recursive_find(nodes, Kind.STRUCT))
        classes.extend(recursive_find(nodes, Kind.INTERFACE))
        dictionary = {letter: [] for letter in LETTERS}

        for klass in classes:
            asd = klass.name_short[0].lower()
            dictionary[asd].append(klass)

        for letter in list(dictionary):
            if len(dictionary[letter]) == 0:
                del dictionary[letter]

        data = {
            "dictionary": dictionary,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def _find_base_classes(self, nodes: [Node], derived: Node):
        """! Find base classes of a node.
        @details
        @param nodes ([Node]): List of nodes to search.
        @param derived (Node): Derived node.
        @return ([Node]): List of base classes.
        """
        ret = []
        for node in nodes:
            if isinstance(node, str):
                ret.append({"refid": node, "derived": derived})
            elif node.kind.is_parent() and not node.kind.is_namespace():
                bases = node.base_classes
                if len(bases) == 0:
                    ret.append(node)
                else:
                    ret.extend(self._find_base_classes(bases, node))
        return ret

    def modules(self, nodes: [Node], config: dict = None):
        """! Render a modules page.
        @details
        @param nodes ([Node]): List of nodes to render.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered modules page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("modules")
        data = {
            "nodes": nodes,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def hierarchy(self, nodes: [Node], config: dict = None):
        """! Render a hierarchy page.
        @details
        @param nodes ([Node]): List of nodes to render.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered hierarchy page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("hierarchy")

        classes = recursive_find(nodes, Kind.CLASS)
        classes.extend(recursive_find(nodes, Kind.STRUCT))
        classes.extend(recursive_find(nodes, Kind.INTERFACE))

        bases = self._find_base_classes(classes, None)
        deduplicated = {base.refid: base for base in bases if not isinstance(base, dict)}

        for base in bases:
            if isinstance(base, dict):
                if base["refid"] not in deduplicated:
                    deduplicated[base["refid"]] = []
                deduplicated[base["refid"]].append(base)

        deduplicated_arr = []
        for key, children in deduplicated.items():
            if isinstance(children, list):
                deduplicated_arr.append(DummyNode(key, list(map(lambda x: x["derived"], children)), Kind.CLASS))
            else:
                found: Node = next((klass for klass in classes if klass.refid == key), None)
                if found:
                    deduplicated_arr.append(found)

        data = {
            "classes": deduplicated_arr,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def function(self, node: Node, config: dict = None):
        """! Render a function page.
        @details
        @param node (Node): Node to render.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered function page.
        """
        if config is None:
            config = {}
        templateMemDef, metaConfigMemDef = self.loadConfigAndTemplate("memDef")
        templateCode, metaConfigCode = self.loadConfigAndTemplate("code")

        data = {
            "node": node,
            "configMemDef": merge_two_dicts(config, metaConfigMemDef),
            "templateCode": templateCode,
            "configCode": metaConfigCode,
            "config": merge_two_dicts(config, metaConfigMemDef),
        }
        return self.render(templateMemDef, data)

    def member(self, node: Node, config: dict = None):
        """! Render a member page.
        @details
        @param node (Node): Node to render.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered member page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("member")
        templateMemDef, metaConfigMemDef = self.loadConfigAndTemplate("memDef")
        templateMemTab, metaConfigMemTab = self.loadConfigAndTemplate("memTab")
        templateCode, metaConfigCode = self.loadConfigAndTemplate("code")

        data = {
            "node": node,
            "templateMemDef": templateMemDef,
            "configMemDef": metaConfigMemDef,
            "templateMemTab": templateMemTab,
            "configMemTab": metaConfigMemTab,
            "templateCode": templateCode,
            "configCode": metaConfigCode,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def file(self, node: Node, config: dict = None):
        """! Render a file page.
        @details
        @param node (Node): Node to render.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered file page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("member")
        templateMemDef, metaConfigMemDef = self.loadConfigAndTemplate("memDef")
        templateMemTab, metaConfigMemTab = self.loadConfigAndTemplate("memTab")

        data = {
            "node": node,
            "templateMemDef": templateMemDef,
            "configMemDef": metaConfigMemDef,
            "templateMemTab": templateMemTab,
            "configMemTab": metaConfigMemTab,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)

    def index(
        self,
        nodes: [Node],
        kind_filters: Kind,
        kind_parents: [Kind],
        title: str,
        config: dict = None,
    ):
        """! Render an index page.
        @details
        @param nodes ([Node]): List of nodes to render.
        @param kind_filters (Kind): Kind of nodes to render.
        @param kind_parents ([Kind]): List of parent kinds of nodes to render.
        @param title (str): Title of the index page.
        @param config (dict): Config for the template. (default: None)
        @return (str): Rendered index page.
        """
        if config is None:
            config = {}
        template, metaConfig = self.loadConfigAndTemplate("index")

        found_nodes = recursive_find_with_parent(nodes, kind_filters, kind_parents)
        dictionary = {letter: [] for letter in LETTERS}

        # Sort items into the dictionary
        for found in found_nodes:
            dictionary[found.name_tokens[-1][0].lower()].append(found)

        # Delete unused letters
        for letter in list(dictionary):
            if len(dictionary[letter]) == 0:
                del dictionary[letter]

        # Sort items if they have the same name
        sorted_dictionary = {}
        for letter, items in dictionary.items():
            d = {}
            for item in items:
                # The name of the item is not yet in the dictionary
                if item.name_short not in d:
                    d[item.name_short] = [item.parent]

                else:
                    found = any(test.refid == item.parent.refid for test in d[item.name_short])
                    if not found:
                        d[item.name_short].append(item.parent)

            sorted_dictionary[letter] = d

        data = {
            "title": title,
            "dictionary": sorted_dictionary,
            "config": merge_two_dicts(config, metaConfig),
        }
        return self.render(template, data)
