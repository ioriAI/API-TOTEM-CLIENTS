#!/usr/bin/env python
"""
PACS Imago Radiologia Login Automation Script
This script automates the login process for the PACS Imago Radiologia website.
"""
import os
import asyncio
import csv
import json
import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from typing import Dict, Any, Optional
    
# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
USERNAME = os.getenv("j_username")
PASSWORD = os.getenv("j_password")

# URLs
LOGIN_URL = "https://pacs.imagoradiologia.com.br/Netris-web/login"
TOTEM_URL = "https://pacs.imagoradiologia.com.br/Netris-web/gerenciamentoTotem/atendimentosTotemPorChegada"

async def login_to_pacs(headless: bool = True, 
                        viewport_width: int = 1280, 
                        viewport_height: int = 800,
                        filter_options: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Automates the login process for PACS Imago Radiologia.
    Uses Playwright to navigate to the login page and fill in credentials.
    
    Args:
        headless: Whether to run browser in headless mode
        viewport_width: Width of browser viewport
        viewport_height: Height of browser viewport
        filter_options: Dictionary with filter options for the dropdown menus
        
    Returns:
        Dictionary with scraped data and status information
    """
    print("Starting login automation...")
    
    # Initialize result dictionary
    result = {
        "status": "failed",
        "data": [],
        "message": "",
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Use default filter options if none provided
    if filter_options is None:
        filter_options = {
            "grupo_totem": "Selecione um grupo totem",
            "guiche": "Selecione um guichê",
            "tipo": "Selecione um tipo",
            "prioridade": "Selecione uma prioridade",
            "modalidade": "Selecione uma modalidade"
        }
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=headless)
        
        # Create a new context with specified viewport size
        context = await browser.new_context(viewport={"width": viewport_width, "height": viewport_height})
        
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
                error_msg = "Error: Username or password not found in environment variables."
                print(error_msg)
                result["message"] = error_msg
                return result
            
            # Fill in the username and password
            print("Filling in credentials...")
            await page.fill('input[name="j_username"]', USERNAME)
            await page.fill('input[name="j_password"]', PASSWORD)
            
            # Click the login button
            print("Submitting login form...")
            await page.click('button[type="submit"]')
            
            # Simple wait for page to load after login
            print("Waiting for page to load after login...")
            await page.wait_for_load_state("networkidle")
            
            # Wait for 5 seconds
            print("Waiting for 5 seconds...")
            await asyncio.sleep(5)
            
            # Navigate to the Totem management page
            print(f"Navigating to {TOTEM_URL}...")
            await page.goto(TOTEM_URL)
            print("Navigation completed")
            
            # Wait for the page to fully load
            await page.wait_for_load_state("networkidle")
            print("Page fully loaded")
            
            # Scroll to and click the Salvar button
            print("Scrolling to and clicking the Salvar button...")
            salvar_button = page.locator("#btnSetGuicheModal")
            
            # Check if the button exists
            if await salvar_button.count() > 0:
                # Scroll the button into view before clicking
                await salvar_button.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                await salvar_button.click()
                print("Clicked Salvar button")
            else:
                # Try alternative method if the button isn't found
                print("Salvar button not found with first selector, trying JavaScript approach...")
                await page.evaluate('''() => {
                    const button = document.querySelector('#btnSetGuicheModal');
                    if (button) {
                        button.scrollIntoView();
                        setTimeout(() => button.click(), 500);
                    }
                }''')
                await asyncio.sleep(2)
                print("Executed JavaScript click on Salvar button")
            
            # Wait for the page to update
            await asyncio.sleep(2)
            
            # Apply all filters using the exact selectors from Playwright Inspector
            print("Applying filters...")
            
            # Helper function to scroll to element and click
            async def scroll_and_click(selector, description):
                print(f"Scrolling to and clicking {description}...")
                element = page.locator(selector)
                
                # Check if the element exists
                if await element.count() > 0:
                    await element.scroll_into_view_if_needed()
                    await asyncio.sleep(1)
                    await element.click()
                    print(f"Clicked {description}")
                    return True
                else:
                    print(f"{description} not found with selector {selector}")
                    # Try JavaScript approach as fallback
                    success = await page.evaluate(f'''() => {{
                        const el = document.querySelector('{selector}');
                        if (el) {{
                            el.scrollIntoView();
                            setTimeout(() => el.click(), 500);
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if success:
                        print(f"Clicked {description} using JavaScript")
                        await asyncio.sleep(1)
                        return True
                    return False
            
            # 1. Select from the grupo totem dropdown
            await scroll_and_click("#slGrupoTotem_chosen", "grupo totem dropdown")
            await asyncio.sleep(1)
            await scroll_and_click(f"#slGrupoTotem_chosen li:has-text('{filter_options['grupo_totem']}')", f"{filter_options['grupo_totem']} option")
            
            # 2. Select from the guichê dropdown
            await scroll_and_click("#guiche_chosen a", "guichê dropdown")
            await asyncio.sleep(1)
            await scroll_and_click(f"#guiche_chosen li:has-text('{filter_options['guiche']}')", f"{filter_options['guiche']} option")
            
            # 3. Select from the tipo dropdown
            await scroll_and_click(f"a:has-text('{filter_options['tipo']}')", "tipo dropdown")
            await asyncio.sleep(1)
            await scroll_and_click(f"li:has-text('{filter_options['tipo']}')", f"{filter_options['tipo']} option")
            
            # 4. Select from the prioridade dropdown
            await scroll_and_click(f"a:has-text('{filter_options['prioridade']}')", "prioridade dropdown")
            await asyncio.sleep(1)
            await scroll_and_click(f"li:has-text('{filter_options['prioridade']}')", f"{filter_options['prioridade']} option")
            
            # 5. Select from the modalidade dropdown
            await scroll_and_click(f"a:has-text('{filter_options['modalidade']}')", "modalidade dropdown")
            await asyncio.sleep(1)
            await scroll_and_click(f"li:has-text('{filter_options['modalidade']}')", f"{filter_options['modalidade']} option")
            
            # Click the Filtrar button
            print("Scrolling to and clicking the Filtrar button...")
            filtrar_button = page.locator("#btnFiltrar")
            
            # Check if the button exists
            if await filtrar_button.count() > 0:
                await filtrar_button.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                await filtrar_button.click()
                print("Clicked Filtrar button")
            else:
                # Try alternative method if the button isn't found
                print("Filtrar button not found with first selector, trying JavaScript approach...")
                await page.evaluate('''() => {
                    const button = document.querySelector('#btnFiltrar');
                    if (button) {
                        button.scrollIntoView();
                        setTimeout(() => button.click(), 500);
                    }
                }''')
                await asyncio.sleep(2)
                print("Executed JavaScript click on Filtrar button")
            
            # Wait for the table to load
            print("Waiting for table to load...")
            await asyncio.sleep(3)
            await page.wait_for_load_state("networkidle")
            
            # Scrape the table data
            print("Scraping table data...")
            
            # First, try to get the table headers
            headers = []
            header_elements = page.locator("table thead th")
            header_count = await header_elements.count()
            
            if header_count == 0:
                print("No headers found with selector 'table thead th', trying alternative selector...")
                header_elements = page.locator("table tr:first-child th, table tr:first-child td")
                header_count = await header_elements.count()
            
            for i in range(header_count):
                header_text = await header_elements.nth(i).inner_text()
                headers.append(header_text.strip())
            
            print(f"Found {len(headers)} table headers: {headers}")
            
            # Initialize empty list for all rows across all pages
            all_rows = []
            current_page = 1
            has_more_pages = True
            
            # Process all pages of the table
            while has_more_pages:
                print(f"Processing page {current_page}...")
                
                # Get the table rows for the current page
                row_elements = page.locator("table tbody tr")
                row_count = await row_elements.count()
                
                if row_count == 0:
                    print("No rows found with selector 'table tbody tr', trying alternative selector...")
                    row_elements = page.locator("table tr:not(:first-child)")
                    row_count = await row_elements.count()
                
                print(f"Found {row_count} table rows on page {current_page}")
                
                # Process rows on the current page
                page_rows = []
                for r in range(row_count):
                    row = row_elements.nth(r)
                    row_data = {}
                    cell_elements = row.locator("td")
                    cell_count = await cell_elements.count()
                    
                    # If no cells found, try th as well (some tables use th for all cells)
                    if cell_count == 0:
                        cell_elements = row.locator("td, th")
                        cell_count = await cell_elements.count()
                    
                    for c in range(cell_count):
                        if c < len(headers):
                            cell_text = await cell_elements.nth(c).inner_text()
                            row_data[headers[c]] = cell_text.strip()
                    
                    # Only add non-empty rows
                    if row_data:
                        page_rows.append(row_data)
                        all_rows.append(row_data)
                        print(f"Processed row {r+1}/{row_count} on page {current_page}")
                
                # Check for pagination elements
                # Common pagination patterns: "Next" button, page numbers, etc.
                pagination_next = page.locator("a.next, a.pagination-next, li.next a, button.next, .pagination .next, [aria-label='Next page'], .paginate_button.next")
                
                # Also check for DataTables specific pagination (common in many web applications)
                if await pagination_next.count() == 0:
                    pagination_next = page.locator("#dataTableAtendimentosTotem_next, .dataTables_paginate .next")
                
                # Check if there's a next page and if it's enabled/clickable
                has_more_pages = False
                if await pagination_next.count() > 0:
                    # Check if the next button is disabled
                    is_disabled = await pagination_next.first.get_attribute("class")
                    if is_disabled and ("disabled" in is_disabled or "inactive" in is_disabled):
                        print("Next page button is disabled, reached the last page")
                    else:
                        print(f"Clicking to navigate to page {current_page + 1}...")
                        try:
                            # Take screenshot before clicking for debugging
                            await page.screenshot(path=f"before_pagination_page_{current_page}.png")
                            
                            # Scroll to the pagination element and click
                            await pagination_next.first.scroll_into_view_if_needed()
                            await asyncio.sleep(1)
                            await pagination_next.first.click()
                            
                            # Wait for the table to update
                            await asyncio.sleep(2)
                            await page.wait_for_load_state("networkidle")
                            
                            # Take screenshot after clicking for debugging
                            await page.screenshot(path=f"after_pagination_page_{current_page}.png")
                            
                            current_page += 1
                            has_more_pages = True
                            print(f"Successfully navigated to page {current_page}")
                        except Exception as e:
                            print(f"Error navigating to next page: {e}")
                            has_more_pages = False
                else:
                    # Try JavaScript approach to find and click next page button
                    print("No standard pagination elements found, trying JavaScript approach...")
                    has_next_page = await page.evaluate('''() => {
                        // Try various selectors for pagination
                        const nextButtons = [
                            document.querySelector('a.next'),
                            document.querySelector('a.pagination-next'),
                            document.querySelector('li.next a'),
                            document.querySelector('button.next'),
                            document.querySelector('.pagination .next'),
                            document.querySelector('[aria-label="Next page"]'),
                            document.querySelector('.paginate_button.next'),
                            document.querySelector('#dataTableAtendimentosTotem_next')
                        ].filter(Boolean);
                        
                        if (nextButtons.length > 0) {
                            const nextButton = nextButtons[0];
                            // Check if button is disabled
                            if (nextButton.classList.contains('disabled') || 
                                nextButton.classList.contains('inactive') ||
                                nextButton.getAttribute('disabled')) {
                                return false;
                            }
                            
                            // Click the button
                            nextButton.scrollIntoView();
                            setTimeout(() => nextButton.click(), 500);
                            return true;
                        }
                        
                        // No pagination found or all options exhausted
                        return false;
                    }''')
                    
                    if has_next_page:
                        await asyncio.sleep(2)
                        await page.wait_for_load_state("networkidle")
                        current_page += 1
                        has_more_pages = True
                        print(f"Successfully navigated to page {current_page} using JavaScript")
                    else:
                        print("No pagination found or reached the last page")
            
            print(f"Finished processing all pages. Total rows collected: {len(all_rows)}")
            
            # Generate timestamp for filenames
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export data to CSV
            csv_filename = f"table_data_{timestamp}.csv"
            print(f"Exporting data to CSV: {csv_filename}")
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                if headers and all_rows:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(all_rows)
                    print(f"Successfully exported {len(all_rows)} rows to CSV")
                else:
                    print("No data to export to CSV")
            
            # Export data to JSON
            json_filename = f"table_data_{timestamp}.json"
            print(f"Exporting data to JSON: {json_filename}")
            
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(all_rows, jsonfile, ensure_ascii=False, indent=4)
                print(f"Successfully exported data to JSON")
            
            # Also try to get the raw HTML of the table for debugging
            print("Getting raw HTML of the table...")
            table_html = await page.evaluate('''() => {
                const table = document.querySelector('table');
                return table ? table.outerHTML : 'No table found';
            }''')
            
            with open(f"table_html_{timestamp}.html", 'w', encoding='utf-8') as htmlfile:
                htmlfile.write(table_html)
                print(f"Saved table HTML to table_html_{timestamp}.html")
            
            # Take a screenshot of the final state
            print("Taking final screenshot...")
            await page.screenshot(path="final_state.png")
            print("Screenshot saved as final_state.png")
            
            # Prepare successful result
            result["status"] = "success"
            result["data"] = all_rows
            result["message"] = f"Successfully scraped {len(all_rows)} rows of data"
            result["headers"] = headers
            result["csv_file"] = csv_filename
            result["json_file"] = json_filename
            result["html_file"] = f"table_html_{timestamp}.html"
            
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            print(error_msg)
            result["message"] = error_msg
            
            # Take a screenshot to help diagnose the error
            try:
                screenshot_path = f"error_state_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                print(f"Error screenshot saved as {screenshot_path}")
                result["error_screenshot"] = screenshot_path
            except:
                print("Could not take error screenshot")
        
        finally:
            # Close the browser
            await browser.close()
            print("Browser closed.")
            
        return result

if __name__ == "__main__":
    # Check if credentials are set in environment variables
    if not os.getenv("j_username") or not os.getenv("j_password"):
        print("Warning: j_username and/or j_password not found in environment variables.")
        print("Please set these environment variables or create a .env file.")
    else:
        # Run the main function
        asyncio.run(login_to_pacs(headless=False))