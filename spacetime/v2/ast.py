"""Syntax tree data structures for the v2 Space-Time DSL.

Two tree shapes (``Ast`` and ``RefinedAst``), with one twist: the
history is a *tree* of items instead of a flat event list, because the
``Maybe`` block groups several history items into one optional
branch.

``Ast``
    Raw output of :mod:`spacetime.v2.builder`. Identifiers keep the
    :class:`SourceLocation` needed to report errors, and message payloads
    stay attached to their declarations.

``RefinedAst``
    Output of :mod:`spacetime.v2.resolve`. Names are resolved to plain
    strings, event names and message declarations are inlined into the
    events that use them, and every event has a temporal position.

All nodes are frozen dataclasses: building a tree never mutates an existing
node, and callers may treat nodes as immutable values. Lists are still
mutable by Python semantics; treat them as read-only after construction.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLocation:
    """A 1-based position in the DSL source.

    Invariants:
        ``line >= 1`` and ``column >= 1``. The builder falls back to
        ``SourceLocation(1, 1)`` when Lark did not attach position metadata
        to a rule, so a location may be approximate but is never absent.

    Failure modes:
        None: this is a passive value and performs no validation.
    """

    line: int
    column: int


@dataclass(frozen=True)
class Ident:
    """A source identifier together with the position where it appeared.

    Used for process names, message names and values, event names, and
    references between them.

    Invariants:
        ``name`` matches the grammar's ``IDENTIFIER`` token: it starts with
        a lowercase ASCII letter and continues with letters, digits, or
        underscores.

    Failure modes:
        None. Whether the name is declared is checked in resolve.
    """

    name: str
    location: SourceLocation


@dataclass(frozen=True)
class MessageDeclaration:
    """A ``name := "value"`` entry in a ``Messages`` block.

    Invariants:
        ``value`` is the payload text with the surrounding double quotes
        removed. No escape processing is applied, so it may contain any
        character the grammar allows between the quotes (no unescaped
        double quote and no line terminator).

    Failure modes:
        Duplicate names are rejected while building the block, with a
        :class:`spacetime.errors.SemanticError` at the second declaration.
    """

    name: Ident
    value: str


@dataclass(frozen=True)
class SendEvent:
    """A named send event from a ``History`` block.

    ``name`` is the event identifier bound with ``:=`` (for example
    ``m1``), not the message name. ``processes_to_ids`` may list several
    recipients, which models a multicast as a single event.

    Invariants:
        - ``name`` is unique among send events; duplicates are rejected in
          resolve.
        - ``processes_to_ids`` is non-empty because the grammar requires at
          least one recipient.
        - Referenced message and process names may still be undeclared at
          this stage.

    Failure modes:
        No validation here. :func:`spacetime.v2.resolve.create_refined_ast`
        raises :class:`spacetime.errors.SemanticError` for undeclared
        messages or processes and for duplicate event names.
    """

    name: Ident
    message_id: Ident
    process_from_id: Ident
    processes_to_ids: list[Ident]


@dataclass(frozen=True)
class RecvEvent:
    """A ``Recv(event) :: p, q`` entry in a ``History`` block.

    A multicast receive stays one event; every listed process is recorded
    in ``process_ids``.

    Invariants:
        - ``send_event_ref`` names a send event that appears *earlier* in
          the flattened history; forward references are rejected.
        - ``process_ids`` is non-empty and every entry names a declared
          process. Entries need not be recipients of the referenced send:
          v2 drops v1's recipient-membership check, and a receive at a
          non-recipient just means the message was not received there.

    Failure modes:
        Declaration order and recipient membership are validated in
        :func:`spacetime.v2.resolve.create_refined_ast`.
    """

    send_event_ref: Ident
    process_ids: list[Ident]


@dataclass(frozen=True)
class MaybeBlock:
    """A ``Maybe { ... }`` group of history items.

    The block marks its items as one optional branch of the history: on any
    execution path, either all of them happen (in order) or none of them
    does. Blocks nest, because ``items`` may contain further ``MaybeBlock``
    nodes.

    Invariants:
        - ``items`` preserves source order.
        - An empty list is valid and denotes a branch that does nothing.

    Failure modes:
        None at this layer; cross-item rules live in resolve.
    """

    items: list["HistoryItem"]
    location: SourceLocation


HistoryItem = SendEvent | RecvEvent | MaybeBlock
"""One entry of a ``History`` block: an event or a ``Maybe`` group."""


@dataclass(frozen=True)
class History:
    """The ordered item list of a ``History`` block.

    Invariants:
        - Order is source order, the only notion of time in the DSL; there
          is no explicit timestamp.
        - An empty list is valid and represents a program without events.

    Failure modes:
        None at this layer; cross-item rules live in resolve.
    """

    items: list[HistoryItem]


@dataclass(frozen=True)
class Ast:
    """Raw syntax tree produced by :func:`spacetime.v2.builder.build_ast`.

    Invariants:
        - ``process_declarations`` preserves source order and contains no
          duplicate names.
        - ``message_declarations`` preserves source order and contains no
          duplicate names.
        - Absent blocks become empty lists, so an empty program is a valid
          ``Ast`` with no declarations and no history.

    Failure modes:
        Constructing an ``Ast`` directly performs no checks; violations are
        only detected when resolve runs.
    """

    process_declarations: list[Ident]
    message_declarations: list[MessageDeclaration]
    history: History


@dataclass(frozen=True)
class SendEventRefined:
    """A send event after name resolution.

    ``message`` is the payload string from the matching declaration rather
    than the message name. The event's own name is intentionally dropped.

    Invariants:
        - ``temporal_pos`` is the 0-based index of the event in the
          *flattened* source-order event sequence (``Maybe`` blocks are
          walked depth-first), not a position inside its parent block.
        - ``process_from_id`` and every entry in ``processes_to_ids`` name
          declared processes.
        - ``processes_to_ids`` is non-empty and may repeat a process if the
          source did.

    Failure modes:
        None; the instance only exists after semantic validation succeeded.
    """

    temporal_pos: int
    message: str
    message_type: int
    process_from_id: str
    processes_to_ids: list[str]


@dataclass(frozen=True)
class RecvEventRefined:
    """A receive event after name resolution.

    Invariants:
        - ``related_send_event`` is the same ``SendEventRefined`` instance
          stored earlier in the refined history.
        - ``temporal_pos`` is greater than the related send's position.
        - ``process_ids`` is a non-empty list of declared processes; it may
          name non-recipients of the related send (the message was then not
          received there).

    Failure modes:
        None; the instance only exists after semantic validation succeeded.
    """

    temporal_pos: int
    related_send_event: SendEventRefined
    process_ids: list[str]


@dataclass(frozen=True)
class MaybeBlockRefined:
    """A resolved ``Maybe`` group.

    Keeps the branch structure of the raw tree; carries no name and no
    position of its own. The events inside keep their global
    ``temporal_pos``.

    Invariants:
        - ``items`` preserves source order and may contain further
          ``MaybeBlockRefined`` nodes.

    Failure modes:
        None; the instance only exists after semantic validation succeeded.
    """

    items: list["RefinedHistoryItem"]


RefinedHistoryItem = SendEventRefined | RecvEventRefined | MaybeBlockRefined
"""One entry of a refined history: an event or a ``Maybe`` group."""


@dataclass(frozen=True)
class HistoryRefined:
    """A resolved history whose items preserve the ``Maybe`` tree shape."""

    items: list[RefinedHistoryItem]


@dataclass(frozen=True)
class RefinedAst:
    """Fully resolved program returned by
    :func:`spacetime.v2.compiler.compile_source`.

    Message declarations are not kept: payloads are inlined in
    ``SendEventRefined.message``.

    Invariants:
        - ``process_declarations`` preserves source order as plain names.
        - ``history.items`` preserves source order; events inside carry a
          global ``temporal_pos`` over the flattened event sequence.

    Failure modes:
        None; constructing one directly is not validated.
    """

    process_declarations: list[str]
    history: HistoryRefined
