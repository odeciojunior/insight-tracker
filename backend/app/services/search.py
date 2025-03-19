from typing import List, Optional, Dict, Any
from elasticsearch import AsyncElasticsearch
from app.db.mongodb import get_mongodb
from app.models.insight import Insight

class SearchService:
    def __init__(self, es_client: AsyncElasticsearch):
        self.es = es_client
        self.index = "insights"

    async def search_insights(
        self,
        query: str,
        user_id: str,
        tags: Optional[List[str]] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """
        Search insights using Elasticsearch.
        """
        must_conditions = [
            {"term": {"user_id": user_id}},
            {"multi_match": {
                "query": query,
                "fields": ["title^2", "content", "tags^1.5"]
            }}
        ]

        if tags:
            must_conditions.append({"terms": {"tags": tags}})

        body = {
            "query": {
                "bool": {
                    "must": must_conditions
                }
            },
            "from": (page - 1) * size,
            "size": size,
            "highlight": {
                "fields": {
                    "title": {},
                    "content": {}
                }
            }
        }

        results = await self.es.search(index=self.index, body=body)
        return self._format_search_results(results)

    def _format_search_results(self, results: Dict) -> Dict[str, Any]:
        """Format Elasticsearch results."""
        hits = results["hits"]
        return {
            "total": hits["total"]["value"],
            "results": [
                {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "highlight": hit.get("highlight", {}),
                    **hit["_source"]
                }
                for hit in hits["hits"]
            ]
        }
