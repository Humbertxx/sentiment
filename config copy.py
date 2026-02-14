FINHUB_API = 'd57mgbhr01qrcrnch4cgd57mgbhr01qrcrnch4d0'
ALPHA_VATAGE_API = 'E31VLHWAWLZXP6SB'
NEWS_API = 'fba0edf9b2fc4a26a4c04776f963510c'

def get_finhub():
    return FINHUB_API
def get_alpha_vantage():
    return ALPHA_VATAGE_API
def get_news_self_title():
    return NEWS_API 

ALPACA_KEY = 'PKPDLU27K3NIIQFYRECKACD5SG'
ALPACA_SECRET = '6iHRXM1ked9WxYfEMPe2Jiyrw9z82ZMm9cbh6F5QKpVT'

# can expand later on the amount of rss feeds
RSS_PREFER_NEWS = {'Yahoo Finance':'https://finance.yahoo.com/rss/headline?s={ticker}' }                                
    
SOURCE_WEIGHTS = {
    'Benzinga': 1.0,       
    'Yahoo Finance': 0.6,  
    'Unknown': 0.2
}
DEFAULT_WEIGHT = 0.5