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
    if process.name not in process_names:
        raise SemanticError(
            f"undeclared process: '{process.name}'",
            location=process.location,
        )


def create_refined_ast(ast: Ast) -> RefinedAst:
    process_names = {process.name for process in ast.process_declarations}
    message_by_name = {
        declaration.name.name: declaration.value
        for declaration in ast.message_declarations
    }

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
