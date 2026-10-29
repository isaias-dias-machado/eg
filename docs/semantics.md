# Semantic rules

The grammar defines the syntax. These rules are checked after parsing, and a
violation is reported at the offending name.

## Structure

- The `Processes`, `Messages`, and `History` blocks may appear in any order,
  at most once each. All are optional, and empty blocks are valid.
- Process names must be unique, message names must be unique, and send event
  names must be unique.

## References

- In a send, the message, the sender, and every recipient must be declared.
- A receive must name a send event that appears earlier in the history;
  referring to a later send is an error.
- Every receive target must be a declared process and a recipient of the
  referenced send.

## Result

- Events keep source order; each event's temporal position is its 0-based
  index.
- Message names are replaced by their payloads, send event names are dropped,
  and each receive points at its send event.
- A send or receive naming several processes stays a single event.

Nothing else is checked: unused declarations, duplicate recipients,
self-sends, payload contents, and per-process clocks are all allowed.
