from setuptools import setup, find_packages


def readme():
    with open("README.md") as f:
        return f.read()


def requirements():
    with open("requirements.txt") as f:
        return f.read().splitlines()


def import_requirements():
    """Imports requirements from requirements.txt file."""
    with open("requirements.txt") as f:
        return f.read().splitlines()


def import_dev_requirements():
    """Imports requirements from devdeps.txt file."""
    with open("devdeps.txt") as f:
        return f.read().splitlines()


# https://pypi.org/project/mkdoxy/
setup(
    name="mkdoxy",
    version="2.0.0",
    description="MkDoxy → MkDocs + Doxygen = easy documentation generator with code snippets",
    long_description=readme(),
    long_description_content_type="text/markdown",
    keywords="mkdoxy, python, open-source, documentation, mkdocs, doxygen, "
    "multilanguage, code-snippets, code, snippets, documentation-generator",
    # noqa: E501
    url="https://github.com/JakubAndrysek/MkDoxy",
    author="Jakub Andrýsek",
    author_email="email@kubaandrysek.cz",
    license="MIT",
    python_requires=">=3.9",
    project_urls={
        "Source": "https://github.com/JakubAndrysek/MkDoxy",
        "Documentation": "https://mkdoxy.kubaandrysek.cz/",
        "Tracker": "https://github.com/JakubAndrysek/MkDoxy/issues",
        "Funding": "https://github.com/sponsors/jakubandrysek",
    },
    install_requires=import_requirements(),
    extras_require={
        "dev": import_dev_requirements(),
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    package_data={"mkdoxy": ["templates/*.jinja2"]},
    entry_points={
        "mkdocs.plugins": ["mkdoxy = mkdoxy.plugin:MkDoxy"],
        # folder mkdoxy/cli.py
        # "console_scripts": ["mkdoxy = mkdoxy.cli:cli"],
        "console_scripts": ["mkdoxy = mkdoxy.__main__:main"],
    },
)
