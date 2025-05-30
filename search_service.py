from search_structured import StructuredSearch
from search_semantic   import SemanticSearch

class SearchService:
    def __init__(self, Session, vector_store, semantic_layer):
        # StructuredSearch به Session نیاز داره
        self.structured    = StructuredSearch(Session)
        # خودِ vector_store (مثلاً Faiss, Pinecone, Chroma، …)
        self.vector_store  = vector_store
        # و لایه‌ی آماده‌ی SemanticSearch
        self.sem           = semantic_layer

    def structured_search(self, neighborhood=None, max_price=None, min_sqft=None):
        return self.structured.search(neighborhood, max_price, min_sqft)

    def semantic_search(self, query: str, k: int = 5, **filters):
        # اگر نیاز بود مستقیماً از vector_store چیزی بخونید،
        # الان self.vector_store در دسترس‌تون هست.
        return self.sem.search(query, k, filter_dict=filters or None)

    
    
    # def semantic_search(self, query, k=5):
    #     return self.semantic.search(query, k)
