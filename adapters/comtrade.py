import datetime
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient, rate_limited
from settings import COMTRADE_API_KEY

class ComtradeIndiaAdapter(DataSourceAdapter):
    """UN Comtrade API v1 with Reporter Code fixed to 356 (India)."""
    def __init__(self, api_key: str | None = None):
        self.client = BaseAPIClient()
        self.api_key = api_key or COMTRADE_API_KEY
        self.base_url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"

    @rate_limited(calls=1, period=2)
    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        # Expects params['hs_codes'] and params['years']
        records = []
        hs_codes_str = ",".join(params.get("hs_codes", []))
        years_str = ",".join(map(str, params.get("years", [datetime.date.today().year - 1])))
        
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        
        # Force reporterCode to 356 for India
        query = {
            "cmdCode": hs_codes_str, 
            "period": years_str, 
            "flowCode": "M,X", # Imports and Exports
            "reporterCode": "356" 
        }
        
        try:
            response = self.client.get(self.base_url, params=query, headers=headers)
            data = response.json().get("data", [])
            
            for record in data:
                records.append(RawRecord(
                    source_name="un_comtrade_india", 
                    raw_data=record, 
                    timestamp=datetime.datetime.now().isoformat()
                ))
        except Exception as e:
            print(f"Comtrade API Error: {e}")
            
        return records