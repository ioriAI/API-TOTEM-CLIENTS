#!/usr/bin/env python
"""
Playwright Inspector Mode Script
This script launches Playwright in debug mode with the Inspector enabled
to help identify elements on the page.
"""
import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
USERNAME = os.getenv("j_username")
PASSWORD = os.getenv("j_password")

# URLs
LOGIN_URL = "https://pacs.imagoradiologia.com.br/Netris-web/login"
TOTEM_URL = "https://pacs.imagoradiologia.com.br/Netris-web/gerenciamentoTotem/atendimentosTotemPorChegada"

async def run_with_inspector():
    """
    Launches Playwright with the Inspector enabled to help identify elements.
    """
    print("Starting Playwright with Inspector enabled...")
    print("This will open a browser and the Playwright Inspector window.")
    print("You can use the Inspector to identify elements and generate selectors.")
    
    async with async_playwright() as p:
        # Launch browser with Inspector enabled
        browser = await p.chromium.launch(headless=False)
        
        # Create a new context with viewport size 800x600
        context = await browser.new_context(viewport={"width": 800, "height": 600})
        
        # Open a new page
        page = await context.new_page()
        
        try:
            # Navigate to the login page
            print(f"Navigating to {LOGIN_URL}...")
            await page.goto(LOGIN_URL)
            
            # Wait for the login form to be visible
            await page.wait_for_selector('input[name="j_username"]')
            
            # Check if credentials are available
            if not USERNAME or not PASSWORD:
                print("Error: Username or password not found in environment variables.")
                print("Please make sure j_username and j_password are set in your .env file.")
                return
            
            # Fill in the username and password
            print("Filling in credentials...")
            await page.fill('input[name="j_username"]', USERNAME)
            await page.fill('input[name="j_password"]', PASSWORD)
            
            # Click the login button
            print("Submitting login form...")
            await page.click('button[type="submit"]')
            
            # Wait for page to load after login
            print("Waiting for page to load after login...")
            await page.wait_for_load_state("networkidle")
            
            # Wait for 5 seconds
            print("Waiting for 5 seconds...")
            await asyncio.sleep(5)
            
            # Navigate to the Totem management page
            print(f"Navigating to {TOTEM_URL}...")
            await page.goto(TOTEM_URL)
            print("Navigation completed")
            
            # Wait for 3 seconds for the page to load
            print("Waiting for 3 seconds for the page to load...")
            await asyncio.sleep(3)
            
            # Pause for manual inspection
            print("\n=== INSPECTOR MODE ACTIVE ===")
            print("The browser is now paused for you to inspect elements.")
            print("1. Use the Playwright Inspector window to hover over elements")
            print("2. Click on elements to see their selectors")
            print("3. Copy the selectors to use in your automation script")
            print("4. Press Enter in this terminal when you're done to close the browser")
            print("===============================\n")
            
            # This will pause the execution and activate the Inspector
            await page.pause()
            
        except Exception as e:
            print(f"An error occurred: {e}")
        
        finally:
            # Wait for user input before closing
            input("Press Enter to close the browser...")
            await browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    # Check if credentials are set in environment variables
    if not os.getenv("j_username") or not os.getenv("j_password"):
        print("Warning: j_username and/or j_password not found in environment variables.")
        print("Please add them to your .env file in the format:")
        print("j_username=your_username")
        print("j_password=your_password")
    
    # Run with Inspector enabled
    asyncio.run(run_with_inspector())
