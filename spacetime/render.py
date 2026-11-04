"""Human-readable rendering of compiler output.

Formatting is intended for debugging and CLI output only: the layout is not
stable and cannot be parsed back into a tree.

The ast/refined-ast stages are rendered in a Lark-pretty style:
  - 2-space indentation per depth level
  - Node names on their own line (like Lark rule names)
  - Leaf values as  `label<TAB>value`  (Lark's collapsed single-token style)
  - Ident dataclasses collapse to their name; SourceLocation is omitted.
  - History/HistoryRefined wrappers collapse directly to their events.
"""

import re
from dataclasses import fields, is_dataclass

from .ast import Ast, History, HistoryRefined, Ident, RefinedAst


def _snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    # Insert underscore before capital letters that follow lowercase letters
    s = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    # Insert underscore before capital letters that are followed by lowercase
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    return s.lower()


def _format_dataclass(obj, label: str | None, depth: int) -> list[str]:
    """Format a dataclass instance as indented lines.
    
    If label is None, the node label is derived from the class name.
    Special cases:
      - Ident: collapses to `label\tname` (locations omitted)
      - History/HistoryRefined: collapse to their events directly
    """
    indent = "  " * depth
    cls = type(obj).__name__
    actual_label = label if label is not None else _snake_case(cls)

    # Ident: collapse to single line with name only
    if cls == "Ident":
        return [f"{indent}{actual_label}\t{obj.name}"]

    # History/HistoryRefined: single-field wrappers, collapse to events
    field_list = fields(obj)
    if len(field_list) == 1 and field_list[0].name == "events":
        lines = [f"{indent}{actual_label}"]
        events = getattr(obj, "events")
        for event in events:
            lines.extend(_format_dataclass(event, None, depth + 1))
        return lines

    # General dataclass: print label, then each field
    lines = [f"{indent}{actual_label}"]
    for field in field_list:
        field_val = getattr(obj, field.name)
        lines.extend(_format_field(field.name, field_val, depth + 1))
    return lines


def _format_field(name: str, value, depth: int) -> list[str]:
    """Format a single dataclass field."""
    return _format_value(value, depth, name)


def _format_value(value, depth: int, label: str) -> list[str]:
    """Format a value (field or list element) at the given depth with a label."""
    indent = "  " * depth

    # Lists: print the label, then each element
    if isinstance(value, list):
        lines = [f"{indent}{label}"]
        for item in value:
            if isinstance(item, Ident):
                # Ident in list: render as "  ident\tname"
                lines.append(f"{indent}  ident\t{item.name}")
            elif is_dataclass(item):
                # Dataclass element: render as tree with its class label
                lines.extend(_format_dataclass(item, None, depth + 1))
            else:
                # Scalar element in list: bare value (Lark multi-token style)
                lines.append(f"{indent}  {item}")
        return lines

    # Ident: collapse to label\tname
    if isinstance(value, Ident):
        return [f"{indent}{label}\t{value.name}"]

    # Dataclass: recurse
    if is_dataclass(value):
        return _format_dataclass(value, label, depth)

    # Scalar (str, int, etc.): label\tvalue
    return [f"{indent}{label}\t{value}"]


def format_parse_tree(tree) -> str:
    """Render a Lark parse tree as indented text.

    This is the stage-1 output of the compiler. Lark's ``pretty`` layout is
    used unchanged, so it depends on the grammar's rule names.
    """
    return tree.pretty()


def format_ast(ast: Ast) -> str:
    """Render a raw ``Ast`` as indented text in Lark-pretty style.

    - Dataclass names become snake_case node labels.
    - Ident nodes collapse to their name (source locations are omitted).
    - History/HistoryRefined collapse directly to their events.
    """
    return "\n".join(_format_dataclass(ast, None, 0))


def format_refined_ast(ast: RefinedAst) -> str:
    """Render a ``RefinedAst`` as indented text in Lark-pretty style.

    Message declarations are omitted because their payloads are already
    inlined in the send events. Ident nodes do not appear because all
    identifiers have been resolved to plain strings.
    """
    return "\n".join(_format_dataclass(ast, None, 0))
