import datetime
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord
from adapters.cache import BaseAPIClient

class EdgarAdapter(DataSourceAdapter):
    """SEC EDGAR API for company facts."""
    def __init__(self, user_agent: str):
        self.client = BaseAPIClient()
        self.user_agent = user_agent
        self.base_url = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        # Expects params['ciks'] 
        records = []
        headers = {"User-Agent": self.user_agent}
        
        for cik in params.get("ciks", []):
            padded_cik = str(cik).zfill(10)
            url = self.base_url.format(cik=padded_cik)
            try:
                response = self.client.get(url, headers=headers)
                records.append(RawRecord(source_name="sec_edgar", raw_data={"cik": cik, "facts": response.json()}, timestamp=datetime.datetime.now().isoformat()))
            except Exception as e:
                pass # In production, log CIK not found
                
        return records