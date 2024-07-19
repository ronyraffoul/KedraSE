# Domstol PDF Scraper

This project is a Scrapy-based web scraper designed to extract metadata and download PDFs from the Swedish Supreme Court's website. The scraper processes the latest decisions and saves the metadata and PDFs to the local file system.

## Features

- Extracts metadata such as case number, designation, legal provisions, legal cases, and keywords from the detailed pages.
- Downloads up to 10 PDFs of the latest decisions.
- Ensures robust error handling and logging.

## Requirements

- Python 3.7+
- Scrapy
- Anaconda (optional, for managing Python environments)

## Installation

1. Extract the zip file to your desired directory.

2. Create a virtual environment using Anaconda (optional but recommended):

   ```sh
   conda create -n domstol-scraper python=3.10
   ```

   and then activate the environement

   ```
   conda activate domstol-scraper
   ```

3. Install the required packages:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

1. Navigate to the project directory:

   ```sh
   cd legal_scraper/legal_scraper/spiders/scraper.py
   ```

2. Run the Scrapy spider:

   ```sh
   scrapy crawl domstol
   ```

   Or using:

   ```
   scrapy runspider scraper.py
   ```

3. The downloaded PDFs and metadata will be saved in the current directory.

## Logging

Logs are generated during the scraping process to help with debugging and monitoring. You can find the logs in the console output.

## Error Handling

The scraper includes robust error handling to ensure it handles exceptions gracefully. If any error occurs during the PDF download or metadata extraction, it will be logged with an appropriate message.

## Notes

- Ensure you have the correct headers for the requests. You may need to update the `headers` dictionary in `DomstolSpider` if the website changes.
- The scraper is set to download a maximum of 10 PDFs. You can change this limit by modifying the `self.pdf_limit` variable in the spider's `__init__` method.
