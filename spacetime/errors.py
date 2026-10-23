"""Diagnostics for the Space-Time DSL.

Both parse and semantic errors derive from :class:`DslError`, so the CLI can
handle them uniformly. An error carries an optional source location and
source name; the compiler fills in the name, and ``str()`` renders the
familiar ``file:line:column: error: message`` form.
"""

from lark.exceptions import UnexpectedInput

from .ast import SourceLocation


class DslError(Exception):
    """Base class for user-facing DSL errors.

    Attributes:
        message: Human-readable description without a location prefix.
        location: Optional 1-based source position.
        source_name: Optional file name or label. Mutable because
            :func:`spacetime.compiler.compile_source` attaches it after the
            error has been raised.

    Failure modes:
        None; construction never validates the fields.
    """

    def __init__(
        self,
        message: str,
        *,
        location: SourceLocation | None = None,
        source_name: str | None = None,
    ):
        """Store the diagnostic; ``Exception`` keeps ``message`` as args[0]."""
        super().__init__(message)
        self.message = message
        self.location = location
        self.source_name = source_name

    def __str__(self) -> str:
        """Render ``source:line:column: error: message``.

        A missing location or source name simply shortens the prefix.
        """
        if self.location is None:
            if self.source_name:
                return f"{self.source_name}: error: {self.message}"
            return f"error: {self.message}"

        prefix = f"{self.location.line}:{self.location.column}"
        if self.source_name:
            prefix = f"{self.source_name}:{prefix}"
        return f"{prefix}: error: {self.message}"


class ParseError(DslError):
    """Syntax error produced by the Lark front end."""

    @classmethod
    def from_lark(
        cls, exc: UnexpectedInput, source: str, source_name: str
    ) -> "ParseError":
        """Adapt Lark's ``UnexpectedInput`` to a ``ParseError``.

        Lark sometimes reports ``-1``/``-1`` for end-of-input failures. In
        that case the position is clamped to the end of ``source`` so the
        diagnostic stays meaningful.

        Failure modes:
            Never raises for malformed Lark metadata. A failure while
            formatting the source excerpt is swallowed and only the main
            message is kept.
        """
        line = getattr(exc, "line", None)
        column = getattr(exc, "column", None)

        # Lark reports -1/-1 for some end-of-input errors. Point at the
        # end of the source instead of exposing a meaningless location.
        if line is None or column is None or line < 1 or column < 1:
            if source:
                line = source.count("\n") + 1
                last_newline = source.rfind("\n")
                column = len(source) - last_newline
            else:
                line, column = 1, 1

        location = SourceLocation(line, column)

        try:
            context = exc.get_context(source)
        except Exception:
            context = ""

        message = f"syntax error: {exc}"
        if context:
            message = f"{message}\n{context}"
        return cls(message, location=location, source_name=source_name)


class SemanticError(DslError):
    """Structural or name-resolution error.

    Raised by the builder for duplicate blocks and declarations, and by
    semantics for undeclared names, reversed causality, and receives from
    non-recipients.
    """
