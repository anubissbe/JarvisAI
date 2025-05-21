import os
import types
import unittest
from unittest.mock import patch

import document_processor

class DummySearcher:
    def __init__(self, *args, **kwargs):
        self.embedding_dim = 3
    def _initialize_vector_collection(self, kb_id):
        return True

class DummyCollection:
    inserted_data = None
    def __init__(self, name):
        self.name = name
    def load(self):
        pass
    def insert(self, data):
        DummyCollection.inserted_data = data
    def flush(self):
        pass
    def release(self):
        pass

def get_dummy_utility():
    return types.SimpleNamespace(has_collection=lambda name: True)

class AddVectorToMilvusTest(unittest.TestCase):
    def setUp(self):
        os.environ['NEO4J_PASSWORD'] = 'test'
        self.patcher_searcher = patch('document_processor.HybridSearch', DummySearcher)
        self.patcher_collection = patch('document_processor.Collection', DummyCollection)
        self.patcher_utility = patch('document_processor.utility', get_dummy_utility())
        self.patcher_searcher.start()
        self.patcher_collection.start()
        self.patcher_utility.start()

    def tearDown(self):
        self.patcher_searcher.stop()
        self.patcher_collection.stop()
        self.patcher_utility.stop()
        DummyCollection.inserted_data = None

    def test_embedding_mismatch_skips_insert(self):
        dp = document_processor.DocumentProcessor()
        with self.assertLogs('DocumentProcessor', level='WARNING') as cm:
            dp.add_vector_to_milvus('t', 'p', 'c', 'kb', [1, 2])
        self.assertIsNone(DummyCollection.inserted_data)
        self.assertTrue(any('Embedding dimension mismatch' in m for m in cm.output))

    def test_embedding_match_inserts(self):
        dp = document_processor.DocumentProcessor()
        dp.add_vector_to_milvus('t', 'p', 'c', 'kb', [1, 2, 3])
        self.assertIsNotNone(DummyCollection.inserted_data)

if __name__ == '__main__':
    unittest.main()
