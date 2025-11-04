import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import re
import numpy as np
import openpyxl 
import requests 

# --- Conf ---
FILE_PATH = '../data/publications_with_all_abstracts.xlsx'
DELAY_BETWEEN_REQUESTS = 15
RANDOM_DELAY_MAX = 5 # to add 0 to 5 extra seconds randomly
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
SAVE_FREQUENCY = 1 
SELENIUM_TIMEOUT = 20 # wait time for Selenium  for an element
SEARCH_URL_TEMPLATE = "https://scholar.google.com/scholar?hl=en&q={query}"

# --- Functions ---

def is_abstract_missing(abstract_value):
    """Checks if the abstract field is effectively missing."""
    if pd.isna(abstract_value):
        return True
    if isinstance(abstract_value, str) and not abstract_value.strip():
        return True
    if isinstance(abstract_value, str) and abstract_value.lower() == 'nan':
        return True
    return False

def setup_driver():
    """Initializes and returns a Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2, 
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })

    try:
        driver = webdriver.Chrome(options=chrome_options)
        # Apply stealth techniques
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]})")
        return driver
    except Exception as e:
        print(f"    ERROR initializing WebDriver: {e}")
        print("    Ensure chromedriver is installed, matches your Chrome version, and is in your system PATH.")
        return None

def search_scholar_selenium(driver, title):
    """Searches Google Scholar using Selenium and extracts snippet."""
    print(f"  Searching Google Scholar (Selenium) for: '{title[:60]}...'")
    if not driver:
        print("    WebDriver not available.")
        return None

    try:
        search_query = requests.utils.quote(title)
        driver.get(SEARCH_URL_TEMPLATE.format(query=search_query))

        # Check for CAPTCHA immediately after loading
        time.sleep(random.uniform(1, 2)) # Small random wait
        if "google.com/sorry/" in driver.current_url or "recaptcha" in driver.page_source.lower():
             print("    *** CAPTCHA or block page detected! Cannot proceed. ***")
             return "CAPTCHA_DETECTED" 

        # Wait for the first result container to be present
        wait = WebDriverWait(driver, SELENIUM_TIMEOUT)
        first_result_container = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.gs_r.gs_or.gs_scl'))
        )

        # Try to find the abstract snippet
        try:
            snippet_div = first_result_container.find_element(By.CSS_SELECTOR, 'div.gs_rs')
            abstract_snippet = snippet_div.text.strip()
            abstract_snippet = re.sub(r'\[.*?\]', '', abstract_snippet).strip()

            # Heuristic check
            if len(abstract_snippet) > 75 and any(kw in abstract_snippet.lower() for kw in ['abstract', 'results', 'methods', 'conclusion', 'study', 'purpose', 'background', 'objective', 'introduction']):
                print(f"    Found relevant snippet ({len(abstract_snippet)} chars).")
                return abstract_snippet[:1500] + ('...' if len(abstract_snippet) > 1500 else '')
            else:
                 print(f"    Snippet found but seems short/irrelevant ({len(abstract_snippet)} chars).")
                 return None

        except NoSuchElementException:
            print("    No standard abstract snippet ('gs_rs') found. Checking main body...")
            try:
                ri_div = first_result_container.find_element(By.CSS_SELECTOR, 'div.gs_ri')
                ri_text = ri_div.text.strip()
                # Try a slightly more robust regex for abstract-like text after common separators
                abstract_match = re.search(r'(?:Abstract|Summary|Introduction|Background|Purpose)\s*[:\-–]?\s*(.*)', ri_text, re.IGNORECASE | re.DOTALL)
                if abstract_match and len(abstract_match.group(1).strip()) > 100:
                    abstract_snippet = abstract_match.group(1).strip()
                    print(f"    Found potential snippet in main result body ({len(abstract_snippet)} chars).")
                    return abstract_snippet[:1500] + ('...' if len(abstract_snippet) > 1500 else '')
                else:
                    print("    Could not reliably extract snippet from main result body.")
                    return None
            except NoSuchElementException:
                 print("    Could not find main result body ('gs_ri') either.")
                 return None

    except TimeoutException:
        print("    Error: Timed out waiting for search results element. CAPTCHA or block likely.")
        if "google.com/sorry/" in driver.current_url or "recaptcha" in driver.page_source.lower():
             print("    *** CAPTCHA or block detected after initial load! ***")
             return "CAPTCHA_DETECTED"
        return None
    except Exception as e:
        print(f"    An error occurred during Selenium operation: {e}")
        return None

def save_dataframe(df_to_save, file_path):
    """Saves the DataFrame to Excel, handling potential errors."""
    print(f"    Attempting to save progress to {file_path}...")
    try:
        df_to_save.to_excel(file_path, index=False, engine='openpyxl')
        print(f"    Successfully saved progress.")
        return True
    except PermissionError:
        print(f"    ERROR: Could not save file '{file_path}'. Is it open in another program?")
        return False
    except Exception as e:
        print(f"    ERROR: An unexpected error occurred while saving: {e}")
        return False

# --- Main Script ---

print(f"Reading input file: {FILE_PATH}")
try:
    df = pd.read_excel(FILE_PATH, keep_default_na=False, na_values=[''])
    df['abstract'] = df['abstract'].replace('', np.nan)
except FileNotFoundError:
    print(f"Error: Input file '{FILE_PATH}' not found.")
    exit()
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit()

if 'title' not in df.columns or 'abstract' not in df.columns:
    print("Error: The Excel file must contain 'title' and 'abstract' columns.")
    exit()

missing_abstracts_indices = df[df['abstract'].apply(is_abstract_missing)].index.tolist()
print(f"Found {len(missing_abstracts_indices)} entries with missing abstracts.")

count_updated = 0
success_since_last_save = 0
driver = None # Initialize driver outside the loop

if not missing_abstracts_indices:
    print("No missing abstracts detected. Exiting.")
else:
    total_missing = len(missing_abstracts_indices)
    driver = setup_driver() # Setup driver once

    if not driver:
        print("Could not initialize Selenium driver. Exiting.")
        exit()

    try: # Use try...finally to ensure driver quits
        for i, index in enumerate(missing_abstracts_indices):
            if not is_abstract_missing(df.loc[index, 'abstract']):
                print(f"Skipping index {index}: Abstract already present.")
                continue

            title = str(df.loc[index, 'title']).strip()
            print(f"\nProcessing {i+1}/{total_missing} (Index {index}): {title}")

            # Add a random delay BEFORE the request
            base_delay = DELAY_BETWEEN_REQUESTS
            random_addition = random.uniform(0, RANDOM_DELAY_MAX)
            sleep_time = base_delay + random_addition
            print(f"  Waiting for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

            # Try Google Scholar using the persistent driver
            abstract_result = search_scholar_selenium(driver, title)

            if abstract_result == "CAPTCHA_DETECTED":
                print("\n*** CAPTCHA detected. Stopping script. Please solve manually or wait a long time before restarting. ***")
                break # Stop the loop immediately

            if abstract_result: # Check if it's a non-empty string (not None)
                df.loc[index, 'abstract'] = abstract_result
                count_updated += 1
                success_since_last_save += 1
                print(f"    ---> Abstract found and updated for index {index}.")

                # Save incrementally
                if success_since_last_save >= SAVE_FREQUENCY:
                    if save_dataframe(df, FILE_PATH):
                        success_since_last_save = 0
                    else:
                        print("    Save failed. Will retry on next successful scrape.")
            else:
                print(f"    Could not find abstract for index {index} via Selenium.")
                df.loc[index, 'abstract'] = np.nan # Ensure it remains NaN

    except KeyboardInterrupt:
        print("\n*** Script interrupted by user (Ctrl+C). ***")
    except Exception as e:
        print(f"\n*** An unexpected error occurred in the main loop: {e} ***")
    finally:
        # --- Final Save & Cleanup ---
        if success_since_last_save > 0:
             print("\nAttempting final save before exiting...")
             save_dataframe(df, FILE_PATH)
        elif count_updated > 0:
             print("\nAttempting final confirmation save before exiting...")
             save_dataframe(df, FILE_PATH)
        else:
             print("\nNo updates made in this session needing final save.")

        if driver:
            print("Quitting Selenium WebDriver...")
            driver.quit()
        print("Script finished.")

# Final check outside the loop in case it finished normally
if count_updated > 0 and success_since_last_save == 0 and driver is None : 
    print("\nProcess completed. Final data saved in:", FILE_PATH)
elif count_updated == 0 and driver is None:
     print("\nProcess completed. No new abstracts found or updated.")