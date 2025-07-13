from . import InconsistentBlockchainException


class InvalidSignature(InconsistentBlockchainException):
  """
  Exception raised when the signature of the block don't match.
  """

  def __init__(self, message: str) -> None:
    super().__init__(message)
