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

The script gets the auctions information and for each auction it gets the urls to the car lots. The result is an excel file with two sheets, one for the auctions and another for the car lots.

In `example_result` some example files are available.

## More technical notes

The script uses Selenium to navigate the website and get the information. It uses the Chrome webdriver, but it can be easily changed to another one.

To get the information about the urls, some regexps are used. The script is not very robust and may break if the website changes. It is recommended to check the website structure and the script if it stops working.