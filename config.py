FINHUB_API = ''
ALPHA_VATAGE_API = ''
NEWS_API = ''

def get_finhub():
    return FINHUB_API
def get_alpha_vantage():
    return ALPHA_VATAGE_API
def get_news_self_title():
    return NEWS_API 

ALPACA_KEY = ''
ALPACA_SECRET = ''

# can expand later on the amount of rss feeds
RSS_PREFER_NEWS = {'Yahoo Finance':'https://finance.yahoo.com/rss/headline?s={ticker}' }                                
    
SOURCE_WEIGHTS = {
    'Benzinga': 1.0,       
    'Yahoo Finance': 0.6,  
    'Unknown': 0.2
}
DEFAULT_WEIGHT = 0.5