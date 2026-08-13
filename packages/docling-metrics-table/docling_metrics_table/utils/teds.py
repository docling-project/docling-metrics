from collections import deque

from apted import APTED, Config
from apted.helpers import Tree
from lxml import html
from rapidfuzz.distance import Levenshtein


class CustomConfig(Config):
    @staticmethod
    def maximum(*sequences):
        """Get maximum possible value"""
        return max(map(len, sequences))

    def normalized_distance(self, *sequences):
        """Get distance from 0 to 1"""
        return float(Levenshtein.distance(*sequences)) / self.maximum(*sequences)

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


# The bracket notation uses {} as structure elements, so a label that contains them must escape
# them as \{ and \}, and the escape character itself as \\.
_LABEL_ESCAPE = str.maketrans({"\\": "\\\\", "{": r"\{", "}": r"\}"})


def _unescape_label(label: str) -> str:
    r"""Inverse of _LABEL_ESCAPE: turn \\ back into \, and \{ / \} back into { / }."""
    out: list[str] = []
    index = 0
    while index < len(label):
        char = label[index]
        if char == "\\" and index + 1 < len(label) and label[index + 1] in "\\{}":
            out.append(label[index + 1])
            index += 2
        else:
            out.append(char)
            index += 1
    return "".join(out)


class TableTree(Tree):
    def __init__(self, tag, colspan=None, rowspan=None, content=None, *children):
        self.tag = tag
        self.colspan = colspan
        self.rowspan = rowspan
        self.content = content
        self.children = list(children)

    def _label(self):
        """The escaped label of this node alone, without its children.

        The escaping covers the node's own label only. Escaping the concatenated children
        too would destroy the structure brackets they legitimately contain.
        """
        if self.tag in ["td", "th"]:
            result = (
                f'"tag": {self.tag}, "colspan": {self.colspan}, '
                f'"rowspan": {self.rowspan}, "text": {self.content}'
            )
        else:
            result = f'"tag": {self.tag}'
        return result.translate(_LABEL_ESCAPE)

    def bracket(self):
        """Show tree using brackets notation"""
        # Iterative post-order walk. A stack entry is either a node still to expand or a
        # literal string to emit; pushing the closer before the children makes it pop after
        # them, which is what the recursive version got from the call stack.
        out: list[str] = []
        stack: list = [self]
        while stack:
            item = stack.pop()
            if isinstance(item, str):
                out.append(item)
                continue
            out.append("{" + item._label())
            stack.append("}")
            stack.extend(reversed(item.children))
        return "".join(out)

    @staticmethod
    def from_bracket(bracket_str):
        """Parse tree from bracket notation string

        Args:
            bracket_str: String in bracket notation format, e.g.:
                {"tag": table{"tag": tbody{"tag": tr{"tag": td, "colspan": 1, "rowspan": 1, "text": []}}}}

        Returns:
            TableTree: Parsed tree structure
        """
        import ast
        import re

        def parse_header(s, pos):
            """Parse a single node's opening brace and attributes, without its children.

            Args:
                s: The full bracket string
                pos: Position of the node's opening brace

            Returns:
                tuple: (parsed_node, position just after the attributes)
            """
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

                # Parse text content. The writer escapes \, { and } in the label, so the
                # escapes have to come off before the group is a valid Python literal.
                text_match = re.match(r',\s*"text":\s*(\[.*?\])', s[pos:])
                if text_match:
                    pos += text_match.end()
                    try:
                        content = ast.literal_eval(_unescape_label(text_match.group(1)))
                    except (ValueError, SyntaxError):
                        content = []
                else:
                    content = []

                node = TableTree(tag, colspan, rowspan, content)
            else:
                # This is a structural node (table, tbody, tr, etc.)
                node = TableTree(tag, None, None, None)

            return node, pos

        # Iterative walk over the string, keeping the currently open nodes on a stack. The
        # recursive version used the call stack for exactly this.
        s = bracket_str
        root = None
        stack: list[TableTree] = []
        pos = 0

        while pos < len(s):
            # Skip whitespace
            while pos < len(s) and s[pos].isspace():
                pos += 1
            if pos >= len(s):
                break

            # An escaped brace belongs to a label, not to the structure. Step over both
            # characters so it is never mistaken for a node boundary.
            if s[pos] == "\\" and pos + 1 < len(s) and s[pos + 1] in "\\{}":
                pos += 2
            elif s[pos] == "}":
                if not stack:
                    raise ValueError(f"Unbalanced '}}' at position {pos}")
                stack.pop()
                pos += 1
            elif s[pos] == "{":
                node, pos = parse_header(s, pos)
                if stack:
                    stack[-1].children.append(node)
                elif root is None:
                    root = node
                else:
                    raise ValueError(f"More than one root at position {pos}")
                stack.append(node)
            else:
                # Skip any other characters (shouldn't happen in valid input)
                pos += 1

        if root is None:
            raise ValueError("No root node found")
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

        # Check against empty table tags to prevent division by zero
        if n_nodes <= 0:
            raise ValueError("Empty tree: both tables have no nodes")

        distance = APTED(tree_pred, tree_gt, CustomConfig()).compute_edit_distance()
        teds = 1.0 - (float(distance) / n_nodes)
        return teds

    def _tokenize(self, node: html):
        r"""
        Tokenizes table cells

        Iterative pre/post-order walk. A stack entry is (element, closing): the closing entry
        is pushed before the children so that it pops after them, carrying the work the
        recursive version did on the way back up.
        """
        stack: list[tuple[html, bool]] = [(node, False)]
        while stack:
            element, closing = stack.pop()
            if closing:
                if element.tag != "unk":
                    self._tokens.append(f"</{element.tag}>")
                if (element.tag not in ["td", "th"]) and element.tail is not None:
                    self._tokens += list(element.tail)
                continue
            self._tokens.append(f"<{element.tag}")
            if element.text is not None:
                self._tokens += list(element.text)
            stack.append((element, True))
            stack.extend((child, False) for child in reversed(element.getchildren()))

    def _make_table_tree_node(self, node: html, convert_cell: bool) -> TableTree:
        r"""
        Builds the TableTree node for a single HTML element, without its children
        """
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
            return TableTree(
                node.tag,
                int(node.attrib.get("colspan", "1")),
                int(node.attrib.get("rowspan", "1")),
                cell,
                *deque(),
            )
        return TableTree(node.tag, None, None, None, *deque())

    def html_to_table_tree(
        self, node: html, convert_cell: bool = False, parent: html = None
    ) -> TableTree:
        r"""
        Converts HTML tree to the bracket notation for APTED

        Iterative pre-order walk over (element, parent) pairs. Children are pushed reversed so
        that LIFO ordering appends siblings in document order.
        """
        new_node: TableTree
        root: TableTree = None  # type: ignore[assignment]
        stack: list[tuple[html, TableTree]] = [(node, parent)]
        while stack:
            element, tree_parent = stack.pop()
            new_node = self._make_table_tree_node(element, convert_cell)
            if tree_parent is not None:
                tree_parent.children.append(new_node)
            if root is None:
                root = new_node
            if element.tag not in ["td", "th"]:
                stack.extend(
                    (child, new_node) for child in reversed(element.getchildren())
                )
        return root

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

    def bracket_to_html(self, bracket_str: str) -> str:
        r"""
        Convert bracket format to HTML while preserving only the table structure.
        """

        def build_html_node(node: TableTree) -> html.HtmlElement:
            # Iterative pre-order walk over (node, parent element) pairs. Appending an element
            # to its parent before its own children exist is fine, lxml elements are live.
            root_element: html.HtmlElement = None
            stack: list[tuple[TableTree, html.HtmlElement]] = [(node, None)]
            while stack:
                tree_node, parent_element = stack.pop()
                element = html.Element(tree_node.tag)
                if parent_element is None:
                    root_element = element
                else:
                    parent_element.append(element)
                if tree_node.tag in ["td", "th"]:
                    if tree_node.colspan and tree_node.colspan > 1:
                        element.set("colspan", str(tree_node.colspan))
                    if tree_node.rowspan and tree_node.rowspan > 1:
                        element.set("rowspan", str(tree_node.rowspan))
                    continue
                stack.extend((child, element) for child in reversed(tree_node.children))
            return root_element

        table_tree = TableTree.from_bracket(bracket_str)
        html_obj = build_html_node(table_tree)
        return html.tostring(html_obj, encoding="unicode")
