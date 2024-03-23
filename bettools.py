import pandas as pd
import numpy as np
from scipy.stats import poisson

def generate_seasons(start_year, end_year):
    seasons = []
    for year in range(start_year, end_year):
        start = str(year)[-2:]
        end = str(year + 1)[-2:]
        seasons.append(start + end)
    return seasons

def get_data(season_list, league_list, additional_cols=[]):
    
    col_list=['Div','Date','HomeTeam','AwayTeam','FTHG','FTAG','PSH','PSD','PSA','home_max_odds','away_max_odds']
    
    for col in additional_cols:
        col_list.append(col)

    df_ls = []
    
    bookmakers = ['B365','BW','IW','PS','WH','VC']

    home_cols = []
    away_cols = []
    
    for book in bookmakers:
        home_col = book + 'H'
        home_cols.append(home_col)
    
    for book in bookmakers:
        away_col = book + 'A'
        away_cols.append(away_col)
    
    for season in season_list:
        for league in league_list:
            try:
                df = pd.read_csv(f'https://www.football-data.co.uk/mmz4281/{season}/{league}.csv')
            except:
                df = pd.read_csv(f'https://www.football-data.co.uk/mmz4281/{season}/{league}.csv', encoding='latin')
            try:
                df["Date"] = pd.to_datetime(df["Date"],format="%d/%m/%y")
            except ValueError:
                df["Date"] = pd.to_datetime(df["Date"],format="%d/%m/%Y")
            existing_home_columns = [col for col in home_cols if col in df.columns]
            existing_away_columns = [col for col in away_cols if col in df.columns]
            
            df['home_max_odds'] = df[existing_home_columns].max(axis=1)
            df['away_max_odds'] = df[existing_away_columns].max(axis=1)
            
            df = df[col_list]
            df_ls.append(df)
    return df_ls

def calculate_poisson_match_outcomes(home_goals_expectation, away_goals_expectation):
    max_goals = 10
    home_probabilities = [poisson.pmf(i, home_goals_expectation) for i in range(0, max_goals+1)]
    away_probabilities = [poisson.pmf(i, away_goals_expectation) for i in range(0, max_goals+1)]
    
    home_win_prob = sum(home_probabilities[i] * sum(away_probabilities[:i]) for i in range(1, max_goals+1))
    draw_prob = sum(home_probabilities[i] * away_probabilities[i] for i in range(max_goals+1))
    away_win_prob = sum(away_probabilities[i] * sum(home_probabilities[:i]) for i in range(1, max_goals+1))
    
    return [home_win_prob, draw_prob, away_win_prob]

def calculate_ev_from_odds(bookmaker_odds, your_probability):
    payout = bookmaker_odds
    ev = (your_probability * payout) - 1
    return ev
