import scrapy
import unicodedata
from scrapy.crawler import CrawlerProcess


def normalize_unicode_to_ascii(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


class CoursesSpider(scrapy.Spider):
    name = "courses"
    allowed_domains = ["catalog.northeastern.edu"]
    start_urls = ["https://catalog.northeastern.edu/undergraduate/computer-information-science/computer-science"]

    def parse(self, response):
        # Select course blocks
        course_blocks = response.css('div.courseblock')
        
        if not course_blocks:
            self.log("No course blocks found. Check your CSS selectors or the page structure.")

        for course in course_blocks:
            # Extract course title
            title_block = course.css('p.courseblocktitle strong::text').get(default='').strip()
            course_number = title_block.split('.')[0]
            course_name = title_block.split('.')[1].strip()


            # Extract course description
            description = course.css('p.cb_desc::text').get(default='').strip()  # Replace non-breaking spaces

            # Extract prerequisites
            prerequisites = course.css('p.courseblockextra:contains("Prerequisite(s):") a::text').getall()
            prerequisites = ', '.join(prerequisites).replace('\xa0', ' ')  # Replace non-breaking spaces

            # Extract attributes
            attributes = course.css('p.courseblockextra:contains("Attribute(s):")::text').getall()
            attributes = ', '.join(attributes).strip()

            yield {
                'course_number': normalize_unicode_to_ascii(course_number),
                'course_name': normalize_unicode_to_ascii(course_name),
                'description': normalize_unicode_to_ascii(description),
                'prerequisites': normalize_unicode_to_ascii(prerequisites),
                'attributes': normalize_unicode_to_ascii(attributes),
            }

# Configure and Run the Spider
if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'FEEDS': {
            'courses.json': {'format': 'json'},  # Save output to a JSON file
        },
        'ROBOTSTXT_OBEY': False,  # Ignore robots.txt for testing
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  # Set User-Agent
        'LOG_LEVEL': 'INFO',  # Set log level to see meaningful output
    })

    process.crawl(CoursesSpider)
    process.start()
