import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient

class MinistryOfMinesOgdAdapter(DataSourceAdapter):
    """Data.gov.in API for Ministry of Mines / Indian Bureau of Mines production data."""
    def __init__(self, api_key: str):
        self.client = BaseAPIClient()
        self.api_key = api_key
        # The specific resource_id for mineral production statistics
        self.base_url = "https://api.data.gov.in/resource/{resource_id}"
        self.reference_path = Path(__file__).resolve().parent.parent / "data" / "mines_reference.json"

    def _load_reference_records(self, materials: List[str]) -> List[RawRecord]:
        fallback_records = []
        if not self.reference_path.exists():
            return fallback_records
        try:
            with open(self.reference_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            mat_set = {m.strip().lower() for m in materials if m.strip()}
            for item in data:
                min_name = item.get("mineral_name", "").lower()
                if not mat_set or any(m in min_name for m in mat_set):
                    fallback_records.append(RawRecord(
                        source_name="ibm_ogd",
                        raw_data=item,
                        timestamp=datetime.datetime.now().isoformat()
                    ))
        except Exception as e:
            print(f"Error loading Mines reference data: {e}")
        return fallback_records

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
                response = self.client.get(url, params=query_params, timeout=5)
                data = response.json()
                
                for item in data.get("records", []):
                    records.append(RawRecord(
                        source_name="ibm_ogd", 
                        raw_data=item, 
                        timestamp=datetime.datetime.now().isoformat()
                    ))
            except Exception as e:
                print(f"Mines OGD API Error for {material}: {e}")

        # If live API timed out or returned no records, fall back to official reference snapshot
        if not records:
            records = self._load_reference_records(materials)
                
        return records