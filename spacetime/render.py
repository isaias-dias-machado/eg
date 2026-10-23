import pprint

from .ast import Ast, RefinedAst


def format_ast(ast: Ast) -> str:
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
    lines = ["Ast", "\tprocess_declarations"]
    lines.extend(f"\t\t{declaration}" for declaration in ast.process_declarations)

    lines.append("\thistory")
    lines.append(f"\t\tevent_number {len(ast.history.events)}")
    for event in ast.history.events:
        lines.append(f"\t\t{pprint.pformat(event)}")

    return "\n".join(lines)
