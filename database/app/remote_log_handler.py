# client/remote_log_handler.py
import logging
import json
import requests

class RemoteLogHandler(logging.Handler):
    """
    A custom log handler that sends logs to a FastAPI server via HTTP POST.
    """
    def __init__(self, endpoint_url: str):
        super().__init__()
        self.endpoint_url = endpoint_url

    def emit(self, record):
        try:
            # Format the log record
            log_entry = self.format(record)
            
            # Construct the payload
            payload = {
                "loggerName": record.name,
                "logLevel": record.levelname,
                "message": log_entry,
                "filename": record.filename,
                "lineNo": record.lineno,
                "created": record.created,  # Unix timestamp
            }

            # Send the log via HTTP POST
            # You could also add "extra" fields if needed
            requests.post(
                self.endpoint_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=2
            )
        except Exception:
            # Avoid infinite loop if logging fails
            pass
