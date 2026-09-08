import datetime
from typing import List, Dict, Any
from adapters.base import DataSourceAdapter, RawRecord

# pip install google-cloud-bigquery
from google.cloud import bigquery

class GooglePatentsIndiaAdapter(DataSourceAdapter):
    """Queries Google Patents Public Datasets on BigQuery for Indian (IN) assignees."""
    def __init__(self, project_id: str):
        # Assumes you have set up GCP credentials locally (GOOGLE_APPLICATION_CREDENTIALS)
        self.client = bigquery.Client(project=project_id)

    def fetch(self, params: Dict[str, Any]) -> List[RawRecord]:
        # Expects params['seed_entities']
        records = []
        entities = params.get("seed_entities", [])
        
        if not entities:
            return records

        # Construct a SQL query looking for IN patents assigned to the seed entities
        # Warning: Standardize entity names before querying for best results
        entity_list_str = ", ".join([f"'{entity.upper()}'" for entity in entities])
        
        query = f"""
            SELECT 
                publication_number,
                title_localized,
                assignee_harmonized,
                filing_date
            FROM 
                `patents-public-data.patents.publications`
            WHERE 
                country_code = 'IN'
                # Unnesting the assignee array to check for matches
                AND EXISTS (
                    SELECT 1 
                    FROM UNNEST(assignee_harmonized) AS assignee 
                    WHERE UPPER(assignee.name) IN ({entity_list_str})
                )
            LIMIT 1000
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            for row in results:
                # Convert BigQuery Row object to dict
                row_dict = dict(row)
                # Convert dates/arrays to strings/lists for serialization
                if 'title_localized' in row_dict:
                     row_dict['title'] = row_dict['title_localized'][0]['text'] if row_dict['title_localized'] else ""
                     del row_dict['title_localized']
                
                records.append(RawRecord(
                    source_name="google_patents_in", 
                    raw_data=row_dict, 
                    timestamp=datetime.datetime.now().isoformat()
                ))
        except Exception as e:
            print(f"BigQuery Error: {e}")
            
        return records