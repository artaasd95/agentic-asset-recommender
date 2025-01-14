from fastapi import FastAPI, Request
import uvicorn
import logging
import sys

app = FastAPI()

# Just use Python’s built-in logger for demonstration
logger = logging.getLogger("fastapi-logs")
logger.setLevel(logging.INFO)

# Option 1: log to stdout so Promtail can scrape Docker logs.
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

@app.post("/logs")
async def handle_logs(request: Request):
    try:
        log_data = await request.json()
        # Format however you want
        msg = (
            f"[{log_data.get('logLevel')}] "
            f"{log_data.get('loggerName')} - "
            f"{log_data.get('message')} "
            f"(File: {log_data.get('filename')}, line {log_data.get('lineNo')})"
        )
        logger.info(msg)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Exception in /logs: {e}")
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
