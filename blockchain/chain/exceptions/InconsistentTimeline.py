from . import InconsistentBlockchainException


class InconsistentTimeline(InconsistentBlockchainException):
  """
  Exception raised when the new block creation time is not after the top block of the blockchain.
  """

  def __init__(self, message: str) -> None:
    super().__init__(message)
