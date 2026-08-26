# Industry Configuration Schema

Every industry configuration file (`configs/<industry>.yaml`) must contain:

*   **sector_name** (String): Human-readable name of the industry.
*   **hs_codes** (List[String]): Harmonized System codes for querying trade and customs databases.
*   **seed_entities** (List[String]): Major anchor companies to jumpstart the graph expansion.
*   **key_materials** (List[String]): Critical inputs to track for vulnerability.
*   **chokepoint_definitions** (List[String]): Known structural bottlenecks (technological or geographic).
*   **search_keywords** (List[String]): Semantic terms for NLP, web scraping, and news ingestion.