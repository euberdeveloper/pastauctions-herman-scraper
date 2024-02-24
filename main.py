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

#### NOT TOTALLY REWRITTEN BY ME ####
def save_to_excel(new_auction_vehicle_urls, new_auction_details, old_auction_vehicle_urls, old_auction_details, file_path):
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        if new_auction_details:
            df_auction = pd.DataFrame(new_auction_details)
            df_auction.to_excel(writer, index=False, sheet_name='NewAuctions')
        if new_auction_vehicle_urls:
            df_event = pd.DataFrame(new_auction_vehicle_urls)
            df_event.to_excel(writer, index=False, sheet_name='NewAuctionVehicleUrls')
        if old_auction_details:
            df_auction = pd.DataFrame(old_auction_details)
            df_auction.to_excel(writer, index=False, sheet_name='OldAuctions')
        if old_auction_vehicle_urls:
            df_event = pd.DataFrame(old_auction_vehicle_urls)
            df_event.to_excel(writer, index=False, sheet_name='OldAuctionVehicleUrls')

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

def get_auctions_data(page_source, verbose=False, waiting_time=3):
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

            # Attempt to find the URL using regex
            url_match = re.search(r'<a href=\"(/en/offer/[^"]*)\"', event_content)
            full_url = base_url + url_match.group(1) if url_match else None

            # Clean up the extracted values
            name = re.sub(r'\&amp;', '&', name) if name else 'N/A'
            if name == 'N/A':
                full_url_desinence = full_url.split('/')[-1]
                name = f"{start_date} - offer {full_url_desinence}"

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

def scrape_auction_names(page_source, waiting_time=3):
    # Get the auction names without duplicates and the special "archive" one
    auction_names = list(set([
        name 
        for name in re.findall(r'href="/en/offer/([^"/]+)/?"', page_source) 
        if name != ''
    ]))
    print(f"Found {len(auction_names)} auction names:")
    print(json.dumps(auction_names, indent=2))

    return auction_names

def get_auctions_page_source(driver, url, only_open, waiting_time=3, verbose=False):
    # Go to page and wait for some seconds
    driver.get(url)
    time.sleep(waiting_time) 

    # Get the the page source and slice only the open ones
    page_source = driver.page_source
    if only_open:
        page_source = "\n".join(re.findall(r'<!-- vandaag in de veiling -->(.*)<!-- gesloten veilingen -->', page_source, re.DOTALL)) 
    if verbose:
        print(page_source)
        
    return page_source

def scrape_open_auction_names(page_source, waiting_time=3):
    print("Getting open auctions names...")
    return scrape_auction_names(page_source)

def scrape_archive_auction_names(page_source, archive_page_url, waiting_time=3):
    print(f"Getting archive auctions names from {archive_page_url}...")
    return scrape_auction_names(page_source)

def scrape_all_archive_page_urls(driver, waiting_time=3, verbose=False):
    print("Getting archived pages urls...")

    archives_url = f"{base_url}/en/offer/archive/"
    # Go to page and wait for some seconds
    driver.get(archives_url)
    time.sleep(waiting_time)

    # Get the the page source and slice only the open ones
    page_source = driver.page_source
    archive_page_indexes = sorted(list(set([
        int(page_index)
        for page_index in re.findall(r'href="/en/offer/archive/(\d+)/?"', page_source) 
    ])))
    archive_page_urls = [archives_url] + [
        f"{base_url}/en/offer/archive/{page_index}/"
        for page_index in archive_page_indexes
    ]
    print(f"Found {len(archive_page_urls)} archive pages")
    if verbose:
        print(json.dumps(archive_page_urls, indent=2))

    return archive_page_urls

def get_event_url_from_name(name):
    return f"{base_url}/en/offer/{name}"

def extract_vehicle_urls(event_name, page_source):
    vehicle_urls = []
    try:
        vehicle_urls = list(set([
            f"{base_url}{url}{'' if url.endswith('/') else '/'}"
            for url in re.findall(rf'href="(/en/offer/{event_name}/[^"/]+/?)"', page_source)
        ]))
    except Exception as e:
        print(f"Error scraping vehicle URLs from {event_name}: {e}")
    return vehicle_urls

def get_vehicle_urls_data(event_name, page_source, verbose=False):
    # Get the vehicle urls
    vehicle_urls = extract_vehicle_urls(event_name, page_source)
    print(f"Found {len(vehicle_urls)} vehicles in {event_name}")
    if verbose:
        print(json.dumps(vehicle_urls, indent=2))
        
    # Return the new urls data
    event_url = get_event_url_from_name(event_name)
    return [{
       "Event URL": f"{event_url}/",
       "Vehicle URL": url
    } for url in vehicle_urls]

def scrape_auction_vehicle_urls(driver, event_name, new_urls_data, waiting_time=3, verbose=False):
    print(f"Scraping event {event_name} vehicle urls...")

    event_url = get_event_url_from_name(event_name)
    print(f"Event url is: {event_url}")

    # Go to page, wait for some seconds and get page source
    driver.get(event_url)
    time.sleep(waiting_time)
    page_source = driver.page_source

    # Extract and add the vehicle urls and get new urls data
    new_urls_data.extend(get_vehicle_urls_data(event_name, page_source, verbose=verbose))

def scrape_open_auctions(driver, verbose=False):
    # Get the open auctions page source
    open_auctions_source = get_auctions_page_source(driver, f"{base_url}/en/offer/", only_open=True, verbose=verbose)

    # Get auctions data
    open_auctions_details = get_auctions_data(open_auctions_source, verbose=verbose)

    # Get the vehicle urls
    open_auctions_vehicle_urls = []
    open_auction_names = scrape_open_auction_names(open_auctions_source)
    for open_auction_name in open_auction_names:
        scrape_auction_vehicle_urls(driver, open_auction_name, open_auctions_vehicle_urls, verbose=verbose)

    return open_auctions_vehicle_urls, open_auctions_details

def scraper_archive_auctions(driver, verbose=False):
    archive_page_urls = scrape_all_archive_page_urls(driver, verbose=verbose)

    archive_auction_vehicle_urls = []
    archive_auctions_details = []

    for archive_page_url in archive_page_urls:
        page_source = get_auctions_page_source(driver, archive_page_url, only_open=False, verbose=verbose)

        auctions_details = get_auctions_data(page_source, verbose=verbose)
        archive_auctions_details.extend(auctions_details)

        archive_auction_names = scrape_archive_auction_names(page_source, archive_page_url)
        for archive_auction_name in archive_auction_names:
            scrape_auction_vehicle_urls(driver, archive_auction_name, archive_auction_vehicle_urls, verbose=verbose)

    return archive_auction_vehicle_urls, archive_auctions_details
        
def scrape_auctions(verbose=False):
    # Get chrome driver
    driver = get_chrome_driver() # ES. get_chrome_driver(headless=True, webdriver_path='PATH_TO_CHROMEDRIVER')

    # Scrape everything; If the process fails, the driver will be closed
    try:
        open_auctions_vehicle_urls, open_auctions_details = scrape_open_auctions(driver, verbose=verbose)
        archive_auction_vehicle_urls, archive_auctions_details = scraper_archive_auctions(driver, verbose=verbose)
    finally:
        driver.quit()

    # Return the results
    return open_auctions_vehicle_urls, open_auctions_details, archive_auction_vehicle_urls, archive_auctions_details

def save_results(open_auctions_vehicle_urls, open_auctions_details, archive_auction_vehicle_urls, archive_auctions_details, save_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = save_path_prefix + f'/UpcomingAuction_{timestamp}.xlsx'
    save_to_excel(open_auctions_vehicle_urls, open_auctions_details, archive_auction_vehicle_urls, archive_auctions_details, save_path)
    
def main(verbose=False):
    open_auctions_vehicle_urls, open_auctions_details, archive_auction_vehicle_urls, archive_auctions_details = scrape_auctions(verbose=verbose)
    print(f"Scraped {len(open_auctions_vehicle_urls)} open vehicle URLs and {len(open_auctions_details)} open auctions")

    save_results(open_auctions_vehicle_urls, open_auctions_details, archive_auction_vehicle_urls, archive_auctions_details, save_path_prefix)
    print(f"Results saved to {save_path_prefix}")

if __name__ == "__main__":
    main(verbose=False)
