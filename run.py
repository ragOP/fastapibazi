#!/usr/bin/env python3
"""
Simple script to run the YouTube Transcript FastAPI server
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Starting YouTube Transcript API...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("🔄 Server will auto-reload on file changes")
    print("-" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 