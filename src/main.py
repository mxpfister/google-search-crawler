from src.crawler import GoogleCrawler

crawler = GoogleCrawler()
keywords = open('../keywords', 'r')
keyword = keywords.readline()
while keyword:
    crawler.crawl_google(keyword, 20)
    keyword = keywords.readline()
keywords.close()
crawler.close()
