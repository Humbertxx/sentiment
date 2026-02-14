import pandas as pd
import feedparser 
import re, html, time
import queue
from alpaca.data.live import NewsDataStream
from config import RSS_PREFER_NEWS, ALPACA_KEY, ALPACA_SECRET
from datetime import datetime
from collections import deque
from difflib import SequenceMatcher
from sentiment import overall_scores
import threading
from concurrent.futures import ThreadPoolExecutor

# COMPILE REGEX ONCE (Global)
CLEAN_HTML = re.compile(r'<[^>]+>')
CLEAN_URLS = re.compile(r'http[s]?://\S+')
CLEAN_METADATA = re.compile(r'(Article URL|Comments URL|Points|# Comments):.*?(?=\n|$)')
CLEAN_SPACES = re.compile(r'\n\s*\n')

SEEN_HEADLINES = deque(maxlen=500) #store last 500 to avoid getting them again
POLL_INTERVAL = 5                  #How often to check (in seconds) — lowered for testing
news_queue = queue.Queue()
TIMEOUT_FETCH = 5                  #Timeout for individual feed fetches

def worker_logic():
    buffer = []
    while True:
        try:
            item = news_queue.get(timeout=5)
            buffer.append(item)
            print("worker received item. buffer size:", len(buffer))
            news_queue.task_done()
        except queue.Empty: # timeout, process whatever is in buffer
            if buffer:
                df_batch = pd.DataFrame(buffer)
                try:
                    overall_scores(df_batch)
                except Exception as e:
                    print(f"Error in pipeline: {e}")
                buffer = []

def fetch_ticker_rss(ticker):
    """Fetch RSS for a single ticker. Designed to run in parallel."""
    try:
        #print(f"Fetching RSS for {ticker}")
        url = RSS_PREFER_NEWS['Yahoo Finance'].format(ticker=ticker)
        feed = feedparser.parse(url)
        articles = []
        if feed.entries:
            for entry in feed.entries:
                description = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                if description:
                    description = html.unescape(description)
                    description = CLEAN_HTML.sub('', description)
                    description = CLEAN_URLS.sub('', description)
                    description = CLEAN_METADATA.sub('', description)
                    description = CLEAN_SPACES.sub('\n', description).strip()
                news_entry = {
                    "ticker": ticker,
                    "source": "Yahoo Finance",
                    "title": entry.title,
                    "description": description,
                    "link": entry.link,
                    "published": entry.published if hasattr(entry, 'published') else datetime.now()
                }
                articles.append(news_entry)
        return articles
    except Exception as e:
        print(f"Error fetching RSS for {ticker}: {e}")
        return []

def rss_market_news(tickers):
    executor = ThreadPoolExecutor(max_workers=5)
    while True:
        futures = [executor.submit(fetch_ticker_rss, ticker) for ticker in tickers]
        for future in futures:
            try:
                articles = future.result(timeout=TIMEOUT_FETCH)
                for article in articles:
                    if article['title'] not in SEEN_HEADLINES:
                        SEEN_HEADLINES.append(article['title'])
                        print(f"Enqueuing RSS article: {article['title']}")
                        news_queue.put(article)
            except Exception as e:
                print(f"Error processing article batch: {e}")
        time.sleep(POLL_INTERVAL)

def start_alpaca_stream(ticker):
    async def alpaca_handler(news):
        relevant_tickers = [t for t in news.symbols if t in ticker]
        if not relevant_tickers:
            return
        if news.headline in SEEN_HEADLINES:
            return
        SEEN_HEADLINES.append(news.headline)

        packet = {
            'source': 'Benzinga', # Alpaca news is almost always Benzinga
            'title': news.headline,
            'ticker': relevant_tickers[0],
            'timestamp': news.created_at
        }
        news_queue.put(packet)
        print(f"Enqueuing Alpaca article: {packet['title']}")
            
    stream_client = NewsDataStream(ALPACA_KEY, ALPACA_SECRET)
    stream_client.subscribe_news(alpaca_handler, *ticker)
    stream_client.run()
        
def combine_table(all_articles):
    if not all_articles:
        return pd.DataFrame()
    # Combine everything into one table
    full_df = pd.concat(all_articles, ignore_index=True)
    
    # Remove duplicates inside this batch
    full_df.drop_duplicates(subset=['title'], inplace=True)
    
    #Remove headlines we have ALREADY seen in previous loops
    new_articles = []
    for index, row in full_df.iterrows():
        headline = row['title']
        if headline not in SEEN_HEADLINES:
            new_articles.append(row)
            SEEN_HEADLINES.append(headline) # Mark as seen
    
    return pd.DataFrame(new_articles)

def is_duplicate(new_headline, seen_headlines, threshold=0.85):
    for seen in seen_headlines:
        if new_headline == seen:
            return True
            
        similarity = SequenceMatcher(None, new_headline, seen).ratio()
        if similarity > threshold:
            return True
            
    return False

if __name__ == "__main__":
    TICKERS = ["AAPL"]
    t_brain = threading.Thread(target=worker_logic, daemon=True)
    t_brain.start()
    print("Worker thread started")


   # t_rss = threading.Thread(target=rss_market_news, args=(TICKERS,), daemon=True)
    #t_rss.start()
    #print("RSS thread started, fetching news...")
    
    t_alpaca = threading.Thread(target=start_alpaca_stream, args=(TICKERS,), daemon=True)
    t_alpaca.start()
    print("Alpaca stream started")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")