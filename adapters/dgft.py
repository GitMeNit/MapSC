import datetime
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
            response = self.client.get(url, params=query_params)
            data = response.json()
            
            for item in data.get("records", []):
                records.append(RawRecord(
                    source_name="dgft_ogd", 
                    raw_data=item, 
                    timestamp=datetime.datetime.now().isoformat()
                ))
        except Exception as e:
            print(f"OGD API Error: {e}")
                
        return records