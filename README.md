# pastauctions-herman-scraper
A web scraper using Selenium to scrape the content of some car auctions from Herman&amp;Herman

## How to use it

Notes: you will need python and pipenv installed in your system.

1. Clone the repository
2. Install the dependencies with `pipenv install`
3. Run the script with `pipenv run python main.py`

Some adjustemnts:
- You should change the destination folder `save_path_prefix`
- Check the function `get_chrome_driver` in case you want to change webdriver, headless mode, etc.

## What does it do

The script gets the auctions information and for each auction it gets the urls to the car lots. Everything is divided into archived auctions and current/future actions. The result is an excel file with four sheets, one for the auctions and another for the car lots, for both archived and new auctions. 

In `example_result` some example files are available.

## More technical notes

The script uses Selenium to navigate the website and get the information. It uses the Chrome webdriver, but it can be easily changed to another one.

To get only the new auctions from the offer page, two special comments (in dutch) are used. To get all the archived auctions, all the pages in the archive page are visited.

To get the information about the urls, some regexps are used. The script is not very robust and may break if the website changes. It is recommended to check the website structure and the script if it stops working.

# Update

Since the website doesn't do any complication with cookies or blocks, a drastical improvement for the performance has been done. The code has been refactored so that selenium and a browser are not used anymore. Instead, the requests library is used to get the content of the pages.