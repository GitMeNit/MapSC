import datetime
import json
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient

class PatentsViewAdapter(DataSourceAdapter):
    """PatentsView API to gauge IP concentration."""
    def __init__(self):
        self.client = BaseAPIClient()
        self.base_url = "https://api.patentsview.org/assignees/query"

    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        # Expects params['seed_entities']
        records = []
        
        for entity in params.get("seed_entities", []):
            # Query looks for the assignee organization name matching the seed entity
            query = {"_contains": {"assignee_organization": entity}}
            payload = {"q": json.dumps(query), "f": '["assignee_id", "assignee_organization", "assignee_total_num_patents"]'}
            
            response = self.client.get(self.base_url, params=payload)
            results = response.json().get("assignees", [])
            if results:
                records.append(RawRecord(source_name="patentsview", raw_data=results[0], timestamp=datetime.datetime.now().isoformat()))
                
        return records