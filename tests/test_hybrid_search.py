from hybrid_search.hybrid_search import HybridSearch


def make_searcher():
    return HybridSearch.__new__(HybridSearch)


def test_extract_query_terms_basic():
    searcher = make_searcher()
    query = "How to use Python for data processing?"
    terms = searcher._extract_query_terms(query)
    assert terms == ["Use", "Python", "Data", "Processing"]


def test_extract_query_terms_filters_stopwords():
    searcher = make_searcher()
    query = "What can you tell me about AI and ML?"
    terms = searcher._extract_query_terms(query)
    assert "What" not in terms and "You" not in terms
    assert "Ai" in terms and "Ml" in terms

