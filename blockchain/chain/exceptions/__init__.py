class InconsistentBlockchainException(Exception):
  """
  Exception raised when the blockchain is found to be inconsistent,
  such as when a remote node has mismatched or corrupted block data.
  """

  def __init__(self, message: str) -> None:
    super().__init__(message)
