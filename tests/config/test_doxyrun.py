import pytest

from pathlib import Path
from mkdoxy.doxy_config import MkDoxyConfig, MkDoxyConfigProject
from mkdoxy.doxygen_generator import DoxygenGenerator, DoxygenCustomConfigNotValid


def test_dox_dict2str():
    dox_dict = {
        "DOXYFILE_ENCODING": "UTF-8",
        "EXAMPLE_PATH": "examples",
        "GENERATE_HTML": False,
        "GENERATE_LATEX": False,
        "GENERATE_XML": True,
        "RECURSIVE": True,
        "SHOW_NAMESPACES": True,
    }

    expected_result = (
        "DOXYFILE_ENCODING = UTF-8\n"
        "EXAMPLE_PATH = examples\n"
        "GENERATE_HTML = NO\n"
        "GENERATE_LATEX = NO\n"
        "GENERATE_XML = YES\n"
        "RECURSIVE = YES\n"
        "SHOW_NAMESPACES = YES"
    )

    assert DoxygenGenerator.dox_dict2str(dox_dict) == expected_result


#  Sets the Doxygen configuration using a custom config file
def test_set_doxy_cfg_custom_file():
    project = MkDoxyConfigProject()
    project.src_dirs = "/path/to/source/files"

    doxygen_run = DoxygenGenerator(
        doxy_config=MkDoxyConfig(),
        project_config=project,
        temp_doxy_folder=Path("/path/to/temp/folder"),
    )

    dox_dict = doxygen_run.get_merged_doxy_dict()

    expected_result = {
        "DOXYFILE_ENCODING": "UTF-8",
        "EXAMPLE_PATH": "examples",
        "GENERATE_HTML": False,
        "GENERATE_LATEX": False,
        "GENERATE_XML": True,
        "INPUT": "/path/to/source/files",
        "OUTPUT_DIRECTORY": "/path/to/temp/folder",
        "RECURSIVE": True,
        "SHOW_NAMESPACES": True,
    }

    assert expected_result == dox_dict


def test_str2dox_dict():
    dox_str = (
        "DOXYFILE_ENCODING = UTF-8\nGENERATE_XML = YES\n"
        "RECURSIVE = YES\nEXAMPLE_PATH = examples\n"
        "SHOW_NAMESPACES = YES\nGENERATE_HTML = NO\nGENERATE_LATEX = NO"
    )

    result = DoxygenGenerator.str2dox_dict(dox_str)

    expected_result = {
        "DOXYFILE_ENCODING": "UTF-8",
        "GENERATE_XML": True,
        "RECURSIVE": True,
        "EXAMPLE_PATH": "examples",
        "SHOW_NAMESPACES": True,
        "GENERATE_HTML": False,
        "GENERATE_LATEX": False,
    }

    assert result == expected_result


def test_str2dox_dict_expanded_config():
    dox_str = (
        "# This is a comment \n"
        "PROJECT_LOGO           =\n"
        'ABBREVIATE_BRIEF       = "The $name class" \\ \n'
        "                         is \n"
        "FILE_PATTERNS          = *.c \n"
        "FILE_PATTERNS          += *.cc\n"
        "PREDEFINED             = BUILD_DATE DOXYGEN=1\n"
    )

    expected_result = {
        "PROJECT_LOGO": "",
        "ABBREVIATE_BRIEF": '"The $name class" is',
        "FILE_PATTERNS": "*.c *.cc",
        "PREDEFINED": "BUILD_DATE DOXYGEN=1",
    }

    assert expected_result == DoxygenGenerator.str2dox_dict(dox_str)


def test_str2dox_dict_expanded_config_errors():
    dox_str = "ONLY_KEY\n"
    error_message = (
        "Invalid line: 'ONLY_KEY'"
        "In custom Doxygen config file: QuestionMark\n"
        "Make sure the file is in standard Doxygen format."
        "Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/."
    )

    with pytest.raises(DoxygenCustomConfigNotValid, match=error_message):
        DoxygenGenerator.str2dox_dict(dox_str, "QuestionMark")

    dox_str = "= ONLY_VALUE\n"
    error_message = (
        "Invalid line: '= ONLY_VALUE'"
        "In custom Doxygen config file: QuestionMark\n"
        "Make sure the file is in standard Doxygen format."
        "Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/."
    )

    with pytest.raises(DoxygenCustomConfigNotValid, match=error_message):
        DoxygenGenerator.str2dox_dict(dox_str, "QuestionMark")

    dox_str = "KEY WITH SPACES = VALUE\n"
    error_message = (
        "Invalid line: 'KEY WITH SPACES = VALUE'"
        "In custom Doxygen config file: QuestionMark\n"
        "Make sure the file is in standard Doxygen format."
        "Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/."
    )

    with pytest.raises(DoxygenCustomConfigNotValid, match=error_message):
        DoxygenGenerator.str2dox_dict(dox_str, "QuestionMark")

    dox_str = "BAD_OPERATOR := VALUE\n"
    error_message = (
        "Invalid line: 'BAD_OPERATOR := VALUE'"
        "In custom Doxygen config file: QuestionMark\n"
        "Make sure the file is in standard Doxygen format."
        "Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/."
    )

    with pytest.raises(DoxygenCustomConfigNotValid, match=error_message):
        DoxygenGenerator.str2dox_dict(dox_str, "QuestionMark")

    dox_str = "BAD_MULTILINE = BAD\n                VALUE\n"
    error_message = (
        "Invalid line: '                VALUE'"
        "In custom Doxygen config file: QuestionMark\n"
        "Make sure the file is in standard Doxygen format."
        "Look at https://mkdoxy.kubaandrysek.cz/usage/advanced/."
    )

    with pytest.raises(DoxygenCustomConfigNotValid, match=error_message):
        DoxygenGenerator.str2dox_dict(dox_str, "QuestionMark")
