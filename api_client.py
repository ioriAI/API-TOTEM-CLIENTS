#!/usr/bin/env python
"""
PACS Imago Radiologia API Client
This script provides a client for the PACS Imago Radiologia API that polls until results are ready.
"""
import sys
import time
import json
import requests
from typing import Dict, Any, Optional
import argparse

# Base URL for the API
API_URL = "https://api-manager-api-totem-ris.uzfqiw.easypanel.host"

def poll_until_complete(task_id: str, max_retries: int = 30, delay: int = 5) -> Dict[str, Any]:
    """
    Poll the API until the task is complete or max retries are reached.
    
    Args:
        task_id: The task ID to poll for
        max_retries: Maximum number of retry attempts
        delay: Delay in seconds between retries
        
    Returns:
        The final API response or an error if max retries reached
    """
    print(f"Polling for task {task_id}...")
    
    # Endpoint to check task status
    status_url = f"{API_URL}/task/{task_id}"
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}...")
            response = requests.get(status_url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if task is complete
                if data.get("status") == "success":
                    print("Task completed successfully!")
                    return data
                elif data.get("status") == "failed":
                    print(f"Task failed: {data.get('message')}")
                    return data
                else:
                    print(f"Task still running. Status: {data.get('status')}, Message: {data.get('message')}")
                    
                    # Wait before the next attempt
                    print(f"Waiting {delay} seconds before next check...")
                    time.sleep(delay)
            else:
                print(f"Error: HTTP {response.status_code} - {response.text}")
                time.sleep(delay)
                
        except Exception as e:
            print(f"Error during polling: {str(e)}")
            time.sleep(delay)
    
    return {
        "status": "timeout",
        "message": f"Maximum retries ({max_retries}) reached without completion",
        "data": []
    }

def scrape_data(username: str, password: str, headless: bool = True, 
                viewport_width: int = 1280, viewport_height: int = 800,
                filter_options: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Initiate a scraping task and poll until completion.
    
    Args:
        username: PACS username
        password: PACS password
        headless: Whether to run browser in headless mode
        viewport_width: Width of browser viewport
        viewport_height: Height of browser viewport
        filter_options: Dictionary with filter options for dropdowns
        
    Returns:
        The final result data
    """
    # Default filter options if none provided
    if filter_options is None:
        filter_options = {
            "grupo_totem": "Selecione um grupo totem",
            "guiche": "Selecione um guichê",
            "tipo": "Selecione um tipo",
            "prioridade": "Selecione uma prioridade",
            "modalidade": "Selecione uma modalidade"
        }
    
    # Prepare the request payload
    payload = {
        "j_username": username,
        "j_password": password,
        "headless": headless,
        "viewport_width": viewport_width,
        "viewport_height": viewport_height,
        "filter_options": filter_options
    }
    
    # Make the initial request to start scraping
    print("Starting scraping task...")
    try:
        response = requests.post(f"{API_URL}/scrape", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if this is the final result or a task ID
            if isinstance(data, list) and len(data) > 0 and "task_id" in data[0]:
                task_id = data[0]["task_id"]
                print(f"Received task ID: {task_id}")
                
                # Poll until task is complete
                return poll_until_complete(task_id)
            else:
                # Immediate result
                print("Received immediate result")
                return {
                    "status": "success",
                    "data": data,
                    "message": "Task completed synchronously"
                }
        else:
            error_msg = f"Error: HTTP {response.status_code} - {response.text}"
            print(error_msg)
            return {
                "status": "failed",
                "message": error_msg,
                "data": []
            }
            
    except Exception as e:
        error_msg = f"Error initiating scraping: {str(e)}"
        print(error_msg)
        return {
            "status": "failed",
            "message": error_msg,
            "data": []
        }

def main():
    """Main function to parse arguments and execute the script."""
    parser = argparse.ArgumentParser(description="Client for PACS Imago Radiologia API")
    parser.add_argument("--username", "-u", required=True, help="PACS username")
    parser.add_argument("--password", "-p", required=True, help="PACS password")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--viewport-width", type=int, default=1280, help="Browser viewport width")
    parser.add_argument("--viewport-height", type=int, default=800, help="Browser viewport height")
    parser.add_argument("--output", "-o", help="Output JSON file (optional)")
    parser.add_argument("--max-retries", type=int, default=30, help="Maximum retry attempts")
    parser.add_argument("--delay", type=int, default=5, help="Delay between retries in seconds")
    
    # Filter options
    parser.add_argument("--grupo-totem", default="Selecione um grupo totem", help="Grupo totem filter")
    parser.add_argument("--guiche", default="Selecione um guichê", help="Guichê filter")
    parser.add_argument("--tipo", default="Selecione um tipo", help="Tipo filter")
    parser.add_argument("--prioridade", default="Selecione uma prioridade", help="Prioridade filter")
    parser.add_argument("--modalidade", default="Selecione uma modalidade", help="Modalidade filter")
    
    args = parser.parse_args()
    
    # Prepare filter options
    filter_options = {
        "grupo_totem": args.grupo_totem,
        "guiche": args.guiche,
        "tipo": args.tipo,
        "prioridade": args.prioridade,
        "modalidade": args.modalidade
    }
    
    # Run the scraping process
    result = scrape_data(
        username=args.username,
        password=args.password,
        headless=args.headless,
        viewport_width=args.viewport_width,
        viewport_height=args.viewport_height,
        filter_options=filter_options
    )
    
    # Output the result
    if args.output:
        # Save to file
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {args.output}")
    else:
        # Print to console
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Exit with appropriate code
    if result["status"] == "success":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
