"""Grammar quality metrics for ``spacetime/grammar.lark`` (TP1, task 4).

Applies the CFG metrics of notebook PL_NB07 (Language and Grammar Quality,
section 7.2) to the project grammar. The metric code follows the notebook's
cells. The last section adds two recognition checks the notebook does not
cover: LALR(1) conflicts and Earley ambiguity on the valid examples.

Run from the repository root, optionally naming another Lark grammar to
measure instead (for example, a proposed variant)::

    python docs/metricas_gramatica.py [GRAMMAR.lark]
"""

import logging
import sys
from collections import Counter
from pathlib import Path

from lark import Lark, logger
from lark.exceptions import UnexpectedInput
from lark.load_grammar import GrammarBuilder

ROOT = Path(__file__).resolve().parent.parent
GRAMMAR_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "spacetime" / "grammar.lark"
EXAMPLES = sorted((ROOT / "tests" / "fixtures" / "valid").glob("*.st"))
EXAMPLES.append(ROOT / "example.txt")


def build_lalr(text):
    """Build an LALR(1) parser and return it with its shift/reduce conflicts.

    Lark resolves these conflicts as shift and only logs them at debug level,
    so they are collected from its logger while the parser is built.
    """
    conflicts = []

    class CollectConflicts(logging.Handler):
        def emit(self, record):
            if record.getMessage().startswith("Shift/Reduce conflict"):
                conflicts.append(record.args[0])

    saved_handlers, saved_level = logger.handlers, logger.level
    logger.handlers = [CollectConflicts()]
    logger.setLevel(logging.DEBUG)
    try:
        parser = Lark(text, parser="lalr")
    finally:
        logger.handlers = saved_handlers
        logger.setLevel(saved_level)
    return parser, conflicts


def reaches(successors, start, goal):
    """Whether ``goal`` is reachable from ``start`` in the dependency graph."""
    seen, stack = set(), [start]
    while stack:
        node = stack.pop()
        if node == goal:
            return True
        if node not in seen:
            seen.add(node)
            stack.extend(successors.get(node, ()))
    return False


grammar = GRAMMAR_PATH.read_text()
parser, conflicts = build_lalr(grammar)
rules = parser.rules

# Rules as written, before Lark expands EBNF operators into helper rules
builder = GrammarBuilder()
builder.load_grammar(grammar)
source_rules = {str(name): tree for name, _params, tree, _options in builder.build().rule_defs}

print("== Size metrics ==")

# Number of productions
n_productions = len(rules)

# Number of non-terminals and productions per non-terminal
productions_per_symbol = Counter(rule.origin.name for rule in rules)
n_nonterminals = len(productions_per_symbol)

# Number of terminals in the compiled grammar
n_terminals = len(parser.terminals)

# Length of each production's right-hand side
rhs_lengths = [len(rule.expansion) for rule in rules]

# Unitary productions: A -> B, where B is a non-terminal
n_unitary = sum(len(rule.expansion) == 1 and not rule.expansion[0].is_term for rule in rules)

# Directly recursive non-terminals
directly_recursive = {
    rule.origin.name
    for rule in rules
    if any(
        not symbol.is_term and symbol.name == rule.origin.name
        for symbol in rule.expansion
    )
}

# Distinct non-terminal dependencies: A -> B
edges = {
    (rule.origin.name, symbol.name)
    for rule in rules
    for symbol in rule.expansion
    if not symbol.is_term
}

nonterminals = {name for name in productions_per_symbol}

# Indirectly recursive non-terminals: a cycle through another non-terminal
successors = {n: {b for a, b in edges if a == n and b != n} for n in nonterminals}
indirectly_recursive = {
    n for n in nonterminals if any(reaches(successors, s, n) for s in successors[n])
}

# Imported sub-grammars
n_imports = sum(line.lstrip().startswith("%import") for line in grammar.splitlines())

print("Source rules (non-terminals as written):", len(source_rules))
print("Terminals:", n_terminals, "(ignored:", ", ".join(parser.ignore_tokens) + ")")
print("Non-terminals:", n_nonterminals)
print("Productions:", n_productions)
print("Unitary productions:", n_unitary)
print("Directly recursive non-terminals:", len(directly_recursive))
print("Indirectly recursive non-terminals:", len(indirectly_recursive))
print("Average RHS length:", round(sum(rhs_lengths) / len(rhs_lengths), 2))
print("Maximum RHS length:", max(rhs_lengths))
print("Average productions per non-terminal:", round(sum(productions_per_symbol.values()) / len(productions_per_symbol), 2))
print("Maximum productions per non-terminal:", max(productions_per_symbol.values()))
print("Imported sub-grammars:", n_imports)

in_degree = Counter(b for a, b in edges)
out_degree = Counter(a for a, b in edges)

print("Average in-degree:", round(sum(in_degree[n] for n in nonterminals) / len(nonterminals), 2))
print("Average out-degree:", round(sum(out_degree[n] for n in nonterminals) / len(nonterminals), 2))

# Access the generated LALR parse table (Lark internals)
parse_table = parser.parser.parser._parse_table

states = parse_table.states

print("LALR states:", len(states))
print("Action/goto table entries:", sum(len(actions) for actions in states.values()))

print("\n== Shape metrics ==")

# Recursion type of each directly recursive non-terminal
for name in sorted(directly_recursive):
    kinds = set()
    for rule in rules:
        if rule.origin.name == name and rule.expansion:
            if rule.expansion[0].name == name:
                kinds.add("left")
            if rule.expansion[-1].name == name:
                kinds.add("right")
    origin = "generated from EBNF" if name.startswith("__") else "written in the source"
    print(f"{name}: {'/'.join(sorted(kinds))} recursion, {origin}")

# Notation: a source rule is EBNF when it uses *, +, ? or [ ]
ebnf_rules = sorted(
    name
    for name, tree in source_rules.items()
    if any(subtree.data in ("expr", "maybe") for subtree in tree.iter_subtrees())
)
print("EBNF rules:", len(ebnf_rules), ebnf_rules)
print("Pure BNF rules:", len(source_rules) - len(ebnf_rules))

print("\n== Lexicographic metrics ==")

print("Non-terminal identifiers:", sorted(source_rules))

# Classify terminals by whether they accept varying values
for terminal in parser.terminals:
    kind = "flexible" if terminal.pattern.type == "re" else "fixed"
    print(f"{terminal.name} {terminal.pattern.value!r}: {kind}")

# Comment support: a valid program with a comment after a declaration
earley = Lark(grammar, parser="earley")
for comment in ("# note", "// note", "/* note */"):
    try:
        earley.parse(f"Processes {{\n  p {comment}\n}}\n")
        verdict = "accepted"
    except UnexpectedInput:
        verdict = "rejected"
    print(f"Comment {comment!r}: {verdict}")

print("\n== Recognition checks (beyond NB07) ==")

print("LALR(1) shift/reduce conflicts:", len(conflicts), dict(Counter(conflicts)))

explicit = Lark(grammar, parser="earley", ambiguity="explicit")
for path in EXAMPLES:
    text = path.read_text()
    n_ambiguous = len(list(explicit.parse(text).find_data("_ambig")))
    try:
        parser.parse(text)
        lalr = "accepted"
    except UnexpectedInput:
        lalr = "rejected"
    print(f"{path.name}: {n_ambiguous} ambiguous nodes (Earley), LALR {lalr}")
