from typing import Optional


class ParseError(ValueError):
    """
    This error occurs when the parser encounters a syntax error
    in the TOML being parsed. The error references the line and
    location within the line where the error was encountered.
    """

    def __init__(
        self, line, col, message=None
    ):  # type: (int, int, Optional[str]) -> None
        self._line = line
        self._col = col

        if message is None:
            message = "TOML parse error"

        super(ParseError, self).__init__(
            "{} at line {} col {}".format(message, self._line, self._col)
        )


class MixedArrayTypesError(ParseError):
    """
    An array was found that had two or more element types.
    """

    def __init__(self, line, col):  # type: (int, int) -> None
        message = "Mixed types found in array"

        super(MixedArrayTypesError, self).__init__(line, col, message=message)


class InvalidNumberOrDateError(ParseError):
    """
    A numeric or date field was improperly specified.
    """

    def __init__(self, line, col):  # type: (int, int) -> None
        message = "Invalid number or date format"

        super(InvalidNumberOrDateError, self).__init__(line, col, message=message)


class UnexpectedCharError(ParseError):
    """
    An unexpected character was found during parsing.
    """

    def __init__(self, line, col, char):  # type: (int, int, str) -> None
        message = "Unexpected character: {}".format(repr(char))

        super(UnexpectedCharError, self).__init__(line, col, message=message)


class UnexpectedEofError(ParseError):
    """
    The TOML being parsed ended before the end of a statement.
    """

    def __init__(self, line, col):  # type: (int, int) -> None
        message = "Unexpected end of file"

        super(InvalidNumberOrDateError, self).__init__(line, col, message=message)


class UnexpectedEofError(ParseError):
    """
    An error that indicates a bug in the parser.
    """

    def __init__(self, line, col):  # type: (int, int) -> None
        message = "Unexpected end of file"

        super(InvalidNumberOrDateError, self).__init__(line, col, message=message)


class NonExistentKey(KeyError):
    """
    A non-existent key was used.
    """

    def __init__(self, key):
        message = 'Key "{}" does not exist.'.format(key)

        super(NonExistentKey, self).__init__(message)
