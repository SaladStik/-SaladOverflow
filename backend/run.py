#!/usr/bin/env python3
"""
Development server startup script for SaladOverflow API
"""
import os
import uvicorn

# Force UTC timezone for the entire application
os.environ["TZ"] = "UTC"

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
