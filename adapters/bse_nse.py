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
        # Expects params['symbols'] (e.g., "TATASTEEL") and optional date range
        records: List[RawRecord] = []
        symbols = params.get("symbols", [])
        from_date = params.get("from_date")
        to_date = params.get("to_date")

        try:
            if from_date or to_date:
                announcements_df = capital_market.corporate_actions_for_equity(
                    from_date=from_date,
                    to_date=to_date,
                )
            else:
                announcements_df = capital_market.corporate_actions_for_equity()

            if announcements_df is None or announcements_df.empty:
                return records

            for symbol in symbols:
                symbol_announcements = announcements_df[announcements_df['symbol'] == symbol]
                for _, row in symbol_announcements.iterrows():
                    records.append(RawRecord(
                        source_name="nse_announcements",
                        raw_data=row.to_dict(),
                        timestamp=datetime.datetime.now().isoformat()
                    ))

        except Exception as e:
            for symbol in symbols:
                print(f"Failed fetching data for {symbol}: {e}")

        return records