import pandas as pd
import re
import time
from datetime import datetime
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Specify the folder of where the output will be saved
save_path_prefix = '/home/euberdeveloper/Github/pastauctions-herman-scraper'
# The baseurl of the website
base_url = "https://www.automotive-auctions.nl"

#### NOT WRITTEN BY ME ####
def save_to_excel(auction_data, event_data, file_path):
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        if auction_data:
            df_auction = pd.DataFrame(auction_data)
            df_auction.to_excel(writer, index=False, sheet_name='NewAuction')
        if event_data:
            df_event = pd.DataFrame(event_data)
            df_event.to_excel(writer, index=False, sheet_name='NewUrls')

def extract_between(content, start_marker, end_marker):
    # Not written by me...
    start_index = content.find(start_marker)
    if start_index == -1:
        return None
    start_index += len(start_marker)
    end_index = content.find(end_marker, start_index)
    if end_index == -1:
        return None
    return content[start_index:end_index].strip()

def get_auctions_data(driver, verbose=False, waiting_time=3):
    auctions_url = f"{base_url}/en/offer/"
    # Go to page and wait for some seconds
    driver.get(auctions_url)
    time.sleep(waiting_time) 

    # Get the names from the page source, without duplicates and the special "archive" one
    page_source = driver.page_source

    # Not written by me...
    events = []

    # Define markers for the start and end of each event
    event_start_marker = "<div class=\"auction set"
    event_end_marker = "<div class=\"auction-picture\">"

    event_sections = re.split(event_start_marker, page_source)
    for section in event_sections:
        if event_end_marker in section:
            event_content = extract_between(section, "", event_end_marker)

            name = extract_between(event_content, "<h2><span>", "</span>")
            date_text = extract_between(event_content, "Duration: <span class=\"val\">", "</span>")
            if verbose:
                print(date_text)

            # Initialize start_date and end_date with default values
            start_date = "Unknown"
            end_date = "Unknown"

            if date_text:
                # Define regex patterns for date formats
                pattern1 = r'(\d{1,2}) (.*?) (.*?) (\d{1,2}) (.*)'
                pattern2 = r'(\d{1,2}) (.*?) (.*?) (\d{1,2}) (.*)'

                # Check for first pattern
                if re.match(pattern1, date_text):
                    match = re.search(pattern1, date_text)
                    start_date = f"{match.group(1)} {match.group(2)} 2024"
                    end_date = f"{match.group(4)} {match.group(5)} 2024"
                # Check for second pattern
                elif re.match(pattern2, date_text):
                    match = re.search(pattern2, date_text)
                    start_date = f"{match.group(1)} {match.group(2)} 2024"
                    end_date = f"{match.group(4)} {match.group(5)} 2024"

            # Clean up the extracted values
            name = re.sub(r'\&amp;', '&', name) if name else 'N/A'

            # Attempt to find the URL using regex
            url_match = re.search(r'<a href=\"(/en/offer/[^"]*)\"', event_content)
            full_url = base_url + url_match.group(1) if url_match else None

            events.append({
                'Maison': "Hermans",
                'Name': name,
                'Start_date': start_date,
                'End_date': end_date,
                'Location': "Boxmeer",
                'url': full_url if full_url else "No URL",  # Ensure 'url' key is always present
            })

    if verbose:
        print(json.dumps(events, indent=2))

    return events
###########################

def get_chrome_driver(headless=False, webdriver_path=None):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")

    if webdriver_path:
        service = Service(webdriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)

    return driver

def scrape_event_names(driver, waiting_time=3):
    print("Getting event urls...")

    auctions_url = f"{base_url}/en/offer/"
    # Go to page and wait for some seconds
    driver.get(auctions_url)
    time.sleep(waiting_time) 

    # Get the names from the page source, without duplicates and the special "archive" one
    page_source = driver.page_source
    event_names = list(set([
        name
        for name in re.findall(r'href="/en/offer/([^"/]+)/?"', page_source) 
        if "archive" not in name
    ]))
    print(f"Found {len(event_names)} events:")
    print(json.dumps(event_names, indent=2))

    return event_names

def get_event_url_from_name(name):
    return f"{base_url}/en/offer/{name}"

def extract_vehicle_urls(event_name, page_source):
    vehicle_urls = []
    try:
        vehicle_urls = [
            f"{base_url}{url}"
            for url in re.findall(rf'href="(/en/offer/{event_name}/[^"/]+/?)"', page_source)
        ]
    except Exception as e:
        print(f"Error scraping vehicle URLs from {event_name}: {e}")
    return vehicle_urls

def get_new_urls_data(event_name, page_source, verbose=False):
    # Get the vehicle urls
    vehicle_urls = extract_vehicle_urls(event_name, page_source)
    print(f"Found {len(vehicle_urls)} vehicles in {event_name}")
    if verbose:
        print(json.dumps(vehicle_urls, indent=2))
        
    # Return the new urls data
    event_url = get_event_url_from_name(event_name)
    return [{
       "Event URL": event_url,
       "Vehicle URL": url
    } for url in vehicle_urls]

def scrape_event(driver, event_name, new_urls_data, waiting_time=3, verbose=False):
    print(f"Scraping event {event_name}...")

    event_url = get_event_url_from_name(event_name)
    print(f"Event url is: {event_url}")

    # Go to page, wait for some seconds and get page source
    driver.get(event_url)
    time.sleep(waiting_time)
    page_source = driver.page_source

    # Extract and add the vehicle urls and get new urls data
    new_urls_data.extend(get_new_urls_data(event_name, page_source, verbose=verbose))

def scrape_events(verbose=False):
    # Get chrome driver
    driver = get_chrome_driver() # ES. get_chrome_driver(headless=True, webdriver_path='PATH_TO_CHROMEDRIVER')

    # Get auctions data
    events_data = get_auctions_data(driver, verbose=verbose)

    # Result arrays
    urls_data = []
    # Scrape everything; If the process fails, the driver will be closed
    try:
        event_names = scrape_event_names(driver)
        for event_name in event_names:
            scrape_event(driver, event_name, urls_data, verbose=verbose)
    finally:
        driver.quit()

    # Return the results
    return urls_data, events_data

def save_results(urls_data, auctions_data, save_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = save_path_prefix + f'/UpcomingAuction_{timestamp}.xlsx'
    save_to_excel(auctions_data, urls_data, save_path)
    
def main(verbose=False):
    urls_data, auctions_data = scrape_events(verbose=verbose)
    print(f"Scraped {len(urls_data)} new urls and {len(auctions_data)} new auctions")

    save_results(urls_data, auctions_data, save_path_prefix)
    print(f"Results saved to {save_path_prefix}")

if __name__ == "__main__":
    main(verbose=False)