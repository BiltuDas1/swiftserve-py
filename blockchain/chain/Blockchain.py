from typing import List
from io import BytesIO
from .Block import Block
from .BlockData import BlockData
from . import Variables, Key
from .exceptions import InconsistentHash, InvalidNextBlock, InconsistentTimeline, InvalidSignature


class Blockchain:
  """
  Blockchain refers to a list of blocks which allows secure addition, validation,
  synchronization, and comparison operations on a blockchain.
  """

  def __init__(self, genesis_block: Block):
    """
    Initializes the blockchain with a genesis block.

    Args:
      genesis_block: The first block of the blockchain.
    """
    self.__blocks: List[Block] = [genesis_block]

  def add(self, block: Block) -> None:
    """
    Adds a block to the blockchain after validating all constraints.

    Args:
      block: The new block to be added.

    Raises:
      InvalidNextBlock: If block number not comes after the top of the block.
      InconsistentTimeline: If the new block creation time is less than the top block in the blockchain.
      InconsistentHash: If the new block previous block hash field has a hash which is not matched with the top of the blockchain.
      InvalidSignature: If the new block signature is invalid.
      FileExistsError: If the public key of the creator of the new node doesn't exist into the system, and also not available into the internet to download.
    """
    data: BlockData = block.to_blockdata()

    if data.block_number != self.last_block_number() + 1:
      raise InvalidNextBlock.InvalidNextBlock(f"blockNumber can only be {self.last_block_number() + 1}")

    if self.__blocks[-1].to_blockdata().creation_time > data.creation_time:
      raise InconsistentTimeline.InconsistentTimeline("new block can't be created before the top of the block")

    if self.__blocks[-1].get_hash() != data.previous_block_hash:
      raise InconsistentHash.InconsistentHash("previousBlockHash does not match top of the chain")

    key = Key.Key()
    key.get_key(data.creator_ip, 80) # Get Public Key

    # If key not found, then reject the block
    if (kpub := key.get_public_key_raw()) is not None:
      if not block.verify_signature(kpub):
        raise InvalidSignature.InvalidSignature("block signature verification failed")
    else:
      raise FileExistsError("key doesn't exist")

    self.__blocks.append(block)

  def last_block_number(self) -> int:
    """
    Returns the block number of the last block in the blockchain.

    Returns:
      int: Last block number.
    """
    return self.__blocks[-1].to_blockdata().block_number

  def size(self) -> int:
    """
    Returns the total number of blocks in the blockchain.

    Returns:
      int: Total block count.
    """
    return len(self.__blocks)

  def last_block_hash(self) -> str:
    """
    Returns the hash of the last block in the blockchain.

    Returns:
      str: Hash of the top block.
    """
    return self.__blocks[-1].get_hash()

  def top_block(self) -> Block:
    """
    Returns the top (most recent) block in the blockchain.

    Returns:
      Block: The top block object.
    """
    return self.__blocks[-1]

  def get_blocks_data(self, start_block_num: int) -> bytes:
    """
    Serializes and returns blocks starting from a specific block number.

    Args:
      start_block_num: The block number to start from.

    Returns:
      bytes: Serialized byte stream of blocks.
    """
    baos = BytesIO()

    for i in range(start_block_num, self.last_block_number() + 1):
      blk = self.__blocks[i]
      baos.write(blk.to_bytes())

    return baos.getvalue()

  def load_blocks_data(self, data: bytes, start_block_num: int) -> None:
    """
    Deserializes and adds blocks from byte data to the blockchain, replacing from startBlockNum.

    Args:
      data: Byte stream containing one or more blocks.
      start_block_num: Index to start replacing from.
    """
    # Removing the blocks till specific index
    for _ in range(self.last_block_number(), start_block_num - 1, -1):
      self.__blocks.pop()

    buffer = BytesIO()
    for b in data:
      buffer.write(bytes([b]))
    if b == Variables.EOF:
      blk = Block.from_bytes(buffer.getvalue())
      self.add(blk)
      buffer = BytesIO()

  def get_block_hash(self, position: int) -> str:
    """
    Returns the hash of the block at a specific position.

    Args:
      position: Index of the block.

    Returns:
      str: Hash of the specified block.
    """
    return self.__blocks[position].get_hash()

