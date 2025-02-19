# MkDoxy

**[MkDoxy](https://mkdoxy.kubaandrysek.cz/)** plugin for **[MkDocs](https://www.mkdocs.org/)** generates API documentation based on **[Doxygen](https://www.doxygen.nl)** comments and **[code snippets](/intro)** in your markdown files.

<p align="center">
<a href="https://hits.seeyoufarm.com"><img src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2FJakubAndrysek%2FMkDoxy&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=true"/></a>
<a href="https://github.com/JakubAndrysek/MkDoxy/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/JakubAndrysek/MkDoxy?style=flat-square"></a>
<a href="https://github.com/JakubAndrysek/MkDoxy/releases" target="_blank"><img src="https://img.shields.io/github/v/release/JakubAndrysek/MkDoxy?style=flat-square"></a>
<a href="https://github.com/JakubAndrysek/MkDoxy/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/JakubAndrysek/MkDoxy?style=flat-square"></a>
<a href="https://github.com/JakubAndrysek/MkDoxy/forks" target="_blank"><img src="https://img.shields.io/github/forks/JakubAndrysek/MkDoxy?style=flat-square"></a>
<a href="https://github.com/JakubAndrysek/MkDoxy/issues" target="_blank"><img src="https://img.shields.io/github/issues/JakubAndrysek/MkDoxy?style=flat-square"></a>
<a href="https://github.com/JakubAndrysek/MkDoxy/discussions" target="_blank"><img src="https://img.shields.io/github/discussions/JakubAndrysek/MkDoxy?style=flat-square"></a>
<a href="https://www.pepy.tech/projects/mkdoxy" target="_blank"><img src="https://static.pepy.tech/badge/mkdoxy"></a>
</p>

> **Warning**
> **Extension is in development**, and a few features are not working properly.
> More information in [Discussions](https://github.com/JakubAndrysek/MkDoxy/discussions) and [Issues](https://github.com/JakubAndrysek/MkDoxy/issues) pages.

---

## [:material-home-edit: Online Demo](https://jakubandrysek.github.io/MkDoxy-demo/) and [:simple-github: Demo source-code ](https://github.com/JakubAndrysek/MkDoxy-demo)

---

**[Feature List](#feature-list)** - **[Installation](#installation)** - **[Quick start](#quick-start)**

## Feature List
- **[Easy to use](#quick-start):**: Just add `mkdoxy` to your `mkdocs.yml` and configure the path to your source code.
- **[Code snippets](./snippets/index.md)**: Generate code snippets in place of your standard Markdown documentation.
- **[Multiple projects](./usage/index.md#multiple-projects)**: Support for multiple projects in one documentation (e.g. C++ and Python).
- **[Multiple source directories](./usage/index.md#multiple-source-directories)**: Configure multiple source directories in one project.
- **[Custom Jinja templates](./usage/index.md#custom-jinja-templates)**: Define custom Jinja templates for rendering Doxygen documentation.
- **[Custom Doxygen configuration](./usage/index.md#custom-doxygen-configuration)**: Specify custom Doxygen configuration for each project.

## Installation
Install the plugin using pip from [PyPI](https://pypi.org/project/mkdoxy/):

```bash
pip install mkdoxy
```
Development version with all dependencies:
```bash
python -m venv .venv
python -m pip install mkdoxy ".[dev]"
```

Install from source:
```bash
pip install git+https://github.com/JakubAndrysek/MkDoxy.git
```

## Quick start

`mkdocs.yml`:
```yaml
site_name: "My MkDoxy documentation"

theme:
  name: material

plugins:
  - search
  - mkdoxy:
      projects:
        myProjectCpp: # name of project must be alphanumeric + numbers (without spaces)
          src-dirs: path/to/src/project1 # path to source code (support multiple paths separated by space) => INPUT
          full-doc: True # if you want to generate full documentation
          doxy-cfg: # standard doxygen configuration (key: value)
            FILE_PATTERNS: "*.cpp *.h*" # specify file patterns to filter out
            RECURSIVE: True # recursive search in source directories
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you want to change.

## Do You Enjoy MkDoxy or Does It Save You Time?
Then definitely consider:

- supporting me on GitHub Sponsors: [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/jakubandrysek)

## License

This project is licensed under the terms of the [MIT license](https://github.com/JakubAndrysek/MkDoxy/blob/main/LICENSE)
