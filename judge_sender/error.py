class SourceListNotFoundError(FileNotFoundError):
    def __init__(self, *args: object) -> None:
        message = (
            f"{args[0]}. A possible cause is an invalid submission, which has a record with wrong lauguage in database."
        )
        super().__init__(message, *args[1:])
