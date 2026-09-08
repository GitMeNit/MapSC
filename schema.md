# Generic Supply Chain Graph Schema

## Node Types
*   **Company**: Corporate entities involved in the supply chain (e.g., manufacturers, suppliers).
*   **Facility**: Physical operational locations (e.g., factories, mines, ports).
*   **Material**: Raw, processed, or refined inputs.
*   **Product**: Manufactured goods, components, or sub-assemblies.
*   **Country**: Geopolitical jurisdictions for risk and trade mapping.

## Edge Types (Relationships)
*   **supplies_to** (Source: Company/Facility → Target: Company/Facility): Represents trade flow, contracts, or logistics.
*   **depends_on** (Source: Product/Material → Target: Material/Product): Represents the Bill of Materials (BOM) hierarchy.
*   **located_in** (Source: Company/Facility → Target: Country): Geographic and jurisdictional mapping.
*   **produces** (Source: Company/Facility → Target: Product/Material): Manufacturing, extraction, or refining capability.