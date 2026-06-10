from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

import ingest

LOGGER = logging.getLogger("lead_generator")

app = FastAPI()


@app.on_event("startup")
def startup_event():
    logging.basicConfig(level=logging.INFO)
    LOGGER.info("Starting app and initialising resources...")
    ingest.init_resources()


@app.post("/ingest")
async def ingest_endpoint(request: Request):
    try:
        payload = await request.json()
    except Exception as exc:
        LOGGER.exception("Failed to read JSON payload: %s", exc)
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON payload"})

    try:
        res = ingest.process_and_store(payload)
    except (ValidationError, ValueError) as ve:
        # Return 422 with descriptive message
        LOGGER.warning("Validation failed: %s", ve)
        return JSONResponse(status_code=422, content={"detail": str(ve)})
    except Exception as exc:
        LOGGER.exception("Internal error during ingestion: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "internal server error: %s" % str(exc)})

    return JSONResponse(status_code=201, content={"artifact_id": res["artifact_id"], "artifact_type": res["artifact_type"], "status": "stored"})


@app.get("/health")
async def health():
    try:
        count = ingest.get_collection_count()
    except Exception as exc:
        LOGGER.exception("Health check failed: %s", exc)
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(exc)})

    return {"status": "ok", "collection_count": count}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)