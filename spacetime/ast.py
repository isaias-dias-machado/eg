from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLocation:
    line: int
    column: int


@dataclass(frozen=True)
class Ident:
    name: str
    location: SourceLocation


@dataclass(frozen=True)
class MessageDeclaration:
    name: Ident
    value: str


@dataclass(frozen=True)
class SendEvent:
    name: Ident
    message_id: Ident
    process_from_id: Ident
    processes_to_ids: list[Ident]


@dataclass(frozen=True)
class RecvEvent:
    send_event_ref: Ident
    process_ids: list[Ident]


@dataclass(frozen=True)
class History:
    events: list[SendEvent | RecvEvent]


@dataclass(frozen=True)
class Ast:
    process_declarations: list[Ident]
    message_declarations: list[MessageDeclaration]
    history: History


@dataclass(frozen=True)
class SendEventRefined:
    temporal_pos: int
    message: str
    process_from_id: str
    processes_to_ids: list[str]


@dataclass(frozen=True)
class RecvEventRefined:
    temporal_pos: int
    related_send_event: SendEventRefined
    process_ids: list[str]


@dataclass(frozen=True)
class HistoryRefined:
    events: list[SendEventRefined | RecvEventRefined]


@dataclass(frozen=True)
class RefinedAst:
    process_declarations: list[str]
    history: HistoryRefined
