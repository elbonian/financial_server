#!/usr/bin/env python3
"""
Simple Financial Data Server
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).resolve().parent.parent / 'src'
sys.path.append(str(src_dir))

from financial_server.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)