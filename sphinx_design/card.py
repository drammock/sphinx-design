import re
from typing import List, NamedTuple, Optional, Tuple

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

from .shared import create_component, make_option

DIRECTIVE_NAME_CARD = "card"
REGEX_HEADER = re.compile(r"^\^{3,}\s*$")
REGEX_FOOTER = re.compile(r"^\+{3,}\s*$")


def setup_card(app: Sphinx):
    """Setup the card components."""
    app.add_directive(DIRECTIVE_NAME_CARD, CardDirective)


class CardContent(NamedTuple):
    """Split card into header (optional), body, footer (optional).

    (offset, content)
    """

    body: Tuple[int, StringList]
    header: Optional[Tuple[int, StringList]] = None
    footer: Optional[Tuple[int, StringList]] = None


class CardDirective(SphinxDirective):
    """A card component."""

    has_content = True
    option_spec = {
        "width": make_option(["auto", "25", "50", "75", "100"]),
        "text-align": make_option(["left", "right", "center"]),
        "img-top": directives.uri,
        "img-bottom": directives.uri,
        "no-shadow": directives.flag,
        "class-card": directives.class_option,
        "class-header": directives.class_option,
        "class-body": directives.class_option,
        "class-footer": directives.class_option,
    }

    def run(self) -> List[nodes.Node]:
        self.assert_has_content()
        return [self.create_card(self, self.options)]

    @classmethod
    def create_card(cls, inst: SphinxDirective, options: dict) -> nodes.Node:
        """Run the directive."""
        card_classes = ["mui-card", "mui-sphinx-override"]
        if "width" in options:
            card_classes += [f'mui-w-{options["width"]}']
        if "text-align" in options:
            card_classes += [f'mui-text-{options["text-align"]}']
        if "no-shadow" in options:
            card_classes += ["mui-shadow"]
        card = create_component(
            "card",
            card_classes + options.get("class-card", []),
        )
        inst.set_source_info(card)

        if "img-top" in options:
            image_top = nodes.image(
                "",
                uri=options["img-top"],
                alt="card-img-top",
                classes=["mui-card-img-top"],
            )
            card.append(image_top)

        components = cls.split_content(inst.content, inst.content_offset)

        if components.header:
            card.append(
                cls._create_component(
                    inst, "header", options, components.header[0], components.header[1]
                )
            )

        card.append(
            cls._create_component(
                inst, "body", options, components.body[0], components.body[1]
            )
        )

        if components.footer:
            card.append(
                cls._create_component(
                    inst, "footer", options, components.footer[0], components.footer[1]
                )
            )

        if "img-bottom" in options:
            image_bottom = nodes.image(
                "",
                uri=options["img-bottom"],
                alt="card-img-bottom",
                classes=["mui-card-img-bottom"],
            )
            card.append(image_bottom)

        return card

    @staticmethod
    def split_content(content: StringList, offset: int) -> CardContent:
        """Split the content into header, body and footer."""
        header_index, footer_index, header, footer = None, None, None, None
        body_offset = offset
        for index, line in enumerate(content):
            # match the first occurrence of a header regex
            if (header_index is None) and REGEX_HEADER.match(line):
                header_index = index
            # match the final occurrence of a footer regex
            if REGEX_FOOTER.match(line):
                footer_index = index
        if header_index is not None:
            header = (offset, content[:header_index])
            body_offset += header_index + 1
        if footer_index is not None:
            footer = (offset + footer_index + 1, content[footer_index + 1 :])
        body = (
            body_offset,
            content[
                (header_index + 1 if header_index is not None else None) : footer_index
            ],
        )
        return CardContent(body, header, footer)

    @classmethod
    def _create_component(
        cls,
        inst: SphinxDirective,
        name: str,
        options: dict,
        offset: int,
        content: StringList,
    ) -> nodes.container:
        """Create the header, body, or footer."""
        component = create_component(
            f"card-{name}", [f"mui-card-{name}"] + options.get(f"class-{name}", [])
        )
        inst.set_source_info(component)  # TODO set proper lines
        inst.state.nested_parse(content, offset, component)
        cls.add_card_child_classes(component)
        return component

    @staticmethod
    def add_card_child_classes(node):
        """Add classes to specific child nodes."""
        for para in node.traverse(nodes.paragraph):
            para["classes"] = ([] if "classes" not in para else para["classes"]) + [
                "mui-card-text"
            ]
        for title in node.traverse(nodes.title):
            title["classes"] = ([] if "classes" not in title else title["classes"]) + [
                "mui-card-title"
            ]