import scrapy
import logging
import json
from scrapy import signals
from scrapy.exceptions import CloseSpider

class DomstolSpider(scrapy.Spider):
    """
    Spider to scrape legal decisions from 'hogsta-domstolen'.
    """

    # Name of the Spider
    name = 'domstol'

    # Initial URLs to crawl
    start_urls = ['https://www.domstol.se/hogsta-domstolen/avgoranden/']

    # HTTP headers to use for the requests
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7',
        'Connection': 'keep-alive',
        'Content-Length': '0',
        'Content-Type': 'application/json',
        'Cookie': 'ASP.NET_SessionId=41os43uw32jusk5zuffhb11o; TS01b8d016=010ba75c4b6aaca1a8a944b54d73c67f257a569d4ce360c1fb1a8ffe648a2975487965640979b4abddff7cde309f822b6f657402e71f491b759ac502505408ece981354f2a; TSb150167c027=08203559eeab200074d1e05e5ea5a4bb2059608d7ef050fe4690f85a0ef3a3124b40f5ba77d8368e08800d18891130003995e99a0f4cfe91dd66bfc468883a5d087cd9d1656d4437c88ffe1d480f4de6f7a403feeb8b3d8f963240174ee7a1cf',
        'Dnt': '1',
        'Host': 'www.domstol.se',
        'Origin': 'https://www.domstol.se',
        'Referer': 'https://www.domstol.se/hogsta-domstolen/avgoranden/',
        'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'
    }

    def __init__(self, *args, **kwargs):
        """
        Initialize the DomstolSpider with a limit for PDF downloads.
        """
        super(DomstolSpider, self).__init__(*args, **kwargs)
        self.pdf_limit = 10

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """
        Create a spider instance from a Scrapy crawler and connect the spider_closed signal.

        Args:
            crawler (Crawler): The Scrapy Crawler instance.

        Returns:
            DomstolSpider: An instance of DomstolSpider.
        """
        spider = super(DomstolSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        """
        Handle actions to be taken when the spider is closed.

        Args:
            spider (Spider): The Scrapy Spider instance.
        """
        logging.info(f"Spider closed. Total PDFs downloaded: {self.crawler.stats.get_value('pdf_count', 0)}")

    def parse(self, response):
        """
        Initiate the search request to the specified API endpoint.

        Args:
            response (Response): The initial response from the start URL.
        """

        url = 'https://www.domstol.se/api/search/1122/?isZip=false&layoutRootId=0&query&scope=decision&searchPageId=15264&skip=0&sortMode=mostRecent'
        logging.info('before request ************')
        self.crawler.stats.set_value('pdf_count', 0)

        request = scrapy.Request(url, method='POST', callback=self.parse_api, headers=self.headers)
        
        logging.info(request)
        yield request

    def parse_api(self, response):
        """
        Parse the API response to extract search results, process each result, and fetch detailed metadata.

        Args:
            response (Response): The response from the API request.
        """
        base_url = 'https://www.domstol.se'
        raw_data = response.body

        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON response: {e}")
            return

        logging.info(f"Total search results fetched: {len(data['searchResultItems'])}")
        logging.info(f"Processing {len(data['searchResultItems'])} results")

        for result in data['searchResultItems']:
            current_count = self.crawler.stats.get_value('pdf_count', 0)
            if current_count >= self.pdf_limit:
                logging.info(f"Requested PDF limit Reached")
                break

            link = result['link']['link']
            trail = result['link']['trail']
            footer = result['footer']

            initial_metadata = {
                'title': link.get('title'),
                'url': base_url + link.get('url'),
                'pdf_url' : None,
                'case_number': None,
                'designation': None,
                'legal_provision': None,
                'legal_case': None,
                'keywords': None
            }

            logging.info(f"Processing result: {initial_metadata['title']} - {initial_metadata['url']}")
            detailed_page_url = base_url + link.get('url')
            logging.info(f"Requesting detailed page for metadata --- {detailed_page_url}")

            try:
                if detailed_page_url:
                    yield scrapy.Request(detailed_page_url, callback=self.parse_detailed_page_and_get_pdf_link, meta={'metadata': initial_metadata})
                else:
                    logging.warning(f"Invalid URL for detailed page: {detailed_page_url}")
            except Exception as e:
                logging.error(f"Failed to create request for detailed page: {e}")

        logging.info("Finished processing search results")

    def parse_detailed_page_and_get_pdf_link(self, response):
        """
        Parse the detailed page to extract metadata and PDF link.

        Args:
            response (Response): The response from the detailed page request.
        """

        metadata = response.meta['metadata']
        base_url = 'https://www.domstol.se'

        try:

            metadata['case_number'] = response.css('div:contains("Målnummer") + div .value-list__item > div::text').get()
            metadata['designation'] = response.css('div:contains("Benämning") + div .value-list__item > div::text').get()
            metadata['legal_provision'] = [provision.strip() for provision in response.css('div:contains("Lagrum") + ul > li::text').getall() if provision.strip()]
            metadata['legal_case'] = [legal_case.strip() for legal_case in response.css('div:contains("Rättsfall") + ul > li::text').getall() if legal_case.strip()]
            metadata['keywords'] = response.css('div:contains("Sökord") + div .value-list__item > a .link__label::text').getall()

            pdf_link = response.css('a[href$=".pdf"]::attr(href)').get()
            if pdf_link:
                pdf_url = base_url + pdf_link
                metadata['pdf_url'] = pdf_url
                logging.info(f"Extracted PDF URL: {pdf_url}")

                current_count = self.crawler.stats.get_value('pdf_count', 0)
                if current_count < self.pdf_limit:
                    yield scrapy.Request(pdf_url, callback=self.download_pdf, meta={'metadata': metadata})
                else:
                    logging.info(f"Requested PDF limit Reached")
            else:
                logging.warning(f"No PDF URL found for: {metadata['title']}")
        
        except Exception as e:
            logging.error(f"Failed to parse detailed page or extract PDF link: {e}")

    def download_pdf(self, response):
        """
        Download the PDF from the response and save the metadata.

        Args:
            response (Response): The response containing the PDF file.
        """

        current_count = self.crawler.stats.get_value('pdf_count', 0)
        if current_count >= self.pdf_limit:
            logging.info(f"Requested PDF limit Reached in download_pdf")
            raise CloseSpider('PDF limit reached')

        metadata = response.meta['metadata']
        pdf_filename = metadata['title'].replace(' ', '_') + '.pdf'

        try:
            # Save the PDF file
            with open(pdf_filename, 'wb') as f:
                f.write(response.body)
            logging.info(f"Downloaded PDF: {pdf_filename}")
        except Exception as e:
            logging.error(f"Failed to download PDF {pdf_filename}: {e}")
            return

        try:
            # Save the metadata to a JSON file
            with open('metadata.json', 'a', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
                f.write(',')
            logging.info(f"Metadata saved for PDF: {pdf_filename}")
        except Exception as e:
            logging.error(f"Failed to save metadata for PDF {pdf_filename}: {e}")
            return
        
        self.crawler.stats.inc_value('pdf_count')

        logging.info(f"Total PDFs downloaded: {self.crawler.stats.get_value('pdf_count', 0)}")
