from django.test import TestCase
import time
from dataclasses import FrozenInstanceError

from ...chain.BlockData import BlockData
from ...chain.ActionData import File, Node


class BlockDataTest(TestCase):
  """Tests for the BlockData dataclass."""

  def setUp(self):
    """Set up common test data."""
    self.node_action = Node.Node(nodeIP="192.168.1.1", port=9000)
    self.file_action = File.File(
        filename="test.zip", filehash="a_valid_sha512_hash", filesize=4096
    )

    self.base_data = {
        "block_number": 1,
        "previous_block_hash": "0" * 64,
        "creation_time": int(time.time()),
        "creator_ip": "127.0.0.1",
        "creator_port": 8000,
    }

    self.node_block_data_dict = {
        **self.base_data,
        "action_type": "add_node",
        "action_data": self.node_action.to_dict(),
    }

    self.file_block_data_dict = {
        **self.base_data,
        "block_number": 2,
        "previous_block_hash": "f" * 64,
        "action_type": "add_file",
        "action_data": self.file_action.to_dict(),
    }

  def test_successful_creation(self):
    """Test that a BlockData object can be created successfully."""
    instance = BlockData(
        **self.base_data, action_type="add_node", action_data=self.node_action
    )
    self.assertEqual(instance.block_number, 1)
    self.assertEqual(instance.action_data, self.node_action)

  def test_is_frozen(self):
    """Test that the BlockData dataclass is frozen."""
    instance = BlockData(
        **self.base_data, action_type="add_node", action_data=self.node_action
    )
    with self.assertRaises(FrozenInstanceError):
      instance.block_number = 5

  def test_invalid_previous_block_hash(self):
    """Test that __post_init__ raises ValueError for an invalid hash."""
    invalid_data = self.base_data.copy()
    invalid_data["previous_block_hash"] = "not_a_hex_string"
    with self.assertRaisesRegex(ValueError, "invalid previous_block_hash"):
      BlockData(
          **invalid_data,
          action_type="add_node",
          action_data=self.node_action,
      )

  def test_to_dict_conversion(self):
    """Test that the to_dict method works correctly."""
    instance = BlockData.from_dict(self.node_block_data_dict)
    self.assertEqual(instance.to_dict(), self.node_block_data_dict)

  def test_from_dict_with_node_action(self):
    """Test creating an instance from a dict with a Node action."""
    instance = BlockData.from_dict(self.node_block_data_dict)
    self.assertEqual(instance.block_number, 1)
    self.assertIsInstance(instance.action_data, Node.Node)
    self.assertEqual(instance.action_data.nodeIP, "192.168.1.1")

  def test_from_dict_with_file_action(self):
    """Test creating an instance from a dict with a File action."""
    instance = BlockData.from_dict(self.file_block_data_dict)
    self.assertEqual(instance.block_number, 2)
    self.assertIsInstance(instance.action_data, File.File)
    self.assertEqual(instance.action_data.filename, "test.zip")

  def test_from_dict_invalid_action_type(self):
    """Test that from_dict raises TypeError for an unsupported action type."""
    invalid_data = self.node_block_data_dict.copy()
    invalid_data["action_type"] = "unknown_action"
    with self.assertRaisesRegex(TypeError, "Invalid action_data"):
      BlockData.from_dict(invalid_data)
