
class DraftPickleException(Exception):
    """Raise when no pickle file exists"""
    pass


class DraftNotInitializedException(Exception):
    """Raise if somehow we try to modify the draft data frame and it hasn't been initialized"""
    pass


class NoTransactionFileExists(Exception):
    """Raise if the transaction file doesn't exist"""