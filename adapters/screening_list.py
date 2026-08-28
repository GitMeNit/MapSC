import datetime
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient

class ConsolidatedScreeningAdapter(DataSourceAdapter):
    """Trade.gov API for denied parties / export controls."""
    def __init__(self, api_key: str):
        self.client = BaseAPIClient()
        self.api_key = api_key
        self.base_url = "https://api.trade.gov/v1/consolidated_screening_list/search"

    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        # Expects params['seed_entities']
        records = []
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        for entity in params.get("seed_entities", []):
            response = self.client.get(self.base_url, params={"name": entity}, headers=headers)
            hits = response.json().get("results", [])
            for hit in hits:
                records.append(RawRecord(source_name="trade_gov_csl", raw_data=hit, timestamp=datetime.datetime.now().isoformat()))
                
        return records