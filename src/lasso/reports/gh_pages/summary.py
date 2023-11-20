"""Summary."""
import logging
import os

import rstcloth
from lasso.reports.corral.herd import Herd
from lasso.reports.tags.tags import Tags

logger = logging.getLogger(__name__)

COLUMNS = ["manual", "changelog", "requirements", "download", "license", "feedback"]

REPO_TYPES = {
    "tool": {
        "title": "Standalone Tools",
        "description": "PDS Tools for Discipline Nodes, Data Providers and Community Users.",
    },
    "library": {
        "title": "Libraries and Clients",
        "description": "Libraries and Clients for programing interfaces to PDS services and data.",
    },
    "core": {
        "title": "Engineering Node Services",
        "description": (
            "Tools and Services centrally deployed by PDS Engineering Node to support "
            "the integration and interoperability of all PDS nodes."
        ),
    },
    "unknown": {"title": "Additional Software Assets", "description": ""},
}


def _indent_ok_for_table(content, indent):
    """Indent—ok?—but for a table.

    :param content:
    :param indent:
    :return:
    """
    if indent == 0:
        return content
    else:
        indent = " " * indent
        if isinstance(content, list):
            return ["".join([indent, line]) for line in content]
        elif "\n" in content:
            content_lines = content.split("\n")
            return f"\n{indent}".join(content_lines)
        else:
            return "".join([indent, content])


# Monkey-patchingthe function used in the rstpackage; should do a pull request eventually
rstcloth.rstcloth._indent = _indent_ok_for_table
_indent = _indent_ok_for_table


class RstClothReferenceable(rstcloth.RstCloth):
    """Apparently this is cloth described in reStructuredText that is also referenceable."""

    def __init__(self, line_width=160):
        """Initializer."""
        super().__init__(line_width=line_width)
        self._deferred_directives = []

    def hyperlink(self, ref, url):
        """Hyperlink the given ``ref`` to ``url``."""
        self._deferred_directives.append(f".. _{ref}: {url}")

    def deferred_directive(self, name, arg=None, fields=None, content=None, indent=0, wrap=True, reference=None):
        """Adds a deferred directive.

        :param name: the directive itself to use
        :param arg: the argument to pass into the directive
        :param fields: fields to append as children underneath the directive
        :param content: the text to write into this element
        :param indent: (optional default=0) number of characters to indent this element
        :param wrap: (optional, default=True) Whether or not to wrap lines to the line_width
        :param reference: (optional, default=None) Reference to call the directive elswhere
        :return:
        """
        logger.debug("Ignoring wrap parameter, presumably for api consistency. wrap=%s", wrap)
        o = list()
        if reference:
            o.append(".. |{0}| {1}::".format(reference, name))
        else:
            o.append(".. {0}::".format(name))

        if arg is not None:
            o[0] += " " + arg

        if fields is not None:
            for k, v in fields:
                o.append(_indent(":" + k + ": " + str(v), 3))

        if content is not None:
            o.append("")

            if isinstance(content, list):
                o.extend(_indent(content, 3))
            else:
                o.append(_indent(content, 3))

        self._deferred_directives.extend(_indent(o, indent))

    def write(self, filename):
        """Write myself to the given ``filename``.

        :param filename:
        :return:
        """
        dirpath = os.path.dirname(filename)
        if os.path.isdir(dirpath) is False:
            try:
                os.makedirs(dirpath)
            except OSError:
                logger.info("{0} exists. ignoring.".format(dirpath))

        with open(filename, "w") as f:
            f.write("\n".join(self._data))
            f.write("\n")
            f.write("\n".join(self._deferred_directives))
            f.write("\n")


def get_table_columns_md():
    """Get the table columns in Markdown format."""

    def column_header(column):
        return f"![{column}](https://nasa-pds.github.io/pdsen-corral/images/{column}_text.png)"

    column_headers = []
    for column in COLUMNS:
        column_headers.append(column_header(column))

    return ["tool", "version", "last updated", "description", *column_headers]


def get_table_columns_rst():
    """Get the table columns in reStructuredText format."""
    column_headers = []
    for column in COLUMNS:
        column_headers.append(f"l |{column}|")

    return ["tool", "version", "last updated", "description", *column_headers]


def rst_column_header_images(d):
    """Column header images for reStructured Text."""
    for column in COLUMNS:
        d.deferred_directive(
            "image",
            arg=f"https://nasa-pds.github.io/pdsen-corral/images/{column}_text.png",
            fields=[("alt", column)],
            reference=column,
        )


def write_md_file(herd, output_file_name, version):
    """Write a Markdown file."""
    from mdutils import MdUtils

    software_summary_md = MdUtils(file_name=output_file_name, title=f"Software Summary (build {version})")

    table = get_table_columns_md()
    n_columns = len(table)
    for _k, ch in herd.get_cattle_heads().items():  # Maybe use .values() and skip the _k
        table.extend(ch.get_table_row(format="md"))
    software_summary_md.new_table(columns=n_columns, rows=herd.number_of_heads() + 1, text=table, text_align="center")

    logger.info(f"Create file {output_file_name}.md")
    software_summary_md.create_md_file()


def write_rst_introduction(d: RstClothReferenceable, version: str):
    """Write a reStructuredText introduction."""
    d.title(f"Software Catalog (Build {version})")

    d.content(f"The software provided for the PDS System Build {version} are listed below and organized by category:")
    d.newline()
    for t, section in REPO_TYPES.items():
        if t != "unknown":
            d.li(f"`{section['title']}`_")
            d.newline()
    d.newline()


def write_rst_file(herd, output_file_name, version):
    """Write the reStructuredText file."""
    d = RstClothReferenceable()

    write_rst_introduction(d, version)

    # create one section per type of repo
    data = {t: [] for t in REPO_TYPES}
    for _k, ch in herd.get_cattle_heads().items():  # Maybe use .values() and skip the _k
        ch.set_rst(d)
        if ch.type in REPO_TYPES.keys():
            data[ch.type].append(ch.get_table_row(format="rst"))
        else:
            logger.warning("unknown type for repo %s in build version %s", ch.repo_name, version)
            data["unknown"].append(ch.get_table_row(format="rst"))

    for type, type_data in data.items():
        if type_data:
            d.h1(REPO_TYPES[type]["title"])
            d.content(REPO_TYPES[type]["description"])
            d.table(get_table_columns_rst(), data=type_data)

    rst_column_header_images(d)

    logger.info(f"Create file {output_file_name}.rst")
    d.write(f"{output_file_name}.rst")


def write_build_summary(
    gitmodules=None, root_dir=".", output_file_name=None, token=None, dev=False, version=None, format="md"
):
    """Write the build summary."""
    herd = Herd(gitmodules=gitmodules, dev=dev, token=token)

    if version is None:
        version = herd.get_shepard_version()
    else:
        # for unit test
        herd.set_shepard_version(version)

    logger.info(f"build version is {version}")
    is_dev = Tags.JAVA_DEV_SUFFIX in version or Tags.PYTHON_DEV_SUFFIX in version
    if dev and not is_dev:
        logger.error(
            f"version of build does not contain {Tags.JAVA_DEV_SUFFIX} or {Tags.PYTHON_DEV_SUFFIX}, "
            "dev build summary is not generated"
        )
        exit(1)
    elif not dev and is_dev:
        logger.error(
            f"version of build contains {Tags.JAVA_DEV_SUFFIX} or {Tags.PYTHON_DEV_SUFFIX}, "
            "release build summary is not generated"
        )
        exit(1)

    if not output_file_name:
        output_file_name = os.path.join(root_dir, version, "index")
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)

    if format == "md":
        write_md_file(herd, output_file_name, version)
    elif format == "rst":
        write_rst_file(herd, output_file_name, version)

    return herd
