import datetime
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient

class ComtradeIndiaAdapter(DataSourceAdapter):
    """UN Comtrade API v1 Adapter specifically configured for India (Reporter Code: 356)."""
    def __init__(self, api_key: str):
        self.client = BaseAPIClient()
        self.api_key = api_key
        # Comtrade v1 endpoint for Annual, HS-classification data
        self.base_url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"

    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        records = []
        hs_codes = params.get("hs_codes", [])
        years = params.get("years", [])
        
        if not hs_codes or not years:
            print("Comtrade Adapter: Missing hs_codes or years in params.")
            return records

        # UN Comtrade expects the key in the Ocp-Apim-Subscription-Key header
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }

        # Format parameters for the Comtrade API
        # India's reporterCode in Comtrade goods is 699 (historical/primary) and 356 (M49)
        query_params = {
            "reporterCode": params.get("reporter_code", "699,356"),
            "period": ",".join(map(str, years)),
            "cmdCode": ",".join(hs_codes),
            "flowCode": params.get("flow_code", "M"),
            "subscription-key": self.api_key
        }
        if "partner_code" in params:
            query_params["partnerCode"] = str(params["partner_code"])
        
        try:
            response = self.client.get(self.base_url, params=query_params, headers=headers, timeout=30)
            data = response.json()
            
            for item in data.get("data", []):
                records.append(RawRecord(
                    source_name="un_comtrade_in", 
                    raw_data=item, 
                    timestamp=datetime.datetime.now().isoformat()
                ))
                
        except Exception as e:
            print(f"Comtrade Network Error: {e}")
            
        return records