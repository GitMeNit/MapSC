import datetime
import json
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient

class IpIndiaAdapter(DataSourceAdapter):
    """Indian Patent Office (IPO / CGPDTM) assignee query adapter."""
    def __init__(self):
        self.client = BaseAPIClient()
        # Proxying via a global patent aggregator focused on IN patents, or a direct scraper
        self.base_url = "https://api.patentdata.in/v1/assignee/search"

    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        records = []
        
        for entity in params.get("seed_entities", []):
            response = self.client.get(self.base_url, params={"applicant_name": entity, "jurisdiction": "IN"})
            results = response.json().get("patents", [])
            if results:
                records.append(RawRecord(
                    source_name="ip_india", 
                    raw_data={"entity": entity, "patent_count": len(results), "top_patents": results[:5]}, 
                    timestamp=datetime.datetime.now().isoformat()
                ))
                
        return records