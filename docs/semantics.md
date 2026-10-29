# Semantic analysis specification

Normative description of what the Space-Time DSL checks after parsing, and
what the compiler must produce for a well-formed program. It describes the
compiler as implemented in `spacetime/builder.py`, `spacetime/semantics.py`,
and `spacetime/ast.py`.

- **Scope:** everything from the Lark parse tree to `RefinedAst`. Concrete
  syntax is defined by `spacetime/grammar.lark` and is out of scope here.
- **Keywords:** MUST / MUST NOT are requirements on a conforming
  implementation. The current Python implementation is the reference.
- **Conformance:** every rule below is exercised by `tests/test_semantics.py`
  and `tests/test_builder.py`; see [Rule-to-test map](#rule-to-test-map).

## 1. Pipeline position

| Stage | Name | Input | Output | Module |
|---|---|---|---|---|
| 1 | Parse | source text | Lark tree | `spacetime/parser.py` |
| 2 | Structural validation (build) | Lark tree | `Ast` | `spacetime/builder.py` |
| 3 | Semantic analysis (refine) | `Ast` | `RefinedAst` | `spacetime/semantics.py` |

Stage 2 and stage 3 both report user errors as
`spacetime.errors.SemanticError`. Syntax errors are `ParseError` and belong to
stage 1. Stage 3 MUST NOT mutate its input tree: nodes are frozen dataclasses.

## 2. Terminology

- **Block** — one of `Processes`, `Messages`, `History`.
- **Process declaration** — an identifier inside a `Processes` block.
- **Message declaration** — `name := "payload"` inside a `Messages` block.
  The payload is the text between the outer double quotes, with no escape
  processing.
- **Send event** — `m := Send(message) :: sender -> recipients` inside a
  `History` block. `m` is the **event name**; it is not a message name.
- **Receive event** — `Recv(event) :: targets` inside a `History` block.
  Receive events are anonymous: they bind no name.
- **History order** — the source order of events. It is the DSL's only
  notion of time; there are no timestamps.

## 3. Stage 2: well-formedness rules

These apply to the program as a whole and to individual blocks.

### W1. At most one block of each kind

A program MUST contain at most one `Processes`, one `Messages`, and one
`History` block. Blocks MAY appear in any order. Programs with no blocks at
all are valid.

Violation: `SemanticError("duplicate <Kind> block")`, located at the second
occurrence of that block kind.

### W2. Process names are unique

Within a `Processes` block, no name MAY be declared twice.

Violation: `SemanticError("duplicate process declaration: '<name>'")`, located
at the second declaration.

### W3. Message names are unique

Within a `Messages` block, no name MAY be declared twice. The payload is not
compared.

Violation: `SemanticError("duplicate message declaration: '<name>'")`, located
at the second declaration.

### W4. Missing and empty blocks

An absent block is equivalent to an empty block. `Processes {}`,
`Messages {}`, and `History {}` are valid, as is an entirely empty source.
An absent block yields empty declaration lists and an empty event list.

### W5. Order preservation, no cross-event checks

`process_declarations` and `message_declarations` MUST preserve source order.
History events MUST be recorded in source order. Stage 2 MUST NOT validate
references between events or to declarations: a receive may still name an
unknown or later event, and `Send`/`Recv` names may still be undeclared when
stage 3 begins.

## 4. Stage 3: semantic rules

These rules are enforced by `create_refined_ast`. Rules S1–S8 are the complete
set of semantic errors; anything not listed here is accepted (see
[Section 7](#7-explicitly-not-checked)).

### S1. Send event names are unique

No two send events in the history MAY share a name. Receive events do not
declare names, so repeated receives of the same send event are valid.

Violation: `SemanticError("duplicate event declaration: '<name>'")`, located
at the second send's event name.

### S2. Messages are declared

The message named in every `Send(...)` MUST be declared in the `Messages`
block.

Violation: `SemanticError("undeclared message: '<name>'")`, located at the
message reference inside `Send(...)`.

### S3. Senders are declared

The sender of every send event MUST be a declared process.

Violation: `SemanticError("undeclared process: '<name>'")`, located at the
sender identifier.

### S4. Send recipients are declared

Every recipient in a send event's target list MUST be a declared process.

Violation: `SemanticError("undeclared process: '<name>'")`, located at the
first offending recipient.

### S5. Receive references are declared

The event named in every `Recv(...)` MUST be the name of a send event
somewhere in the same history.

Violation: `SemanticError("undeclared send event: '<name>'")`, located at the
reference inside `Recv(...)`.

### S6. Causality: no forward references

A receive MUST refer to a send event that appears earlier in history order.
Referring to a send that exists but appears later MUST be reported as a
distinct error, not as an undeclared event.

Violation: `SemanticError("receive refers to send event declared later:
'<name>'")`, located at the reference inside `Recv(...)`.

### S7. Receive targets are declared

Every process listed in `Recv(...) :: ...` MUST be a declared process.

Violation: `SemanticError("undeclared process: '<name>'")`, located at the
first offending target, in source order.

### S8. Receive targets received the message

Every target of a receive MUST be listed among the recipients of the
referenced send event. A receive MAY cover any non-empty subset of those
recipients, including all of them.

Violation: `SemanticError("process '<name>' is not a recipient of send event
'<event>'")`, located at the offending target.

## 5. Resolution rules

On success, stage 3 produces a `RefinedAst` satisfying the following.

### R1. Process declarations survive as plain names

`RefinedAst.process_declarations` is the declared process names in source
order, without locations.

### R2. Sends are inlined

A `SendEventRefined` stores:

- `temporal_pos` — 0-based index of the event in history order;
- `message` — the payload string of the declared message, not its name;
- `process_from_id` — the sender as a plain name;
- `processes_to_ids` — recipient names in source order.

The event's own name MUST be absent from the refined node. Duplicate
recipients are preserved if the source listed them.

### R3. Receives are linked

A `RecvEventRefined` stores `temporal_pos`, `related_send_event` (the exact
`SendEventRefined` instance stored earlier in the refined history), and
`process_ids` (target names in source order, duplicates preserved). It has
no name of its own.

### R4. Events are numbered by source order

`temporal_pos` MUST equal the event's index in `HistoryRefined.events`,
starting at 0 and counting both sends and receives. `RefinedAst.history.events`
MUST be sorted by `temporal_pos`.

### R5. Multicast stays one event

A send with several recipients and a receive with several targets MUST each
remain a single history event. They MUST NOT be expanded into per-process or
per-pair events.

### R6. Declarations are dropped

Message declarations MUST NOT appear in `RefinedAst`; their payloads live in
the send events. Process declarations appear only in
`RefinedAst.process_declarations`.

## 6. Error precedence

The order of checks is normative only where it is observable in a program
with several independent violations:

1. Stage 1 syntax errors are reported before any stage 2 or 3 error.
2. Stage 2 visits every block's contents before merging blocks, so duplicate
   declarations inside any block (W2, W3) are reported before duplicate-block
   errors (W1).
3. Within stage 3, S1 scans the whole history first. A duplicate send name
   anywhere in the history is therefore reported before any name-resolution
   error (S2–S8), even if the undeclared name occurs earlier in the source.
4. Stage 3 then walks events in source order. For a send, checks run in the
   order S2, S3, S4. For a receive, checks run in the order S5, S6, S7, S8.
5. Each error carries the 1-based source location of the offending
   identifier (or block) and renders as
   `<source>:<line>:<column>: error: <message>`.

## 7. Explicitly not checked

A conforming implementation MUST accept the following, because the current
semantics define no error for them:

- **N1.** Unused processes and messages: declarations with no use are valid.
- **N2.** Missing receives: a send need not be received, and a receive need
  not cover every recipient.
- **N3.** Duplicate entries in a recipient list or receive target list; they
  are preserved in the refined AST.
- **N4.** Self-sends and self-receives; a process may send to or receive from
  itself.
- **N5.** Sender as recipient; the sender may be in its own target list.
- **N6.** Payload content; payloads are never interpreted, only inlined.
- **N7.** Per-process event ordering beyond history order, and any global
  clock, vector clock, or logical-time computation.
- **N8.** Process-local alternation of sends and receives; there is no
  per-process state machine.
- **N9.** Declaration order of processes or messages relative to each other
  or to the history; only history order is significant.

## 8. Worked examples

### Valid minimal program

```text
Processes {
  p
  q
}

Messages {
  request := "Request"
}

History {
  m1 := Send(request) :: p -> q
  Recv(m1) :: q
}
```

Refined result:

```text
process_declarations = ["p", "q"]
history.events = [
  SendEventRefined(temporal_pos=0, message="Request",
                   process_from_id="p", processes_to_ids=["q"]),
  RecvEventRefined(temporal_pos=1, related_send_event=<the send>,
                   process_ids=["q"]),
]
```

### Forward reference (S6)

```text
History {
  Recv(m1) :: q     # error: declare later
  m1 := Send(request) :: p -> q
}
```

`Recv(m1)` fails with
`receive refers to send event declared later: 'm1'`, not with
`undeclared send event`.

### Receive from a non-recipient (S8)

```text
History {
  m1 := Send(request) :: p -> q
  Recv(m1) :: q, r
}
```

`q` is accepted; `r` fails with
`process 'r' is not a recipient of send event 'm1'`.

## 9. Rule-to-test map

| Rule | Test | Fixture |
|---|---|---|
| W1 | `test_repeated_blocks_are_errors` | `invalid/repeated_{processes,messages,history}.st` |
| W2 | `test_duplicate_process_declaration_has_location` | `invalid/duplicate_process.st` |
| W3 | `test_duplicate_message_declaration` | `invalid/duplicate_message.st` |
| W4 | `test_empty_program_is_valid`, `test_missing_history_is_valid` | `valid/empty_program.st`, `valid/empty_blocks.st`, `valid/single_line_blocks.st` |
| W5 | `test_process_order_is_preserved`, `test_raw_events_do_not_carry_temporal_positions` | — |
| S1 | `test_invalid_programs` | `invalid/duplicate_event.st` |
| S2 | `test_invalid_programs` | `invalid/undeclared_message.st` |
| S3 | `test_invalid_programs` | `invalid/undeclared_send_sender.st` |
| S4 | `test_invalid_programs` | `invalid/undeclared_send_recipient.st` |
| S5 | `test_invalid_programs` | `invalid/undefined_event.st` |
| S6 | `test_undefined_and_later_event_errors_are_distinct` | `invalid/later_event.st` |
| S7 | `test_invalid_programs` | `invalid/undeclared_recv_process.st` |
| S8 | `test_invalid_programs` | `invalid/recv_not_recipient.st` |
| R1 | `test_process_order_is_preserved_in_refined_ast` | — |
| R2 | `test_refined_send_does_not_keep_event_name` | `valid/canonical.st` |
| R3 | `test_multicast_receive_stays_one_event` | `valid/canonical.st` |
| R4 | `test_temporal_positions_come_from_event_order` | — |
| R5 | `test_multicast_receive_stays_one_event` | `valid/canonical.st` |
| R6 | `test_refined_send_does_not_keep_event_name` | — |
| precedence | `test_semantic_error_has_source_name_and_location`, `test_all_invalid_fixtures_are_covered` | `invalid/duplicate_process.st` |
