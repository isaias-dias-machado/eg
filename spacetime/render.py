"""Human-readable rendering of compiler output.

Formatting is intended for debugging and CLI output only: the layout is not
stable and cannot be parsed back into a tree.
"""

import pprint

from .ast import Ast, RefinedAst


def format_ast(ast: Ast) -> str:
    """Render a raw ``Ast`` as indented text.

    Events are printed with ``pprint`` so every dataclass field, including
    source locations, remains visible.
    """
    lines = ["Ast", "\tprocess_declarations"]
    lines.extend(f"\t\t{declaration.name}" for declaration in ast.process_declarations)

    lines.append("\tmessage_declarations")
    lines.extend(
        f"\t\t{declaration.name.name}: {declaration.value}"
        for declaration in ast.message_declarations
    )

    lines.append("\thistory")
    lines.append(f"\t\tevent_number {len(ast.history.events)}")
    for event in ast.history.events:
        lines.append(f"\t\t{pprint.pformat(event)}")

    return "\n".join(lines)


def format_refined_ast(ast: RefinedAst) -> str:
    """Render a ``RefinedAst`` as indented text.

    Message declarations are omitted because their payloads are already
    inlined in the send events.
    """
    lines = ["Ast", "\tprocess_declarations"]
    lines.extend(f"\t\t{declaration}" for declaration in ast.process_declarations)

    lines.append("\thistory")
    lines.append(f"\t\tevent_number {len(ast.history.events)}")
    for event in ast.history.events:
        lines.append(f"\t\t{pprint.pformat(event)}")

    return "\n".join(lines)
