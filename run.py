#!/usr/bin/env python3
"""Convenience script to run ETL Pipeline"""

import sys
import os
import uvicorn

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    #main()
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
