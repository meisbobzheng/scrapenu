import scrapy
import logging
from scrapy.crawler import CrawlerProcess
from courses import normalize_unicode_to_ascii
from collections import defaultdict
import json
import scrapy
import re

def parse_prereq(prerequisite):
    extracted_text = []
    if not prerequisite:
        return ""
    for item in prerequisite:
        if isinstance(item, str):
            text = item.strip()
            extracted_text.append(text)
        elif item.root.tag == 'a':  # Check if it's a link
            text = item.xpath('text()').get()  # Extract the link text
            extracted_text.append(text)
        elif item.root.tag is None:  # Text node
            text = item.get().strip()
            extracted_text.append(text)

    # Join the text to create the desired structure
    result = ' '.join(extracted_text)
    return result


def parseCourseBlocks(course_blocks, college, logging):
    courses = []

    for course in course_blocks:
        # Extract course title
        title_block = course.css('p.courseblocktitle strong::text').get(default='').strip()
        if not title_block:
            logging.warning("No title block found for a course.")
            continue

        course_number = title_block.split('.')[0]
        course_name = title_block.split('.')[1].strip() if '.' in title_block else ''

        # Extract course description
        description = course.css('p.cb_desc::text').get(default='').strip().replace('\xa0', ' ')

        # Extract prerequisites
        raw_prerequisites = course.css('p.courseblockextra:contains("Prerequisite(s):")').getall()
        prerequisites = parse_prereq(raw_prerequisites)

        # Extract attributes
        attributes = course.css('p.courseblockextra:contains("Attribute(s):")::text').getall()
        attributes = ', '.join(attributes).strip()

        if course_number is 'CS 3000':
            logging.info(f"Found CS 3000: {course_number}, {course_name}")

        courses.append({
            'college': college,
            'course_number': normalize_unicode_to_ascii(course_number),
            'course_name': normalize_unicode_to_ascii(course_name),
            'description': normalize_unicode_to_ascii(description),
            'prerequisites': prerequisites,
            'attributes': normalize_unicode_to_ascii(attributes),
        })

    return courses

class GroupByCollegePipeline:
    """Pipeline to group courses by college and write them to a JSON file."""
    def __init__(self):
        self.college_courses = defaultdict(list)

    def process_item(self, item, spider):
        # Group courses by college
        college = item['college']
        self.college_courses[college].append(item)
        return item

    def close_spider(self, spider):
        # Sort courses within each college by course number
        for college in self.college_courses:
            self.college_courses[college].sort(key=lambda x: x['course_number'])

        # Save grouped and sorted data to a JSON file
        with open('courses_grouped.json', 'w') as f:
            json.dump(self.college_courses, f, indent=4)
        spider.custom_logger.info("Grouped and sorted courses saved to courses_grouped.json.")


class UGPageSpider(scrapy.Spider):
    name = "courses"
    allowed_domains = ["catalog.northeastern.edu"]
    start_urls = ["https://catalog.northeastern.edu/undergraduate/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create a custom logger
        self.custom_logger = logging.getLogger("custom_logger")
        self.custom_logger.propagate = False
        self.custom_logger.setLevel(logging.DEBUG)

        # Create handlers
        file_handler = logging.FileHandler("my_spider_log.txt")
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

        # Select college navigation items
        college_navs = response.css('ul.nav.levelone')

        for nav in college_navs:
            li_elements = nav.css("li")
            for li in li_elements:
                college = li.css("a::text").get()
                href = li.css("a::attr(href)").get()

                if college and href:
                    normalized_college = normalize_unicode_to_ascii(college)
                    self.custom_logger.info(f"Found College: {normalized_college}, URL: {href}")

                    # Follow the link and pass data to the callback
                    yield response.follow(
                        href,
                        callback=self.parse_college,
                        cb_kwargs={"college": normalized_college, "depth": 0},
                    )

    def parse_college(self, response, college, depth):
        # self.custom_logger.info(f"Parsing college page: {response.url}, Depth: {depth}")

        # Select course blocks
        course_blocks = response.css('div.courseblock')

        if not course_blocks:
            self.custom_logger.info(f"No course blocks found on {response.url}. Checking for nested links...")
            if depth < 2:  # Limit recursion depth
                nested_links = response.xpath('//li[contains(@class, "active") and contains(@class, "isparent") and contains(@class, "self")]//ul/li/a')

                if not nested_links:
                   # self.custom_logger.warning(f"No nested links found on {response.url}. Probably not a valid college.")
                    return

                for link in nested_links:
                    href = link.xpath('@href').get()
                    if href:
                     #   self.custom_logger.info(f"Following nested link: {href}")
                        yield response.follow(
                            href,
                            callback=self.parse_college,
                            cb_kwargs={"college": college, "depth": depth + 1},
                        )
            else:
               self.custom_logger.info("Maximum depth reached. Stopping recursion.")
            return

        # Parse course blocks
        courses = parseCourseBlocks(course_blocks, college, self.custom_logger)

        if courses:
            for course in courses:
                yield course




# Configure and Run the Spider
if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'ITEM_PIPELINES': {
            '__main__.GroupByCollegePipeline': 300,  # Use the pipeline for grouping
        },
        'ROBOTSTXT_OBEY': False,  # Ignore robots.txt for testing
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  # Set User-Agent
        'LOG_LEVEL': 'INFO',  # Set log level for debugging
    })

    process.crawl(UGPageSpider)
    process.start()
