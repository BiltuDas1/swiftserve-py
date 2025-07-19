import re
from typing import List
from io import BytesIO
from .Block import Block
from .BlockData import BlockData
from . import Variables, Key
from .exceptions import (
    InconsistentHash,
    InvalidNextBlock,
    InconsistentTimeline,
    InvalidSignature,
)
from .ActionData import Node, File
from registry.Node.List import NodeList
from registry.File.List import FileList
from registry.File.FileInfo import FileInfo
from environments import Env
import httpx
import os
import time


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

  def add(self, block: Block, blockOperation: bool = True) -> None:
    """
    Adds a block to the blockchain after validating all constraints.

    Args:
      block: The new block to be added.
      blockOperation: Process action data, and then do the operation which is mentioned. Default True.

    Raises:
      InvalidNextBlock: If block number not comes after the top of the block.
      InconsistentTimeline: If the new block creation time is less than the top block in the blockchain.
      InconsistentHash: If the new block previous block hash field has a hash which is not matched with the top of the blockchain.
      InvalidSignature: If the new block signature is invalid.
      FileExistsError: If the public key of the creator of the new node doesn't exist into the system, and also not available into the internet to download.
      TypeError: If it doesn't get the expected type of action_data.
      ValueError: If it doesn't get the expected action_type.
    """
    data: BlockData = block.to_blockdata()

    if data.block_number != self.last_block_number() + 1:
      raise InvalidNextBlock.InvalidNextBlock(
          f"blockNumber can only be {self.last_block_number() + 1}"
      )

    if self.__blocks[-1].to_blockdata().creation_time > data.creation_time:
      raise InconsistentTimeline.InconsistentTimeline(
          "new block can't be created before the top of the block"
      )

    if self.__blocks[-1].get_hash() != data.previous_block_hash:
      raise InconsistentHash.InconsistentHash(
          "previousBlockHash does not match top of the chain"
      )

    key = Key.Key()
    key.get_key(data.creator_ip, data.creator_port)  # Get Public Key

    # If key not found, then reject the block
    if (kpub := key.get_public_key_raw()) is not None:
      if not block.verify_signature(kpub):
        raise InvalidSignature.InvalidSignature(
            "block signature verification failed"
        )
    else:
      raise FileExistsError("key doesn't exist")

    self.__blocks.append(block)

    # If block operation is not permitted
    if not blockOperation:
      return

    # Perform operation according to the action_type
    nodelist: NodeList = Env.get("NODES")
    filelist: FileList = Env.get("FILES")
    match data.action_type:
      case "add_node":
        if isinstance(data.action_data, Node.Node):
          machine_ip: str = Env.get("IPADDRESS")
          port: int = int(Env.get("PORT"))
          if machine_ip != data.action_data.nodeIP and nodelist.add(data.action_data.nodeIP, data.action_data.port):
            # Sending the whole blockchain data to the new node
            blocks_data = self.get_blocks_data(0)
            try:
              httpx.post(
                  url=f"http://{data.action_data.nodeIP}:{data.action_data.port}/overwriteBlockchain",
                  content=blocks_data,
                  headers={"Content-Type": "application/octet-stream"}
              )
            except Exception:
              pass

            nodelist.save(Env.get("NODELIST_PATH"))

            # Sending response to download files of current node
            for filename in filelist.getFiles():
              file_info = filelist.get(filename)
              if file_info.total_chunks == 1:
                end_byte = file_info.size - 1
              else:
                end_byte = (4 * 1024 * 1024) - 1
              try:
                httpx.post(
                    url=f"http://{data.action_data.nodeIP}:{data.action_data.port}/response",
                    data={
                        "filename": filename,
                        "chunk": 1,
                        "total_chunks": filelist.get(filename).total_chunks,
                        "start_byte": 0,
                        "end_byte": end_byte,
                        "sha1": file_info.filehash,
                        "ip_address": machine_ip,
                        "port": port,
                    },
                )
              except Exception:
                pass
        else:
          raise TypeError("Invalid action_data")
      case "remove_node":
        if isinstance(data.action_data, Node.Node):
          nodelist.remove(data.action_data.nodeIP)
        else:
          raise TypeError("Invalid action_data")

      case "add_file":
        if isinstance(data.action_data, File.File):
          f = data.action_data
          total_chunks = f.filesize // (4 * 1024 * 1024)
          if (f.filesize % (4 * 1024 * 1024)) != 0:
            total_chunks += 1
          if not filelist.exist(f.filename):
            filelist.add(f.filename, FileInfo(
                f.filehash, f.filesize, int(time.time()), total_chunks
            ))
        else:
          raise TypeError("Invalid action_data")

      case "remove_file":
        if isinstance(data.action_data, File.File):
          f = data.action_data

          if not filelist.exist(f.filename):
            filelist.remove(f.filename)
        else:
          raise TypeError("Invalid action_data")

      case _:
        raise ValueError("Invalid action_type")

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

  def save(self, filepath: str):
    """
    Saves the blockchain data into file
    Args:
      filepath: The path where the data will be stored
    """
    data = self.get_blocks_data(0)

    with open(filepath, 'wb') as f:
      f.write(data)

  def load(self, filepath: str):
    """
    Loads the blockchain data from file
    Args:
      filepath: The path where the blockchian data is stored
    Raises:
      ValueError: when the file doesn't contains valid blockchain data
      FileNotFoundError: When the file doesn't exist
    """
    if not os.path.exists(filepath):
      raise FileNotFoundError()

    with open(filepath, 'rb') as f:
      data: bytes = f.read()
      self.load_blocks_data(data, 0)

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
    baos = bytearray()

    for i in range(start_block_num, self.last_block_number() + 1):
      blk = self.__blocks[i]
      baos.extend(blk.to_bytes())

    return bytes(baos)

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

    buffer = bytearray()
    for b in data:
      buffer.append(b)
      if b == Variables.EOF[0]:
        blk = Block.from_bytes(buffer)
        if self.size() == 0:
          self.add_genesis(blk)
        else:
          self.add(blk, blockOperation=False)
        buffer = bytearray()

  def get_block_hash(self, position: int) -> str:
    """
    Returns the hash of the block at a specific position.

    Args:
      position: Index of the block.

    Returns:
      str: Hash of the specified block.
    """
    return self.__blocks[position].get_hash()

  def add_genesis(self, genesis_block: Block) -> bool:
    """
    Add the genesis block to the blockchain (Only when the blockchain doesn't have any genesis block)
    Args:
      genesis_block: The genesis block of the blockchain
    Returns:
      bool: True if adding genesis block is successful, otherwise False
    """
    if self.size() != 0:
      return False

    nodelist: NodeList = Env.get("NODES")
    data = genesis_block.to_blockdata()
    match data.action_type:
      case "add_node":
        if isinstance(data.action_data, Node.Node):
          nodelist.add(data.action_data.nodeIP, data.action_data.port)
      case _:
        return False

    self.__blocks.append(genesis_block)
    return True
