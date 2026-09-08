import datetime
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient

class MinesOgdAdapter(DataSourceAdapter):
    """Data.gov.in API for Ministry of Mines / Indian Bureau of Mines production data."""
    def __init__(self, api_key: str | None = None):
        self.client = BaseAPIClient()
        self.api_key = api_key or ""
        # The specific resource_id for mineral production statistics
        self.base_url = "https://api.data.gov.in/resource/{resource_id}"

    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        # Expects params['resource_id'] and params['materials']
        records = []
        resource_id = params.get("resource_id")
        materials = params.get("materials", [])
        
        if not resource_id:
            return records

        url = self.base_url.format(resource_id=resource_id)
        
        for material in materials:
            query_params = {
                "api-key": self.api_key,
                "format": "json",
                "limit": 50,
                # Filtering by material name (adjust the exact field name based on the OGD dataset schema)
                "filters[mineral_name]": material 
            }
            
            try:
                response = self.client.get(url, params=query_params)
                data = response.json()
                
                for item in data.get("records", []):
                    records.append(RawRecord(
                        source_name="mines_ogd", 
                        raw_data=item, 
                        timestamp=datetime.datetime.now().isoformat()
                    ))
            except Exception as e:
                print(f"Mines OGD API Error for {material}: {e}")
                
        return records