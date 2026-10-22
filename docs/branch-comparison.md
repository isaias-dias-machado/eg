# Branch comparison: `Pedro_branch` vs `isaias_v2`

This note compares the two feature branches that build a Lark grammar for the
message-history DSL described in `README.md`. It covers history, code layout,
observed behaviour, and what to do next.

## History and shape

| | `Pedro_branch` | `isaias_v2` |
|---|---|---|
| Tip | `0f75dae` (2026-10-19) | `ca37755` (2026-10-22) |
| Commits after `00fc392` (init) | 3 | 5 |
| Common ancestor | `00fc392` | `00fc392` |
| Position vs `master` | 1 commit behind (`8ae0369`, example update) | `example.txt` content matches `master`, but commits `0477566` (requirements fix) and `8ae0369` are missing from history |

The branches are siblings, not a parent/child pair. Both are Python + Lark
parsers for the same syntax (`Processes` / `Messages` / `History`), but they
took different design routes.

## Design differences

### `Pedro_branch`

- Grammar lives as a Python string **inside `main.py`** (~70 lines), fused with
  the driver.
- Parsing runs at import time (`print(parser.parse(ex).pretty())` at module
  level), so the file cannot be imported as a library.
- No tests. A single hardcoded example lives in the source.
- `requirements.txt` is correct: `lark==1.3.1`.
- Recognises an `Events { ... }` block, but only through **hardcoded literals**
  (`persist`, `"Send event %succession"`, `"Recv event"`). It is a sketch of the
  idea, not a general syntax.

### `isaias_v2`

- Grammar extracted to `grammar.lark` (87 lines, sectioned and commented);
  `main.py` is a 30-line driver.
- Driver parses one inline sample and then loops over `test_examples/`
  (4 fixtures: empty file, reordered blocks, full scenario).
- Wraps the inline parse in `try/except UnexpectedInput`; the fixture loop is
  **not** guarded.
- Reads `grammar.lark` through a **relative path**, so it only works when the
  current directory is the repo root.
- Iterates `os.listdir()` without sorting, so test order depends on the
  filesystem.
- `requirements.txt` still carries the init typo **`lark==1.3.1k`**;
  `pip install -r requirements.txt` fails with `Invalid requirement: 'lark==1.3.1k'`.
  Pedro fixed exactly this in `0477566`; `isaias_v2` did not carry the fix over.

## Observed behaviour

Each input was fed to both grammars directly (not through the drivers):

| Input feature | `Pedro_branch` | `isaias_v2` |
|---|---|---|
| Comments `// ...` | FAIL | FAIL |
| `Recv m1 :: q` (dotted spelling) | FAIL | FAIL |
| `Recv(m1) :: p, q` (multicast list) | FAIL | **OK** |
| `Events { ... }` block | OK (hardcoded forms only) | FAIL |
| Blocks in any order / empty blocks | FAIL | **OK** |
| Blank lines between blocks | FAIL | **OK** |
| Escaped quote inside a string | FAIL | FAIL |
| File without trailing newline | OK | OK |

Both drivers run their own embedded example successfully.

The repo's own `example.txt` fails to parse in **both** branches: it starts
with `//` comments and neither grammar supports comments. Neither branch yet
parses the documentation example it ships with.

Also note that comments inside `grammar.lark` advertise a dotted `Recv`
spelling and list sugar; only the list sugar is actually implemented.

## Assessment

- **`isaias_v2` is the better base.** Grammar is separated from the driver,
  block handling is general, blocks may appear in any order, blank lines are
  preserved, and there is a test corpus. That structure is what should grow.
- **`Pedro_branch` is narrower** (single fixed layout, order-dependent grammar
  inside a string, hardcoded `Events`), but it fixed the dependency pin and it
  sketched the `Events` concept that `isaias_v2` has no notion of.
- Neither branch is ready to parse `example.txt`. Comments are the immediate
  blocker. There is also one shared bug: strings cannot contain `\"` in either
  grammar, because `".*?"` matches lazily and stops at the first quote.

## Suggested next steps

1. Correct `requirements.txt` on `isaias_v2` to `lark==1.3.1` (cherry-pick
   `0477566`, or simply fix the line).
2. Add comment support to `grammar.lark` (`%ignore /\/\/[^\n]*/`) so
   `example.txt` becomes parseable, then add `example.txt` to the test fixtures.
3. Guard the fixture loop with `try/except UnexpectedInput`, sort
   `os.listdir`, and resolve `grammar.lark` relative to `__file__`.
4. Decide whether `Events` belongs to the language. If it does, add it to
   `grammar.lark` as real syntax; `Pedro_branch` is the reference for intent,
   not for implementation.
5. Update the `grammar.lark` comments so they describe only syntax that exists
   (dotted `Recv` is claimed but unsupported).
