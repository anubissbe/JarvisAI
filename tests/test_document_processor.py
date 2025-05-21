import os
import tempfile
import unittest

from document_processor import DocumentProcessor

class TestExtractKbId(unittest.TestCase):
    def setUp(self):
        # Use temporary directories for environment paths
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ['UPLOADS_DIR'] = os.path.join(self.temp_dir.name, 'uploads')
        os.environ['PROCESSED_DIR'] = os.path.join(self.temp_dir.name, 'processed')
        os.environ['CONFIG_DIR'] = os.path.join(self.temp_dir.name, 'config')
        os.makedirs(os.environ['UPLOADS_DIR'], exist_ok=True)
        os.makedirs(os.environ['PROCESSED_DIR'], exist_ok=True)
        os.makedirs(os.environ['CONFIG_DIR'], exist_ok=True)
        os.environ['NEO4J_PASSWORD'] = 'dummy'
        self.processor = DocumentProcessor()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_lowercase_uuid(self):
        uuid_lower = '123e4567-e89b-12d3-a456-426614174000'
        path = os.path.join('some', 'path', 'uploads', uuid_lower, 'file.txt')
        kb_id = self.processor.extract_kb_id_from_path(path)
        self.assertEqual(kb_id, uuid_lower)

    def test_uppercase_uuid(self):
        uuid_upper = '123E4567-E89B-12D3-A456-426614174000'
        path = os.path.join('another', 'path', 'uploads', uuid_upper, 'file.txt')
        kb_id = self.processor.extract_kb_id_from_path(path)
        self.assertEqual(kb_id, uuid_upper)

if __name__ == '__main__':
    unittest.main()
