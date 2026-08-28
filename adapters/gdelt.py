import datetime
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient

class GdeltAdapter(DataSourceAdapter):
    """GDELT DOC API for geopolitical signals."""
    def __init__(self):
        self.client = BaseAPIClient()
        self.base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        # Expects params['keywords']
        keywords = params.get("keywords", [])
        query = " OR ".join([f'"{kw}"' for kw in keywords])
        
        payload = {"query": query, "mode": "artlist", "maxrecords": 250, "format": "json"}
        response = self.client.get(self.base_url, params=payload)
        
        articles = response.json().get("articles", [])
        return [RawRecord(source_name="gdelt", raw_data=art, timestamp=datetime.datetime.now().isoformat()) for art in articles]