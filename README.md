# Lead Generator

Lead Generator is a FastAPI-based retrieval and analysis service for browser artifacts such as history, search records, downloads, and bookmarks. It stores artifact data in ChromaDB, embeds it with a sentence-transformer model, and can answer investigator questions with optional LLM-based query decomposition.

## Features

- Ingest browser-derived artifacts via `/ingest`
- Query by `autopsy_case_id`, artifact type, and `top_k`
- Optional `use_decomposition` query decomposition mode
- Timeline and anomaly extraction for investigation summaries
- Synthetic dataset generators for evaluation scenarios

## Requirements

- Python 3.10+
- A virtual environment
- Access to an LLM endpoint configured through environment variables

## Setup

1. Open a terminal in the project root.
2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the required LLM settings:

```env
LLM_BASE_URL=https://your-llm-endpoint
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o-mini
LLM_MAX_TOKENS=1000
LLM_REQUEST_TIMEOUT=200
```

If your deployment does not use the environment variables, the app will still start, but query decomposition and LLM-backed analysis may fail.

## Start the server

From the project root:

```bash
PYTHONPATH=src .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

This starts the API on:

- http://localhost:8000
- Health check: http://localhost:8000/health

You can also run the app directly from the `src` folder if needed, but the `PYTHONPATH=src` pattern is the standard setup used here.

## Basic usage

### Health check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{ "status": "ok", "collection_count": 0 }
```

### Ingest an artifact

Send a POST request to `/ingest` with a browser artifact payload. Example:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_type": "search",
    "browser": "chrome",
    "browser_profile": "Default",
    "source_db_path": "C:/Users/test/AppData/Local/Google/Chrome/User Data/Default/History",
    "source_db_hash": "abc123",
    "os_user_account": "testuser",
    "autopsy_case_id": "CASE-2024-001",
    "search_term": "best cloud storage no logs",
    "search_engine": "DuckDuckGo",
    "search_timestamp": "2024-06-12T10:52:00Z",
    "result_url": "https://www.duckduckgo.com/?q=best+cloud+storage+no+logs"
  }'
```

The response includes an `artifact_id` for the stored item.

### Query the database

Use the `/query` endpoint with a question and case ID.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Did this user show intent to exfiltrate data?",
    "autopsy_case_id": "CASE-2024-001",
    "top_k": 10,
    "artifact_types": ["search", "history", "download"],
    "use_decomposition": true
  }'
```

Key fields:

- `question`: natural language investigator question
- `autopsy_case_id`: case identifier to search within
- `top_k`: max number of artifacts to retrieve per query
- `artifact_types`: optional artifact filter
- `use_decomposition`: enables decomposed multi-query retrieval

## Synthetic datasets

This repo includes two sample dataset scripts:

- `synthetic_dataset_1.py`
- `synthetic_dataset_2.py`

These scripts generate realistic browser artifact data, ingest it into the running service, and execute evaluation queries against the server.

### Run a synthetic dataset

Make sure the server is running first, then run:

```bash
python3 synthetic_dataset_1.py
```

or:

```bash
python3 synthetic_dataset_2.py
```

These scripts create outputs in:

- `test_output/`
- `test_output_fraud/`

and also populate the ChromaDB indexes used by the app.

## Project layout

```text
.
├── README.md
├── requirements.txt
├── synthetic_dataset_1.py
├── synthetic_dataset_2.py
├── src/
│   ├── app.py
│   ├── ingest.py
│   ├── main.py
│   ├── models.py
│   ├── query.py
│   └── templates/
├── chroma_db/
├── datasets/
├── llm_outputs_reports/
├── test_output/
├── test_output_fraud/
└── .env
```

## Typical workflow

1. Start the API server.
2. Check `/health` to verify the collection is ready.
3. Post artifacts to `/ingest`.
4. Query the collection with `/query` using a case ID and a question.
5. Use the synthetic scripts to generate and evaluate example cases.

## Notes

- The app uses ChromaDB persistence under `./chroma_db`.
- Generated output files and vector store directories are useful for debugging and benchmarking.
- Keep the `.env` file local and do not commit secrets to source control.
