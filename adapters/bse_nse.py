import datetime
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord

# pip install nselib
from nselib import capital_market

class BseNseAdapter(DataSourceAdapter):
    """BSE/NSE corporate actions and announcements through nselib."""
    def __init__(self):
        # nselib doesn't require initialization or API keys
        pass

    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        records = []
        symbols = params.get("symbols", [])
        
        for symbol in symbols:
            try:
                # nselib requires a period parameter for this function
                df = capital_market.price_volume_and_deliverable_position_data(symbol=symbol, period='1M')
                
                # Convert the pandas DataFrame to a list of dicts for our RawRecords
                if df is not None and not df.empty:
                    data_dict = df.to_dict(orient="records")
                    for row in data_dict:
                        records.append(RawRecord(
                            source_name="nse_market_data",
                            raw_data=row,
                            timestamp=datetime.datetime.now().isoformat()
                        ))
            except Exception as e:
                print(f"Failed fetching data for {symbol}: {e}")
                
        return records

    