from django.test import TestCase
from ...chain.ActionData.File import File
from ...chain.ActionData.Node import Node
from dataclasses import FrozenInstanceError


class FileActionDataTest(TestCase):
  """Tests for the File ActionData class."""

  def setUp(self):
    """Set up test data for File tests."""
    self.file_data = {
        "filename": "test.txt",
        "filehash": "a_very_long_sha512_hash_string_for_testing_purposes",
        "filesize": 1024,
    }
    self.file_instance = File(**self.file_data)

  def test_to_dict(self):
    """Test that to_dict method returns the correct dictionary."""
    self.assertEqual(self.file_instance.to_dict(), self.file_data)

  def test_from_dict(self):
    """Test that from_dict class method creates a correct File instance."""
    new_instance = File.from_dict(self.file_data)
    self.assertEqual(new_instance, self.file_instance)


class NodeActionDataTest(TestCase):
  """Tests for the Node ActionData class."""

  def setUp(self):
    """Set up test data for Node tests."""
    self.node_data = {"nodeIP": "127.0.0.1", "port": 8000}
    self.node_instance = Node(**self.node_data)

  def test_to_dict(self):
    """Test that to_dict method returns the correct dictionary."""
    self.assertEqual(self.node_instance.to_dict(), self.node_data)

  def test_from_dict(self):
    """Test that from_dict class method creates a correct Node instance."""
    new_instance = Node.from_dict(self.node_data)
    self.assertEqual(new_instance, self.node_instance)
