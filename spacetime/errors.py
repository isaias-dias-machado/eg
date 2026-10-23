from lark.exceptions import UnexpectedInput

from .ast import SourceLocation


class DslError(Exception):
    def __init__(
        self,
        message: str,
        *,
        location: SourceLocation | None = None,
        source_name: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.location = location
        self.source_name = source_name

    def __str__(self) -> str:
        if self.location is None:
            if self.source_name:
                return f"{self.source_name}: error: {self.message}"
            return f"error: {self.message}"

        prefix = f"{self.location.line}:{self.location.column}"
        if self.source_name:
            prefix = f"{self.source_name}:{prefix}"
        return f"{prefix}: error: {self.message}"


class ParseError(DslError):
    @classmethod
    def from_lark(
        cls, exc: UnexpectedInput, source: str, source_name: str
    ) -> "ParseError":
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
    pass
