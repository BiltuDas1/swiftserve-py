from django.test import TestCase
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import time
import json
import base64
from dataclasses import asdict

from ...chain import Block, Variables
from ...chain.ActionData import File, Node


class BlockTest(TestCase):
  """Tests for the Block class."""

  def setUp(self):
    """Set up test data for Block tests."""
    self.private_key = Ed25519PrivateKey.generate()
    self.public_key = self.private_key.public_key()

    self.node_action = Node.Node(nodeIP="192.168.1.1", port=9000)
    self.file_action = File.File(
        filename="data.zip", filehash="some_sha512_hash", filesize=2048
    )

    self.block_with_node = Block.Block(
        block_number=1,
        previous_block_hash="0" * 64,
        action_type="add_node",
        action_data=self.node_action,
        creator_ip="127.0.0.1",
        creator_port=8000,
        key=self.private_key,
    )

    self.block_with_file = Block.Block(
        block_number=2,
        previous_block_hash=self.block_with_node.get_hash(),
        action_type="add_file",
        action_data=self.file_action,
        creator_ip="127.0.0.1",
        creator_port=8000,
        key=self.private_key,
    )

  def test_block_creation(self):
    """Test the basic creation and properties of a Block."""
    block_data = self.block_with_node.to_blockdata()
    self.assertEqual(block_data.block_number, 1)
    self.assertEqual(block_data.previous_block_hash, "0" * 64)
    self.assertEqual(block_data.action_type, "add_node")
    self.assertEqual(block_data.action_data, self.node_action)
    self.assertEqual(block_data.creator_ip, "127.0.0.1")
    self.assertEqual(block_data.creator_port, 8000)
    # Check if creation time is recent
    self.assertAlmostEqual(block_data.creation_time, int(time.time()), delta=2)

    self.assertIsInstance(self.block_with_node.get_hash(), str)
    self.assertEqual(len(self.block_with_node.get_hash()), 64)  # SHA-256

    # Test __str__ and get_signature
    self.assertIsInstance(self.block_with_node.get_signature(), str)
    self.assertEqual(str(self.block_with_node), json.dumps(asdict(block_data)))

  def test_invalid_action_data_type(self):
    """Test that creating a block with invalid action_data raises ValueError."""
    with self.assertRaisesRegex(ValueError, "Invalid type for action_data"):
      Block.Block(
          block_number=2,
          previous_block_hash="a" * 64,
          action_type="invalid_action",
          action_data={"some": "dict"},  # Invalid type
          creator_ip="127.0.0.1",
          creator_port=8000,
          key=self.private_key,
      )

  def test_signature_verification(self):
    """Test that signature verification works correctly."""
    # Test with the correct public key
    self.assertTrue(self.block_with_node.verify_signature(self.public_key))

    # Test with an incorrect public key
    wrong_private_key = Ed25519PrivateKey.generate()
    wrong_public_key = wrong_private_key.public_key()
    self.assertFalse(self.block_with_node.verify_signature(wrong_public_key))

  def test_serialization_deserialization(self):
    """Test that a block can be serialized to bytes and deserialized back."""
    block_bytes = self.block_with_node.to_bytes()
    deserialized_block = Block.Block.from_bytes(block_bytes)

    # Compare the core components
    self.assertEqual(
        self.block_with_node.to_blockdata(), deserialized_block.to_blockdata()
    )
    self.assertEqual(self.block_with_node.get_hash(), deserialized_block.get_hash())
    self.assertEqual(
        self.block_with_node.get_signature_bytes(),
        deserialized_block.get_signature_bytes(),
    )

  def test_from_bytes_malformed_data(self):
    """Test that deserializing malformed data raises a ValueError."""
    malformed_bytes = b"\x02some_invalid_data\x03\x17"
    with self.assertRaisesRegex(ValueError, "Malformed byte structure"):
      Block.Block.from_bytes(malformed_bytes)

  def test_serialization_deserialization_with_file_action(self):
    """Test serialization/deserialization with a File action."""
    block_bytes = self.block_with_file.to_bytes()
    deserialized_block = Block.Block.from_bytes(block_bytes)

    self.assertEqual(
        self.block_with_file.to_blockdata(), deserialized_block.to_blockdata()
    )
    self.assertEqual(self.block_with_file.get_hash(), deserialized_block.get_hash())
    self.assertEqual(
        self.block_with_file.get_signature_bytes(),
        deserialized_block.get_signature_bytes(),
    )
    # Check that the action_data is correctly deserialized as a File object
    self.assertIsInstance(deserialized_block.to_blockdata().action_data, File.File)
    self.assertEqual(deserialized_block.to_blockdata().action_data, self.file_action)

  def test_from_bytes_unsupported_action_type(self):
    """Test that from_bytes raises ValueError for an unsupported action type."""
    # Manually construct a byte stream with an invalid action type
    block_data_dict = self.block_with_node.to_blockdata().to_dict()
    block_data_dict["action_type"] = "unknown_action"

    # Re-serialize the modified data part
    modified_data_b64 = base64.b64encode(json.dumps(block_data_dict).encode("utf-8"))

    # Get original hash and signature
    original_hash_b64 = base64.b64encode(self.block_with_node.get_hash().encode("utf-8"))
    original_sig_b64 = base64.b64encode(self.block_with_node.get_signature_bytes())

    # Assemble the malformed byte stream
    result = bytearray()
    result.extend(Variables.START)
    result.extend(modified_data_b64)
    result.extend(Variables.END)
    result.extend(Variables.START)
    result.extend(original_hash_b64)
    result.extend(Variables.END)
    result.extend(Variables.START)
    result.extend(original_sig_b64)
    result.extend(Variables.END)
    result.extend(Variables.EOF)

    with self.assertRaisesRegex(ValueError, "Unsupported action_type: unknown_action"):
      Block.Block.from_bytes(bytes(result))
