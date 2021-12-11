class SourceListNotFoundError(FileNotFoundError):
    # A possible cause is an invalid submission, which has a record with wrong lauguage in database.
    pass
