"""Name resolution and validation: ``Ast`` -> ``RefinedAst`` (v2).

Same checks as v1 :mod:`spacetime.semantics`, walked over the item *tree*:
every identifier is checked against its declaration, duplicate send-event
names are rejected, each receive is resolved to the send event it refers to,
and events are numbered by their position in the flattened source-order
event sequence. One v1 check is dropped: recipient membership. A ``Recv``
may name any declared process; at a non-recipient it just means the message
was not received there.

Known limitation (to be tightened by the CFG walk over the refined tree):
causality is checked linearly over the flattened order, so a ``Recv``
outside a ``Maybe`` whose ``Send`` is inside it is still accepted here. On
the CFG, that receive is only legal on paths where the send happened.

Failure modes:
    Every user error is reported as a
    :class:`spacetime.errors.SemanticError` carrying the source location of
    the offending identifier. The input tree is never mutated.
"""

from ..errors import SemanticError
from .ast import (
    Ast,
    HistoryRefined,
    Ident,
    MaybeBlock,
    MaybeBlockRefined,
    RecvEvent,
    RecvEventRefined,
    RefinedAst,
    RefinedHistoryItem,
    SendEvent,
    SendEventRefined,
)


def _validate_process(process: Ident, process_names: set[str]) -> None:
    """Ensure ``process`` was declared in the ``Processes`` block.

    Failure modes:
        Raises :class:`SemanticError` at ``process.location`` when the name
        is unknown.
    """
    if process.name not in process_names:
        raise SemanticError(
            f"undeclared process: '{process.name}'",
            location=process.location,
        )


def _resolve_items(
    items: list,
    process_names: set[str],
    message_by_name: dict[str, str],
    resolved_sends: dict[str, SendEventRefined],
    out: list[RefinedHistoryItem],
    pos: int,
) -> int:
    """Resolve ``items`` in source order, appending refined nodes to ``out``.

    ``pos`` is the next global temporal position; the flattened walk means
    an event inside a ``Maybe`` gets the same kind of position as a top-level
    event. Returns the position after the last resolved event.

    Failure modes:
        Same as :func:`create_refined_ast`; ``TypeError`` for an item that
        is neither event nor ``MaybeBlock`` (a builder/grammar drift).
    """
    for item in items:
        match item:
            case SendEvent():
                name = item.name.name
                if name in resolved_sends:
                    raise SemanticError(
                        f"duplicate event declaration: '{name}'",
                        location=item.name.location,
                    )

                message_name = item.message_id.name
                if message_name not in message_by_name:
                    raise SemanticError(
                        f"undeclared message: '{message_name}'",
                        location=item.message_id.location,
                    )

                _validate_process(item.process_from_id, process_names)
                for recipient in item.processes_to_ids:
                    _validate_process(recipient, process_names)

                # The message name is replaced by its payload; the event
                # name is dropped from the refined node on purpose.
                refined_event = SendEventRefined(
                    temporal_pos=pos,
                    message=message_by_name[message_name],
                    message_type=1,
                    process_from_id=item.process_from_id.name,
                    processes_to_ids=[
                        recipient.name for recipient in item.processes_to_ids
                    ],
                )
                resolved_sends[name] = refined_event
                out.append(refined_event)
                pos += 1

            case RecvEvent():
                send_name = item.send_event_ref.name
                if send_name not in resolved_sends:
                    raise SemanticError(
                        f"undeclared send event: '{send_name}'",
                        location=item.send_event_ref.location,
                    )

                for process in item.process_ids:
                    _validate_process(process, process_names)

                related_send = resolved_sends[send_name]
                # v2 drops v1's recipient-membership check: a Recv may name
                # any declared process, and at a non-recipient it just means
                # the message was not received there.
                out.append(
                    RecvEventRefined(
                        temporal_pos=pos,
                        related_send_event=related_send,
                        process_ids=[process.name for process in item.process_ids],
                    )
                )
                pos += 1

            case MaybeBlock():
                inner: list[RefinedHistoryItem] = []
                pos = _resolve_items(
                    item.items,
                    process_names,
                    message_by_name,
                    resolved_sends,
                    inner,
                    pos,
                )
                out.append(MaybeBlockRefined(items=inner))

            case _:
                raise TypeError(f"unexpected history item: {item!r}")

    return pos


def create_refined_ast(ast: Ast) -> RefinedAst:
    """Resolve and validate a raw v2 ``Ast``.

    Works in two passes:

    1. collect declared process names and message payloads;
    2. walk the history item tree in source order (depth-first through
       ``Maybe`` blocks), validating each event and building its refined
       counterpart.

    Invariants of the result:
        - the item tree preserves source order and the ``Maybe`` structure;
        - ``temporal_pos`` numbers events by the flattened source order,
          starting at 0;
        - every process and message reference denotes a declaration;
        - every receive refers to an earlier send event and lists declared
          processes (recipients or not — see below);
        - send-event names and message declarations are inlined and dropped.

    Failure modes:
        Raises :class:`SemanticError` for duplicate event names, undeclared
        messages or processes, and undeclared send events (a receive may
        only refer to a send that precedes it in the flattened order).
        Raises ``TypeError`` if the history holds a node that is neither an
        event nor a ``MaybeBlock`` (a builder/grammar drift, i.e. an internal
        invariant violation).
    """
    process_names = {process.name for process in ast.process_declarations}
    message_by_name = {
        declaration.name.name: declaration.value
        for declaration in ast.message_declarations
    }

    # Sends already seen by the current walk. A receive may only point at
    # one of these, which enforces causality in flattened history order.
    resolved_sends: dict[str, SendEventRefined] = {}
    refined_items: list[RefinedHistoryItem] = []

    _resolve_items(
        ast.history.items,
        process_names,
        message_by_name,
        resolved_sends,
        refined_items,
        0,
    )

    return RefinedAst(
        process_declarations=[
            process.name for process in ast.process_declarations
        ],
        history=HistoryRefined(items=refined_items),
    )
