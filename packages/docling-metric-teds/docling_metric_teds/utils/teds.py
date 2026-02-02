#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: MIT
#
from collections import deque

from apted import APTED, Config
from apted.helpers import Tree
from Levenshtein import distance
from lxml import html


class CustomConfig(Config):
    @staticmethod
    def maximum(*sequences):
        """Get maximum possible value"""
        return max(map(len, sequences))

    def normalized_distance(self, *sequences):
        """Get distance from 0 to 1"""
        return float(distance.levenshtein(*sequences)) / self.maximum(*sequences)

    def rename(self, node1, node2):
        """Compares attributes of trees"""
        if (
            (node1.tag != node2.tag)
            or (node1.colspan != node2.colspan)
            or (node1.rowspan != node2.rowspan)
        ):
            return 1.0
        if node1.tag in ["td", "th"]:
            if node1.content or node2.content:
                return self.normalized_distance(node1.content, node2.content)
        return 0.0


class TableTree(Tree):
    def __init__(self, tag, colspan=None, rowspan=None, content=None, *children):
        self.tag = tag
        self.colspan = colspan
        self.rowspan = rowspan
        self.content = content
        self.children = list(children)

    def bracket(self):
        """Show tree using brackets notation"""
        if self.tag in ["td", "th"]:
            result = '"tag": %s, "colspan": %d, "rowspan": %d, "text": %s' % (
                self.tag,
                self.colspan,
                self.rowspan,
                self.content,
            )
        else:
            result = '"tag": %s' % self.tag
        for child in self.children:
            result += child.bracket()
        return "{{{}}}".format(result)

    @staticmethod
    def from_bracket(bracket_str):  # noqa
        """Parse tree from bracket notation string

        Args:
            bracket_str: String in bracket notation format, e.g.:
                {"tag": table{"tag": tbody{"tag": tr{"tag": td, "colspan": 1, "rowspan": 1, "text": []}}}}

        Returns:
            TableTree: Parsed tree structure
        """
        import ast
        import re

        def parse_node(s, pos):  # noqa
            """Recursively parse a node from bracket notation

            Args:
                s: The full bracket string
                pos: Current position in the string

            Returns:
                tuple: (parsed_node, new_position)
            """
            # Skip whitespace
            while pos < len(s) and s[pos].isspace():
                pos += 1

            # Expect opening {
            if pos >= len(s) or s[pos] != "{":
                raise ValueError(
                    f"Expected '{{' at position {pos}, found: {s[pos : pos + 10]}"
                )
            pos += 1

            # Parse the tag attribute
            tag_match = re.match(r'"tag":\s*(\w+)', s[pos:])
            if not tag_match:
                raise ValueError(f"Could not find tag at position {pos}")

            tag = tag_match.group(1)
            pos += tag_match.end()

            # Check if this is a td/th node by looking for colspan
            colspan = None
            rowspan = None
            content = None

            # Look ahead to see if we have colspan/rowspan (indicates td/th node)
            lookahead = s[pos : pos + 100]
            colspan_match = re.match(r',\s*"colspan":\s*(\d+)', lookahead)

            if colspan_match:
                # This is a td/th node
                pos += colspan_match.end()
                colspan = int(colspan_match.group(1))

                # Parse rowspan
                rowspan_match = re.match(r',\s*"rowspan":\s*(\d+)', s[pos:])
                if rowspan_match:
                    pos += rowspan_match.end()
                    rowspan = int(rowspan_match.group(1))

                # Parse text content
                text_match = re.match(r',\s*"text":\s*(\[.*?\])', s[pos:])
                if text_match:
                    pos += text_match.end()
                    try:
                        content = ast.literal_eval(text_match.group(1))
                    except (ValueError, SyntaxError):
                        content = []
                else:
                    content = []

                node = TableTree(tag, colspan, rowspan, content)
            else:
                # This is a structural node (table, tbody, tr, etc.)
                node = TableTree(tag, None, None, None)

            # Parse children
            while pos < len(s):
                # Skip whitespace
                while pos < len(s) and s[pos].isspace():
                    pos += 1

                if pos >= len(s):
                    raise ValueError("Unexpected end of string")

                # Check for closing brace
                if s[pos] == "}":
                    pos += 1
                    break

                # Check for child node
                if s[pos] == "{":
                    child, pos = parse_node(s, pos)
                    node.children.append(child)
                else:
                    # Skip any other characters (shouldn't happen in valid input)
                    pos += 1

            return node, pos

        # Parse the root node
        root, _ = parse_node(bracket_str, 0)
        return root


class TEDScorer:
    r"""
    Compute Tree-Edit-Distance Score on HTML tables with support for cell content
    """

    def __init__(self):
        self._tokens = []

    def teds(self, gt_table: html, pred_table: html, structure_only: bool) -> float:
        r"""
        Compute the tree-edit-distance score TEDS
        TEDS is a float between [0, 1] where 0 is the worst and 1 is the best
        """
        n_nodes_pred = len(pred_table.xpath(".//*"))
        n_nodes_gt = len(gt_table.xpath(".//*"))

        # Convert the html objects into APTED trees
        tree_pred: TableTree = self.html_to_table_tree(
            pred_table, convert_cell=not structure_only
        )
        tree_gt: TableTree = self.html_to_table_tree(
            gt_table, convert_cell=not structure_only
        )

        n_nodes = max(n_nodes_pred, n_nodes_gt)
        distance = APTED(tree_pred, tree_gt, CustomConfig()).compute_edit_distance()
        teds = 1.0 - (float(distance) / n_nodes)
        return teds

    def _tokenize(self, node: html):
        r"""
        Tokenizes table cells
        """
        self._tokens.append(f"<{node.tag}")
        if node.text is not None:
            self._tokens += list(node.text)
        for n in node.getchildren():
            self._tokenize(n)
        if node.tag != "unk":
            self._tokens.append(f"</{node.tag}>")
        if (node.tag not in ["td", "th"]) and node.tail is not None:
            self._tokens += list(node.tail)

    def html_to_table_tree(
        self, node: html, convert_cell: bool = False, parent: html = None
    ) -> TableTree:
        r"""
        Converts HTML tree to the bracket notation for APTED
        """
        new_node: TableTree
        if node.tag in ["td", "th"]:
            # Normalize the tag to td, otherwise the comparison in APTED causes mismatch
            # TODO: Make this normalization configurable.
            node.tag = "td"
            if convert_cell:
                self._tokens = []
                self._tokenize(node)
                cell = self._tokens[1:-1].copy()
            else:
                cell = []
            new_node = TableTree(
                node.tag,
                int(node.attrib.get("colspan", "1")),
                int(node.attrib.get("rowspan", "1")),
                cell,
                *deque(),
            )
        else:
            new_node = TableTree(node.tag, None, None, None, *deque())
        if parent is not None:
            parent.children.append(new_node)
        if node.tag not in ["td", "th"]:
            for n in node.getchildren():
                self.html_to_table_tree(n, convert_cell, new_node)
        # if parent is None:
        #     return new_node
        return new_node

    def html_to_bracket(self, html_str: str, structure_only: bool = False) -> str:
        r"""
        Convert html to bracket format
        """
        html_obj = html.fromstring(html_str)
        table_tree: TableTree = self.html_to_table_tree(
            html_obj, convert_cell=not structure_only
        )
        bracket: str = table_tree.bracket()
        return bracket
