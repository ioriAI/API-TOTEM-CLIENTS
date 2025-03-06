#!/usr/bin/env python
"""
PACS Imago Radiologia API
This module provides a FastAPI-based API for the PACS Imago Radiologia automation.
"""
import os
import json
import uuid
import asyncio
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from login_automation import login_to_pacs

# Load environment variables
load_dotenv()

# Dictionary to store task status
task_storage = {}

app = FastAPI(
    title="PACS IMAGO - TOTEM API",
    description="API for NETRIS' TOTEM - Version: 1.0.0"
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
class FilterOptions(BaseModel):
    grupo_totem: Optional[str] = "Selecione um grupo totem"
    guiche: Optional[str] = "Selecione um guichê"
    tipo: Optional[str] = "Selecione um tipo"
    prioridade: Optional[str] = "Selecione uma prioridade"
    modalidade: Optional[str] = "Selecione uma modalidade"

class ScrapingRequest(BaseModel):
    j_username: str = Field(..., description="Username for PACS login")
    j_password: str = Field(..., description="Password for PACS login")
    filter_options: Optional[FilterOptions] = None
    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 800

async def run_scraping_task(task_id: str, request: ScrapingRequest):
    """Background task to run the scraping process"""
    try:
        # Temporarily set environment variables for login function
        os.environ["j_username"] = request.j_username
        os.environ["j_password"] = request.j_password
        
        # Call the automation function with parameters
        filter_options = None
        if request.filter_options:
            filter_options = {
                "grupo_totem": request.filter_options.grupo_totem,
                "guiche": request.filter_options.guiche,
                "tipo": request.filter_options.tipo,
                "prioridade": request.filter_options.prioridade,
                "modalidade": request.filter_options.modalidade,
            }
        
        # Run the automation and get results
        result = await login_to_pacs(
            headless=request.headless,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            filter_options=filter_options
        )
        
        # Clear environment variables after use
        os.environ.pop("j_username", None)
        os.environ.pop("j_password", None)
        
        # Update task status with result
        task_storage[task_id] = result
        
    except Exception as e:
        # Update task status with error
        task_storage[task_id] = {
            "status": "failed",
            "message": str(e),
            "data": []
        }

@app.get("/")
async def root():
    """Root endpoint that returns API information."""
    return {
        "name": "PACS Imago Radiologia API",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "API information"},
            {"path": "/scrape", "method": "POST", "description": "Scrape data from PACS system (asynchronous)"},
            {"path": "/scrape_sync", "method": "POST", "description": "Scrape data from PACS system (synchronous, waits for completion)"},
            {"path": "/task/{task_id}", "method": "GET", "description": "Get status of a scraping task"}
        ]
    }

@app.post("/scrape")
async def scrape_data(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to scrape data from the PACS system asynchronously.
    This starts a background task and returns a task ID immediately.
    
    Required parameters:
    - j_username: Username for PACS login
    - j_password: Password for PACS login
    
    Optional parameters:
    - filter_options: Filter options for the scraping
    - headless: Whether to run browser in headless mode
    - viewport_width: Width of browser viewport
    - viewport_height: Height of browser viewport
    """
    # Generate a unique task ID
    task_id = f"task_{uuid.uuid4().hex}"
    # Initialize task status
    task_storage[task_id] = {
        "status": "running",
        "message": "Scraping task started in the background",
        "data": []
    }
    
    # Start background task
    background_tasks.add_task(run_scraping_task, task_id, request)
    
    # Return task ID and status
    return [
        {
            "task_id": task_id,
            "status": "running",
            "message": "Scraping task started in the background"
        }
    ]

@app.post("/scrape_sync")
async def scrape_data_sync(request: ScrapingRequest):
    """
    Endpoint to scrape data from the PACS system synchronously.
    This waits for the scraping process to complete before returning the results.
    
    Required parameters:
    - j_username: Username for PACS login
    - j_password: Password for PACS login
    
    Optional parameters:
    - filter_options: Filter options for the scraping
    - headless: Whether to run browser in headless mode
    - viewport_width: Width of browser viewport
    - viewport_height: Height of browser viewport
    """
    try:
        # Temporarily set environment variables for login function
        os.environ["j_username"] = request.j_username
        os.environ["j_password"] = request.j_password
        
        # Call the automation function with parameters
        filter_options = None
        if request.filter_options:
            filter_options = {
                "grupo_totem": request.filter_options.grupo_totem,
                "guiche": request.filter_options.guiche,
                "tipo": request.filter_options.tipo,
                "prioridade": request.filter_options.prioridade,
                "modalidade": request.filter_options.modalidade,
            }
        
        # Run the automation and get results
        result = await login_to_pacs(
            headless=request.headless,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            filter_options=filter_options
        )
        
        # Clear environment variables after use
        os.environ.pop("j_username", None)
        os.environ.pop("j_password", None)
        
        # Return the result directly
        if result["status"] == "success":
            return result["data"]
        else:
            return JSONResponse(
                status_code=500,
                content=result
            )
        
    except Exception as e:
        # Handle exceptions
        return JSONResponse(
            status_code=500,
            content={
                "status": "failed",
                "message": str(e),
                "data": []
            }
        )

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Endpoint to check the status of a scraping task.
    
    Parameters:
    - task_id: The ID of the task to check
    """
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return task_storage[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
