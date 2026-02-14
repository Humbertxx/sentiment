import pandas as pd
from difflib import SequenceMatcher
from transformers import pipeline
from config import SOURCE_WEIGHTS, DEFAULT_WEIGHT


sentiment_pipe = pipeline("text-classification", model="ProsusAI/finbert", top_k=None)
print("FinBERT Ready.")

def overall_scores(df):
    if df.empty:
        print("No data to process.")
        return
    df = remove_similar_rows_weighted(df, SOURCE_WEIGHTS)
    df = calculated_weighted_sentiment(df, sentiment_pipe)
    score = news_weights(df)
    results(df, score)

def remove_similar_rows_weighted(df, weights_dict, threshold=0.85, time_window=1800):
    df['published'] = pd.to_datetime(df['published'], utc=True)
    df_clean = df.sort_values(by='published').reset_index(drop=True).copy()
    
    df_clean['temp_weight'] = df_clean['source'].map(weights_dict).fillna(DEFAULT_WEIGHT)
    indices_to_drop = set()
    
    for i in range(len(df_clean)):
        if i in indices_to_drop:
            continue
        current_row = df_clean.iloc[i]
        
        for j in range(i + 1, len(df_clean)):
            if j in indices_to_drop:
                continue   
            compare_row = df_clean.iloc[j]
            
            time_diff = (compare_row['published'] - current_row['published']).total_seconds()
            
            if time_diff > time_window:
                break
            
            ratio = SequenceMatcher(None, current_row['title'], compare_row['title']).ratio()
            if ratio > threshold:
                if current_row['temp_weight'] < compare_row['temp_weight']:
                    indices_to_drop.add(i)
                    break 
                else:
                    indices_to_drop.add(j)
    return df_clean.drop(index=list(indices_to_drop)).drop(columns=['temp_weight']).reset_index(drop=True)
     
def calculated_weighted_sentiment(df, pipe):
    texts = df['title'].tolist() # Using Title is often cleaner than full_text for headlines
    raw_results = pipe(texts)
    
    sentiment_scores = []
    
    for result in raw_results:
        scores = {item['label']: item['score'] for item in result}
        # Calculate Scalar: Positive - Negative
        scalar = scores.get('positive', 0) - scores.get('negative', 0)
        sentiment_scores.append(scalar)
        
    df['sentiment_score'] = sentiment_scores
    df['weight'] = df['source'].map(SOURCE_WEIGHTS).fillna(DEFAULT_WEIGHT)
    df['weighted_contribution'] = df['sentiment_score'] * df['weight']
    return df

def news_weights(df):  
    total_weight = df['weight'].sum()
    if total_weight == 0:
        return 0
    final_signal_score = df['weighted_contribution'].sum() / total_weight
    return final_signal_score

def results(overall_dataframe, final_signal_score):
    print("\n" + "="*50)
    print("PROCESSED DATAFRAME (Top 5)")
    print("="*50)
    cols_to_show = ['published', 'source', 'sentiment_score', 'weight', 'title']
    print(overall_dataframe[cols_to_show].head())

    print("\n" + "="*50)
    print("FINAL TRADING SIGNAL")
    print("="*50)
    print(f"Aggregated Sentiment Score: {final_signal_score:.4f}")

    if final_signal_score > 0.2:
        print("Signal: STRONG BUY")
    elif final_signal_score > 0.05:
        print("Signal: WEAK BUY")
    elif final_signal_score < -0.2:
        print("Signal: STRONG SELL")
    elif final_signal_score < -0.05:
        print("Signal: WEAK SELL")
    else:
        print("Signal: HOLD / NEUTRAL")
    
    
