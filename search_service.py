# search_service.py
from search_structured import StructuredSearch
from search_semantic  import SemanticSearch

class SearchService:
    def __init__(self, listings_collection, vector_store, semantic_layer):
        self.structured   = StructuredSearch(listings_collection)
        self.vector_store = vector_store
        self.sem          = semantic_layer

    # لایهٔ ساختاری
    def structured_search(self, **kwargs):
        return self.structured.search(**kwargs)

    # لایهٔ معنایی
    def semantic_search(self, query: str, k: int = 5, **filters):
        return self.sem.search(query, k, filter_dict=filters or None)

    
    
    # def semantic_search(self, query, k=5):
    #     return self.semantic.search(query, k)
