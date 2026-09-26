import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient

class DgftOgdAdapter(DataSourceAdapter):
    """Data.gov.in API for DGFT Export Controls and Denied Entities."""
    def __init__(self, api_key: str):
        self.client = BaseAPIClient()
        self.api_key = api_key
        # Example base URL for Data.gov.in APIs. 
        # You need the specific 'resource_id' for the DGFT dataset you are targeting.
        self.base_url = "https://api.data.gov.in/resource/{resource_id}"
        self.reference_path = Path(__file__).resolve().parent.parent / "data" / "dgft_reference.json"

    def _load_reference_records(self, search_query: str) -> List[RawRecord]:
        fallback_records = []
        if not self.reference_path.exists():
            return fallback_records
        try:
            with open(self.reference_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            query = search_query.strip().lower()
            for item in data:
                if not query or query in item.get("title", "").lower() or query in item.get("entity", "").lower():
                    fallback_records.append(RawRecord(
                        source_name="dgft_ogd",
                        raw_data=item,
                        timestamp=datetime.datetime.now().isoformat()
                    ))
        except Exception as e:
            print(f"Error loading DGFT reference data: {e}")
        return fallback_records

    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        # Expects params['resource_id'] (for the specific DGFT dataset) and params['search_query']
        records = []
        resource_id = params.get("resource_id")
        search_query = params.get("search_query", "")
        
        if not resource_id:
            return records

        url = self.base_url.format(resource_id=resource_id)
        query_params = {
            "api-key": self.api_key,
            "format": "json",
            "limit": 100
        }
        
        # If searching for a specific entity or term within the dataset
        if search_query:
            query_params["filters[title]"] = search_query # Adjust filter key based on actual dataset schema

        try:
            response = self.client.get(url, params=query_params, timeout=5)
            data = response.json()
            
            for item in data.get("records", []):
                records.append(RawRecord(
                    source_name="dgft_ogd", 
                    raw_data=item, 
                    timestamp=datetime.datetime.now().isoformat()
                ))
        except Exception as e:
            print(f"OGD API Error: {e}")

        # If live API timed out or returned no records, fall back to official reference snapshot
        if not records:
            records = self._load_reference_records(search_query)
                
        return records