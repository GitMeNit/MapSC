import datetime
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient, rate_limited

class ComtradeAdapter(DataSourceAdapter):
    """UN Comtrade API wrapper for bilateral trade flows."""
    def __init__(self, api_key: str):
        self.client = BaseAPIClient()
        self.api_key = api_key
        self.base_url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"

    @rate_limited(calls=1, period=2) # Comtrade is strict
    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        # Expects params['hs_codes'] and params['years']
        hs_codes_str = ",".join(params.get("hs_codes", []))
        years_str = ",".join(map(str, params.get("years", [datetime.date.today().year - 1])))
        
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        query = {"cmdCode": hs_codes_str, "period": years_str, "flowCode": "M,X"} # Imports, Exports
        
        response = self.client.get(self.base_url, params=query, headers=headers)
        data = response.json().get("data", [])
        
        return [RawRecord(source_name="un_comtrade", raw_data=record, timestamp=datetime.datetime.now().isoformat()) for record in data]