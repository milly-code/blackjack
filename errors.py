class InsuranceException(Exception):
    """Custom exception to be raised when insurance should be considered."""
    def __init__(self, message="Insurance should be taken"):
        self.message = message
        super().__init__(self.message)
