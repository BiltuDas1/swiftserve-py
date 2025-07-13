from . import InconsistentBlockchainException


class InvalidNextBlock(InconsistentBlockchainException):
  """
  Exception raised when the top block and the new block can't be linked together.
  """

  def __init__(self, message: str) -> None:
    super().__init__(message)
