# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrap.spiders import curseforge

if __name__ == "__main__":
    # Create a new instance of the spider
    spider = curseforge.CurseforgeSpider()

    # Create a new Scrapy crawler process
    process = CrawlerProcess(get_project_settings())

    # Start the spider by calling start_requests
    requests = spider.start_requests()
    for request in requests:
        process.crawl(spider, request=request)

    # Start the crawler process
    process.start()
    pass