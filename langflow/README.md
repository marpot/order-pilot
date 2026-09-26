# OrderPilot Langflow foundation

Langflow is an optional enrichment layer. OrderPilot always runs deterministic extraction first and only calls Langflow when required order fields are missing. Every Langflow response is validated by Pydantic before an order can be persisted. A failure or timeout returns the deterministic result with `NEEDS_REVIEW`.

## Local setup

1. Start the optional service: `docker compose --profile ai up -d langflow`.
2. Open <http://localhost:7860> and create a flow with Chat Input and Chat Output.
3. Use `prompts/order-extraction.md` as the system instruction.
4. Configure the model provider key inside Langflow, not in this repository.
5. Make the Chat Output return only JSON matching `structured-output.schema.json`.
6. Copy the flow ID and an API key to your local `.env`, then set `LANGFLOW_ENABLED=true`.
7. Restart the backend.

The backend calls `POST /api/v1/run/{flow_id}` and accepts the standard Langflow Chat Output response or a direct `result` object.

## Minimal RAG extension

`knowledge/product_catalog.csv` is a deliberately small example knowledge source. Add a File component, split rows into documents, embed them with the selected provider, and connect a small vector store retriever to the extraction prompt. Retrieve only a few matching product rows. Use retrieved catalog data to resolve aliases and validate SKUs, never to invent missing quantities or customer data.

Recommended next knowledge fields are canonical SKU, aliases, product name, default unit, minimum order quantity, and handling notes. Production knowledge should come from a controlled catalog export and include a refresh process.
