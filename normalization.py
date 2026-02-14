import pandas as pd

def normalize(df1, df2):
    df = collected_data(df1,df2)
    df = concatenate_text(df)
    df = time_fix(df)
    return df

def collected_data(df_api, df_rss):
    return pd.concat([df_api, df_rss], ignore_index=True)

def time_fix(df):
    df['published'] = pd.to_datetime(df['published'], utc=True, format='mixed')
    return df

def concatenate_text(df):
    df['description'] = df['description'].fillna('')
    df['full_text'] = df['title'] + ". " + df['description']
    return df