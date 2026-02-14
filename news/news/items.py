import scrapy

class NewsItem(scrapy.Item):
    date =  scrapy.Field()
    title = scrapy.Field()
    ticket = scrapy.Field()
    source = scrapy.Field()
    content = scrapy.Field()
    
    
