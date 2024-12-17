import scrapy
import logging
from scrapy.crawler import CrawlerProcess


class MajorRequirementsSpider(scrapy.Spider):
    name = "major_requirements"
    allowed_domains = ["catalog.northeastern.edu"]
    start_urls = ["https://catalog.northeastern.edu/undergraduate/computer-information-science/computer-science/bscs/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create a custom logger
        self.custom_logger = logging.getLogger("custom_logger")
        self.custom_logger.propagate = False
        self.custom_logger.setLevel(logging.DEBUG)

        # Create handlers
        file_handler = logging.FileHandler("logging/req_log.txt")
        console_handler = logging.StreamHandler()

        # Set logging format
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to the custom logger
        self.custom_logger.addHandler(file_handler)
        self.custom_logger.addHandler(console_handler)

    def parse(self, response):
        self.custom_logger.info(f"Scraping URL: {response.url}")

        all_tables = response.css('table.sc_courselist tbody')

        if not all_tables:
            self.custom_logger.warning(f"No tables found on {response.url}")
            return

        for table in all_tables:
            yield self.parse_table(table)

    def parse_table(self, table):
        table_name = table.xpath('preceding::h2[1]/span/text()').get()
        if not table_name:
            # If no span, just get the h2 text directly
            table_name = table.xpath('preceding::h2[1]/text()').get()

        table_rows = table.css('tbody > tr')
        grouped_requirements = []
        current_group = {'type': '', 'courses': []}

        self.custom_logger.info(f"Scraping table: {table_name}")

        for row in table_rows:
            header_class = row.attrib.get('class')

            self.custom_logger.info(f"Header class: {header_class}")

        return
        
if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'ROBOTSTXT_OBEY': False,  
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  # Set User-Agent
        'LOG_LEVEL': 'INFO',  
    })

    process.crawl(MajorRequirementsSpider)
    process.start()
