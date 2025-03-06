#!/usr/bin/env python
"""
PACS Imago Radiologia API
This module provides a FastAPI-based API for the PACS Imago Radiologia automation.
"""
import os
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
from login_automation import login_to_pacs

# Load environment variables
load_dotenv()

app = FastAPI(
    title="PACS Imago Radiologia API",
    description="API for automating interactions with the PACS Imago Radiologia system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class LoginCredentials(BaseModel):
    username: str
    password: str

class FilterOptions(BaseModel):
    grupo_totem: Optional[str] = "Selecione um grupo totem"
    guiche: Optional[str] = "Selecione um guichê"
    tipo: Optional[str] = "Selecione um tipo"
    prioridade: Optional[str] = "Selecione uma prioridade"
    modalidade: Optional[str] = "Selecione uma modalidade"

class ScrapingRequest(BaseModel):
    credentials: LoginCredentials
    filter_options: Optional[FilterOptions] = None
    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 800

# In-memory storage for background task results
task_results = {}

@app.get("/")
async def root():
    """Root endpoint that returns API information."""
    return {
        "name": "PACS Imago Radiologia API",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "API information"},
            {"path": "/scrape", "method": "POST", "description": "Scrape data from PACS system"},
            {"path": "/tasks/{task_id}", "method": "GET", "description": "Get status of a background task"},
        ]
    }

async def run_scraping_task(task_id: str, request: ScrapingRequest):
    """Background task to run the scraping process."""
    try:
        # Set credentials from request or environment variables
        if request.credentials:
            os.environ["j_username"] = request.credentials.username
            os.environ["j_password"] = request.credentials.password
        
        # Call the automation function with parameters
        result = await login_to_pacs(
            headless=request.headless,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            filter_options={
                "grupo_totem": request.filter_options.grupo_totem if request.filter_options else "Selecione um grupo totem",
                "guiche": request.filter_options.guiche if request.filter_options else "Selecione um guichê",
                "tipo": request.filter_options.tipo if request.filter_options else "Selecione um tipo",
                "prioridade": request.filter_options.prioridade if request.filter_options else "Selecione uma prioridade",
                "modalidade": request.filter_options.modalidade if request.filter_options else "Selecione uma modalidade",
            } if request.filter_options else None
        )
        
        # Store the result
        task_results[task_id] = {
            "status": "completed",
            "data": result,
            "completed_at": datetime.now().isoformat()
        }
    except Exception as e:
        # Store the error
        task_results[task_id] = {
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        }

@app.post("/scrape")
async def scrape_data(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to initiate data scraping from the PACS system.
    This runs as a background task and returns a task ID for checking status.
    
    Required parameters:
    - credentials: LoginCredentials with username and password for PACS login
    
    Optional parameters:
    - filter_options: Filter options for the scraping
    - headless: Whether to run browser in headless mode
    - viewport_width: Width of browser viewport
    - viewport_height: Height of browser viewport
    """
    # Validate credentials
    if not request.credentials or not request.credentials.username or not request.credentials.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    # Generate a task ID
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(task_results) + 1}"
    
    # Initialize task status
    task_results[task_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat()
    }
    
    # Start the background task
    background_tasks.add_task(run_scraping_task, task_id, request)
    
    return {
        "task_id": task_id,
        "status": "running",
        "message": "Scraping task started in the background"
    }

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a background task by its ID."""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return task_results[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
