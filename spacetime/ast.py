"""Syntax tree data structures for the Space-Time DSL.

The compiler works with two tree shapes:

``Ast``
    Raw output of :mod:`spacetime.builder`. Identifiers keep the
    :class:`SourceLocation` needed to report errors, and message payloads
    stay attached to their declarations.

``RefinedAst``
    Output of :mod:`spacetime.semantics`. Names are resolved to plain
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
        None. Whether the name is declared is checked in semantics.
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
          semantics.
        - ``processes_to_ids`` is non-empty because the grammar requires at
          least one recipient.
        - Referenced message and process names may still be undeclared at
          this stage.

    Failure modes:
        No validation here. :func:`spacetime.semantics.create_refined_ast`
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
          the same history; forward references are rejected.
        - ``process_ids`` is non-empty and every entry must be a recipient
          of the referenced send event.

    Failure modes:
        Declaration order and recipient membership are validated in
        :func:`spacetime.semantics.create_refined_ast`.
    """

    send_event_ref: Ident
    process_ids: list[Ident]


@dataclass(frozen=True)
class History:
    """The ordered event list of a ``History`` block.

    Invariants:
        - Order is source order, the only notion of time in the DSL; there
          is no explicit timestamp.
        - An empty list is valid and represents a program without events.

    Failure modes:
        None at this layer; cross-event rules live in semantics.
    """

    events: list[SendEvent | RecvEvent]


@dataclass(frozen=True)
class Ast:
    """Raw syntax tree produced by :func:`spacetime.builder.build_ast`.

    Invariants:
        - ``process_declarations`` preserves source order and contains no
          duplicate names.
        - ``message_declarations`` preserves source order and contains no
          duplicate names.
        - Absent blocks become empty lists, so an empty program is a valid
          ``Ast`` with no declarations and no history.

    Failure modes:
        Constructing an ``Ast`` directly performs no checks; violations are
        only detected when semantics runs.
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
        - ``temporal_pos`` is the 0-based index of the event in
          ``HistoryRefined.events``.
        - ``process_from_id`` and every entry in ``processes_to_ids`` name
          declared processes.
        - ``processes_to_ids`` is non-empty and may repeat a process if the
          source did.

    Failure modes:
        None; the instance only exists after semantic validation succeeded.
    """

    temporal_pos: int
    message: str
    process_from_id: str
    processes_to_ids: list[str]


@dataclass(frozen=True)
class RecvEventRefined:
    """A receive event after name resolution.

    Invariants:
        - ``related_send_event`` is the same ``SendEventRefined`` instance
          stored earlier in the refined history.
        - ``temporal_pos`` is greater than the related send's position.
        - ``process_ids`` is a non-empty subset of
          ``related_send_event.processes_to_ids``.

    Failure modes:
        None; the instance only exists after semantic validation succeeded.
    """

    temporal_pos: int
    related_send_event: SendEventRefined
    process_ids: list[str]


@dataclass(frozen=True)
class HistoryRefined:
    """A resolved history whose events are ordered by ``temporal_pos``."""

    events: list[SendEventRefined | RecvEventRefined]


@dataclass(frozen=True)
class RefinedAst:
    """Fully resolved program returned by
    :func:`spacetime.compiler.compile_source`.

    Message declarations are not kept: payloads are inlined in
    ``SendEventRefined.message``.

    Invariants:
        - ``process_declarations`` preserves source order as plain names.
        - ``history.events`` is ordered by ``temporal_pos``.

    Failure modes:
        None; constructing one directly is not validated.
    """

    process_declarations: list[str]
    history: HistoryRefined
