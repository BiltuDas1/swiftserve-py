from . import InconsistentBlockchainException


class InconsistentHash(InconsistentBlockchainException):
  """
  Exception raised when the hash of the blocks don't match.
  """

  def __init__(self, message: str) -> None:
    super().__init__(message)
