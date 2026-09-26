import pytest
from unittest.mock import patch, MagicMock
from adapters.base import RawRecord
from adapters.bse_nse import BseNseAdapter
from adapters.dgft import DgftOgdAdapter
from adapters.ibm_mines import MinistryOfMinesOgdAdapter
from adapters.ip_india import GooglePatentsBigQueryAdapter
from adapters.comtrade import ComtradeIndiaAdapter

# --- MOCK DATA FIXTURES ---

@pytest.fixture
def mock_nselib_df():
    import pandas as pd
    # Simulating nselib's corporate announcement dataframe
    data = {
        'symbol': ['TATASTEEL', 'RELIANCE', 'TATASTEEL'],
        'subject': ['Dividend', 'AGM', 'Board Meeting'],
        'date': ['2023-01-01', '2023-01-02', '2023-01-03']
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_api_response():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "records": [
            {"title": "Export restriction on sensitive materials", "entity": "Test Entity"},
            {"title": "Policy update 2024", "entity": "Other Entity"}
        ],
        "data": [
            {"cmdCode": "8542", "period": 2023, "tradeValue": 100000}
        ]
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp

@pytest.fixture
def mock_bq_results():
    # Simulating a BigQuery RowIterator
    row1 = MagicMock()
    row1.__iter__.return_value = [
        ('publication_number', 'IN-123456-A'), 
        ('assignee_harmonized', [{'name': 'TATA ELECTRONICS'}])
    ]
    # Emulate dict(row) behavior
    row1.keys.return_value = ['publication_number', 'assignee_harmonized']
    row1.__getitem__.side_effect = lambda k: dict(row1.__iter__())[k]
    
    return [row1]


# --- ADAPTER TESTS ---

@patch('adapters.bse_nse.capital_market.price_volume_and_deliverable_position_data')
def test_bse_nse_adapter(mock_price_data, mock_nselib_df):
    # Setup mock
    mock_price_data.return_value = mock_nselib_df

    # Run test
    adapter = BseNseAdapter()
    records = adapter.fetch({"symbols": ["TATASTEEL"]})
    
    # Assertions
    assert len(records) == 3
    assert isinstance(records[0], RawRecord)
    assert records[0].source_name == "nse_market_data"
    assert records[0].raw_data["subject"] == "Dividend"

@patch('adapters.dgft.BaseAPIClient')
def test_dgft_ogd_adapter(mock_api_client_class, mock_api_response):
    mock_instance = mock_api_client_class.return_value
    mock_instance.get.return_value = mock_api_response
    
    adapter = DgftOgdAdapter(api_key="fake_key")
    records = adapter.fetch({"resource_id": "test_id", "search_query": "Test Entity"})
    
    assert len(records) == 2
    assert records[0].source_name == "dgft_ogd"
    assert records[0].raw_data["title"] == "Export restriction on sensitive materials"
    # Ensure correct parameters were passed to the HTTP client
    mock_instance.get.assert_called_once()
    args, kwargs = mock_instance.get.call_args
    assert "filters[title]" in kwargs["params"]
    assert kwargs["params"]["api-key"] == "fake_key"

@patch('adapters.ibm_mines.BaseAPIClient')
def test_ibm_mines_adapter(mock_api_client_class, mock_api_response):
    mock_instance = mock_api_client_class.return_value
    mock_instance.get.return_value = mock_api_response
    
    adapter = MinistryOfMinesOgdAdapter(api_key="fake_key")
    records = adapter.fetch({"resource_id": "test_id", "materials": ["Lithium"]})
    
    assert len(records) == 2
    assert records[0].source_name == "ibm_ogd"
    mock_instance.get.assert_called_once()
    args, kwargs = mock_instance.get.call_args
    assert kwargs["params"]["filters[mineral_name]"] == "Lithium"

@patch('adapters.ip_india.bigquery.Client')
def test_google_patents_bq_adapter(mock_bq_client_class, mock_bq_results):
    mock_instance = mock_bq_client_class.return_value
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = mock_bq_results
    mock_instance.query.return_value = mock_query_job
    
    adapter = GooglePatentsBigQueryAdapter(project_id="test_project")
    records = adapter.fetch({"seed_entities": ["Tata Electronics"]})
    
    assert len(records) == 1
    assert records[0].source_name == "google_patents_bq_in"
    # Verify the SQL query injected the uppercase entity name
    args, kwargs = mock_instance.query.call_args
    assert "TATA ELECTRONICS" in args[0]

@patch('adapters.comtrade.BaseAPIClient')
def test_comtrade_india_adapter(mock_api_client_class, mock_api_response):
    mock_instance = mock_api_client_class.return_value
    mock_instance.get.return_value = mock_api_response
    
    adapter = ComtradeIndiaAdapter(api_key="fake_key")
    records = adapter.fetch({"hs_codes": ["8542"], "years": [2023]})
    
    assert len(records) == 1
    assert records[0].source_name == "un_comtrade_in"
    assert records[0].raw_data["cmdCode"] == "8542"
    
    args, kwargs = mock_instance.get.call_args
    assert "356" in kwargs["params"]["reporterCode"] # Verifying India is queried
    assert kwargs["params"]["cmdCode"] == "8542"