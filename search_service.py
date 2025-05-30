
from search_structured import StructuredSearch
from search_semantic import SemanticSearch

class SearchService:
    def __init__(self, Session, vector_store):
        self.structured = StructuredSearch(Session)
        self.semantic = SemanticSearch(vector_store)


    # ─── search_service.py (فقط همین خط) ───────────────────────────────────────
    def structured_search(self, neighborhood=None, max_price=None, min_sqft=None):
        return self.structured.search(neighborhood, max_price, min_sqft)



    # def structured_search(self, city, max_price=None, min_area=None):
    #     return self.structured.search(city, max_price, min_area)

    def semantic_search(self, query: str, k: int = 5, **filters):
        """
        اگر فیلترهایی مثل city یا price داشتیم اینجا به semantic_search پاس دهیم.
        """
        return self.semantic.search(query, k, filter_dict=filters or None)
    
    
    # def semantic_search(self, query, k=5):
    #     return self.semantic.search(query, k)