import time
import json
import hashlib
import base64
from dataclasses import asdict
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey
)
from cryptography.exceptions import InvalidSignature
from . import BlockData, Variables
from .ActionData import ActionData, File, Node


class Block:
  """
  Represents a block in the blockchain
  """

  def __init__(self, block_number: int, previous_block_hash: str, action_type: str, action_data: ActionData, creator_ip: str, key: Ed25519PrivateKey):
    """
    Initializes a new block either from data or from a byte stream.

    Args:
      block_number: Unique index of the block.
      previous_block_hash: Hash of the previous block in the chain.
      action_type: Type of action this block represents (e.g., 'add_file', 'add_node').
      action_data: The associated data for the action.
      creator_ip: IP address of the block creator.
      key: Private key used to sign the block.

    Raises:
      ValueError: If action_data is not of allowed types.
    """
    if not isinstance(action_data, (File.File, Node.Node)):
        raise ValueError(f"Invalid type for action_data: {type(action_data)}")

    self.__data: BlockData.BlockData = BlockData.BlockData(
        block_number=block_number,
        previous_block_hash=previous_block_hash,
        creation_time=int(time.time()),
        action_type=action_type,
        action_data=action_data,
        creator_ip=creator_ip
    )

    self.__json: str = json.dumps(asdict(self.__data))
    self.__signature: bytes = self.__sign(key)
    self.__hash: str = self.__generate_hash()
    self.__bytes: bytes = self._convert_to_bytes()

  def __generate_hash(self) -> str:
    """
    Generates a SHA-256 hash from the block's JSON representation.

    Returns:
      str: Hexadecimal string of the hash.
    """
    return hashlib.sha256(self.__json.encode('utf-8')).hexdigest()

  def __sign(self, key: Ed25519PrivateKey) -> bytes:
    """
    Signs the block using Ed25519 private key.

    Args:
      key: Private key of the creator node.

    Returns:
      bytes: Raw byte signature of the block.
    """
    return key.sign(self.__json.encode('utf-8'))

  def get_hash(self) -> str:
    """
    Returns the SHA-256 hash of the block.

    Returns:
      str: Hash value of the block.
    """
    return self.__hash

  def get_signature(self) -> str:
    """
    Returns the base64 encoded signature of the block.

    Returns:
      str: Base64 signature string.
    """
    return base64.b64encode(self.__signature).decode()

  def get_signature_bytes(self) -> bytes:
    """     
    Returns the raw byte signature.

    Returns:
      bytes: Raw digital signature.
    """
    return self.__signature

  def verify_signature(self, pub_key: Ed25519PublicKey) -> bool:
    """
    Verifies the block's signature using the creator's public key.

    Args:
      pub_key (Ed25519PublicKey): The public key for verification.

    Returns:
      bool: True if signature is valid, False otherwise.
    """
    try:
      pub_key.verify(self.__signature, self.__json.encode('utf-8'))
      return True
    except InvalidSignature:
      return False

  def __str__(self) -> str:
    return self.__json

  def to_blockdata(self) -> BlockData.BlockData:
    """
    Returns the internal data record of the block.

    Returns:
      BlockData: The actual block data (excluding hash and signature).
    """
    return self.__data

  def to_bytes(self) -> bytes:
    """
    Serializes the block into a byte array (data + hash + signature + delimiters).

    Returns:
      bytes: Serialized binary format of the block.
    """
    return self.__bytes

  def _convert_to_bytes(self) -> bytes:
    """
    Converts internal state of the block into a structured byte stream
    using control delimiters (START, END, EOF).

    Returns:
      bytes: Complete byte structure representing the block.
    """
    result = bytearray()

    # Serialize data
    result.extend(Variables.START)
    result.extend(base64.b64encode(json.dumps(self.__data.to_dict()).encode('utf-8')))
    result.extend(Variables.END)

    # Serialize hash
    result.extend(Variables.START)
    result.extend(base64.b64encode(self.__hash.encode('utf-8')))
    result.extend(Variables.END)

    # Serialize signature
    result.extend(Variables.START)
    result.extend(base64.b64encode(self.__signature))
    result.extend(Variables.END)

    result.extend(Variables.EOF)
    return bytes(result)

  @classmethod
  def __load_block(cls, block_data: BlockData.BlockData, hashstr: str, signature: bytes, bytes_data: bytes) -> 'Block':
    """
    Helper method allows to load data to a class using BlockData, Signature, Hash

    Args:
      block_data: The BlockData object containing BlockData
      hashstr: The hash of the Block
      signature: The signature of the Block
      bytes_data: The byte format data of the whole block
    """
    instance = cls.__new__(cls)
    instance.__data = block_data
    instance.__json = json.dumps(asdict(block_data))
    instance.__signature = signature
    instance.__hash = hashstr
    instance.__bytes = bytes_data
    return instance

  @classmethod
  def from_bytes(cls, data: bytes) -> 'Block':
    """
    Parses a byte stream and reconstructs the block's components:
    data, hash, and signature.

    Args:
      data: The byte array representing a serialized block.

    Raises:
      ValueError: If the byte format is invalid or incomplete.
    """
    blocks: list[bytes] = []
    current = bytearray()
    recording = False

    # Reading the data
    for byte in data:
      if byte == Variables.START[0]:
        current = bytearray()
        recording = True
      elif byte == Variables.END[0]:
        if recording:
          blocks.append(bytes(current))
        recording = False
      elif byte == Variables.EOF[0]:
        break
      elif recording:
        current.append(byte)

    if len(blocks) != 3:
      raise ValueError("Malformed byte structure")

    # Deserialize block data (JSON)
    block_data_dict = json.loads(base64.b64decode(blocks[0]).decode("utf-8"))

    # Determine which ActionData type to use
    action_type = block_data_dict["action_type"]
    action_data_dict = block_data_dict["action_data"]

    if action_type in Variables.FileMethods:
      action_data = File.File.from_dict(action_data_dict)
    elif action_type in Variables.NodeMethods:
      action_data = Node.Node.from_dict(action_data_dict)
    else:
      raise ValueError(f"Unsupported action_type: {action_type}")

    # Create BlockData
    block_data = BlockData.BlockData(
      block_number=block_data_dict["block_number"],
      previous_block_hash=block_data_dict["previous_block_hash"],
      creation_time=block_data_dict["creation_time"],
      action_type=action_type,
      action_data=action_data,
      creator_ip=block_data_dict["creator_ip"]
    )

    # Get hash and signature
    hash_str = base64.b64decode(blocks[1]).decode("utf-8")
    signature_bytes = base64.b64decode(blocks[2])

    return cls.__load_block(block_data, hash_str, signature_bytes, data)
