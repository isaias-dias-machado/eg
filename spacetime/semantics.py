"""Name resolution and validation: ``Ast`` -> ``RefinedAst``.

This is the last compiler stage. It checks every identifier against its
declaration, rejects duplicate send-event names, resolves each receive to
the send event it refers to, and numbers events by source order.

Failure modes:
    Every user error is reported as a
    :class:`spacetime.errors.SemanticError` carrying the source location of
    the offending identifier. The input tree is never mutated.
"""

from .ast import (
    Ast,
    HistoryRefined,
    Ident,
    RecvEvent,
    RecvEventRefined,
    RefinedAst,
    SendEvent,
    SendEventRefined,
)
from .errors import SemanticError


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


def create_refined_ast(ast: Ast) -> RefinedAst:
    """Resolve and validate a raw ``Ast``.

    Works in three passes:

    1. collect declared process names and message payloads;
    2. collect all send-event names, so a receive that refers to a later
       event can be reported differently from one that refers to no event
       at all;
    3. walk the history in source order, validating each event and building
       its refined counterpart.

    Invariants of the result:
        - event order and ``temporal_pos`` match source order, starting at
          0;
        - every process and message reference denotes a declaration;
        - every receive refers to an earlier send event and lists only that
          event's recipients;
        - send-event names and message declarations are inlined and
          dropped.

    Failure modes:
        Raises :class:`SemanticError` for duplicate event names, undeclared
        messages or processes, undeclared send events, receives that refer
        to a later send event, and receives from non-recipients. Raises
        :class:`TypeError` if the history holds a node that is neither
        ``SendEvent`` nor ``RecvEvent`` (a builder/grammar drift, i.e. an
        internal invariant violation).
    """
    process_names = {process.name for process in ast.process_declarations}
    message_by_name = {
        declaration.name.name: declaration.value
        for declaration in ast.message_declarations
    }

    # First pass: index every send by its event name. This must happen
    # before resolution so that "declared later" and "never declared" are
    # distinguishable errors for receives.
    all_send_names: dict[str, SendEvent] = {}
    for event in ast.history.events:
        if isinstance(event, SendEvent):
            name = event.name.name
            if name in all_send_names:
                raise SemanticError(
                    f"duplicate event declaration: '{name}'",
                    location=event.name.location,
                )
            all_send_names[name] = event

    # Sends already seen by the current walk. A receive may only point at
    # one of these, which enforces causality (a receive cannot precede its
    # send in history order).
    resolved_sends: dict[str, SendEventRefined] = {}
    refined_events: list[SendEventRefined | RecvEventRefined] = []

    for temporal_pos, event in enumerate(ast.history.events):
        match event:
            case SendEvent():
                message_name = event.message_id.name
                if message_name not in message_by_name:
                    raise SemanticError(
                        f"undeclared message: '{message_name}'",
                        location=event.message_id.location,
                    )

                _validate_process(event.process_from_id, process_names)
                for recipient in event.processes_to_ids:
                    _validate_process(recipient, process_names)

                # The message name is replaced by its payload; the event
                # name is dropped from the refined node on purpose.
                refined_event = SendEventRefined(
                    temporal_pos=temporal_pos,
                    message=message_by_name[message_name],
                    process_from_id=event.process_from_id.name,
                    processes_to_ids=[
                        recipient.name for recipient in event.processes_to_ids
                    ],
                )
                resolved_sends[event.name.name] = refined_event
                refined_events.append(refined_event)

            case RecvEvent():
                send_name = event.send_event_ref.name
                if send_name not in all_send_names:
                    raise SemanticError(
                        f"undeclared send event: '{send_name}'",
                        location=event.send_event_ref.location,
                    )
                # Known event, but not yet walked: it appears later in the
                # history, which would reverse the intended causality.
                if send_name not in resolved_sends:
                    raise SemanticError(
                        f"receive refers to send event declared later: '{send_name}'",
                        location=event.send_event_ref.location,
                    )

                for process in event.process_ids:
                    _validate_process(process, process_names)

                related_send = resolved_sends[send_name]
                for process in event.process_ids:
                    if process.name not in related_send.processes_to_ids:
                        raise SemanticError(
                            f"process '{process.name}' is not a recipient of "
                            f"send event '{send_name}'",
                            location=process.location,
                        )

                refined_events.append(
                    RecvEventRefined(
                        temporal_pos=temporal_pos,
                        related_send_event=related_send,
                        process_ids=[process.name for process in event.process_ids],
                    )
                )

            case _:
                raise TypeError(f"unexpected event: {event!r}")

    return RefinedAst(
        process_declarations=[
            process.name for process in ast.process_declarations
        ],
        history=HistoryRefined(events=refined_events),
    )
