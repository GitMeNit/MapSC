from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class RawRecord:
    """Generic container for raw data before graph transformation."""
    source_name: str
    raw_data: Dict[str, Any]
    timestamp: str

class DataSourceAdapter(ABC):
    """Abstract base class for all external data ingestion."""
    
    @abstractmethod
    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        """
        Fetch data based on provided parameters (e.g., keywords, HS codes).
        Returns a list of generic RawRecord objects.
        """
        pass