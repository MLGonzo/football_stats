import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson


def generate_seasons(start_year, end_year):
    seasons = []
    for year in range(start_year, end_year):
        start = str(year)[-2:]
        end = str(year + 1)[-2:]
        seasons.append(start + end)
    return seasons


def get_data(season_list, league_list, additional_cols=[]):

    col_list = [
        "Div",
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "PSH",
        "PSD",
        "PSA",
        "home_max_odds",
        "away_max_odds",
        "draw_max_odds",
    ]

    for col in additional_cols:
        col_list.append(col)

    df_ls = []

    bookmakers = ["B365", "BW", "IW", "PS", "WH", "VC"]

    home_cols = []
    away_cols = []
    draw_cols = []

    for book in bookmakers:
        home_col = book + "H"
        home_cols.append(home_col)

    for book in bookmakers:
        away_col = book + "A"
        away_cols.append(away_col)

    for book in bookmakers:
        draw_col = book + "D"
        draw_cols.append(draw_col)

    for season in season_list:
        for league in league_list:
            try:
                df = pd.read_csv(
                    f"https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
                )
            except:
                df = pd.read_csv(
                    f"https://www.football-data.co.uk/mmz4281/{season}/{league}.csv",
                    encoding="latin",
                )
            try:
                df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%y")
            except ValueError:
                df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
            existing_home_columns = [col for col in home_cols if col in df.columns]
            existing_away_columns = [col for col in away_cols if col in df.columns]
            existing_draw_columns = [col for col in draw_cols if col in df.columns]

            df["home_max_odds"] = df[existing_home_columns].max(axis=1)
            df["away_max_odds"] = df[existing_away_columns].max(axis=1)
            df["draw_max_odds"] = df[existing_draw_columns].max(axis=1)

            df = df[col_list]
            df_ls.append(df)
    return df_ls


def calculate_poisson_match_outcomes(home_goals_expectation, away_goals_expectation):
    max_goals = 10
    home_probabilities = [
        poisson.pmf(i, home_goals_expectation) for i in range(0, max_goals + 1)
    ]
    away_probabilities = [
        poisson.pmf(i, away_goals_expectation) for i in range(0, max_goals + 1)
    ]

    home_win_prob = sum(
        home_probabilities[i] * sum(away_probabilities[:i])
        for i in range(1, max_goals + 1)
    )
    draw_prob = sum(
        home_probabilities[i] * away_probabilities[i] for i in range(max_goals + 1)
    )
    away_win_prob = sum(
        away_probabilities[i] * sum(home_probabilities[:i])
        for i in range(1, max_goals + 1)
    )

    return [home_win_prob, draw_prob, away_win_prob]


def calculate_ev_from_odds(bookmaker_odds, your_probability):
    payout = bookmaker_odds
    ev = (your_probability * payout) - 1
    return ev


def find_best_fit_goals(prob_home_win, prob_draw, prob_away_win):
    """
    Find the expected goals for home and away teams that best fit the given win, draw, and away win probabilities.
    This is a simplified estimation and does not perform a complex optimization due to the complexity of the task.
    """
    # Initial guesses for average goals scored by home and away teams
    avg_goals_home = 1.4
    avg_goals_away = 1.1

    # Define a simple error function to minimize
    def error_function(guess):
        home, away = guess
        # Calculate win, draw, and lose probabilities using Poisson distribution
        max_goals = 10  # Maximum number of goals to consider for calculation
        prob_draw_estimated = sum(
            poisson.pmf(i, home) * poisson.pmf(i, away) for i in range(max_goals)
        )
        prob_home_win_estimated = sum(
            poisson.pmf(i, home) * sum(poisson.pmf(j, away) for j in range(i))
            for i in range(1, max_goals)
        )
        prob_away_win_estimated = sum(
            poisson.pmf(i, away) * sum(poisson.pmf(j, home) for j in range(i))
            for i in range(1, max_goals)
        )

        # Error based on the difference between estimated and actual probabilities
        error = (
            (prob_home_win_estimated - prob_home_win) ** 2
            + (prob_draw_estimated - prob_draw) ** 2
            + (prob_away_win_estimated - prob_away_win) ** 2
        )
        return error

    # Use optimization to minimize the error function
    initial_guess = [avg_goals_home, avg_goals_away]
    result = minimize(error_function, initial_guess, bounds=((0, None), (0, None)))

    if result.success:
        fitted_goals_home, fitted_goals_away = result.x
        return fitted_goals_home, fitted_goals_away
    else:
        return None


def kelly_criterion(probability, odds, bankroll, kelly_fraction=1.0):
    """
    Calculate the optimal betting amount using the Kelly Criterion, with an option to use a fraction of the full recommendation.

    Parameters:
    - probability: The probability of the outcome occurring.
    - odds: The decimal odds offered for the bet.
    - bankroll: The current amount in your bankroll.
    - kelly_fraction: Fraction of the Kelly bet to use (default is 1.0 for 100%).

    Returns:
    - The optimal amount to bet from your bankroll, adjusted by the specified Kelly fraction.
    """
    b = odds - 1  # Convert decimal odds to b in the formula
    q = 1 - probability  # Probability of losing

    # Calculate the fraction of the bankroll to bet, according to the Kelly Criterion
    f_star = (b * probability - q) / b

    # Adjust the fraction with the specified Kelly fraction
    f_star = max(f_star, 0) * kelly_fraction

    # Calculate the amount to bet
    bet_amount = f_star * bankroll

    return bet_amount


def calculate_overround(odds_list):
    """
    This function calculates the overround from a list of odds.
    It will return a negative number if the sum of the implied probabilities of the odds is greater than one
    """
    # Convert each odd in the list to implied probability
    implied_probabilities = [1 / odd for odd in odds_list]
    # Sum up all the implied probabilities
    total_implied_probability = sum(implied_probabilities)
    # Calculate overround
    overround = (total_implied_probability - 1) * 100
    return overround


def calculate_exchange_overround(odds_list, commission_rate):
    """
    This function calculates the overround from a list of odds for an exchange, adding in the comission rate.
    The comission should be given as a decimal representation of the percentage (2% = 0.02 etc.)
    """
    odds_minus_comission = []
    for odd in odds_list:
        profit = odd - 1
        comm_profit = profit * (1 - commission_rate)
        revised_odd = comm_profit + 1
        odds_minus_comission.append(revised_odd)
    # Convert each odd in the list to implied probability
    implied_probabilities = [1 / odd for odd in odds_minus_comission]
    # Sum up all the adjusted implied probabilities
    total_adjusted_implied_probability = sum(implied_probabilities)
    # Calculate overround with commission
    overround = (total_adjusted_implied_probability - 1) * 100
    return overround


def find_true_probabilities_equal(odds):
    # Convert odds to implied probabilities
    probabilities = [1 / o for o in odds]
    # Calculate the total implied probability
    total_probability = sum(probabilities)
    # Calculate the overround
    overround = total_probability - 1
    # Calculate the adjustment factor for each odd
    adjustment_factor = overround / len(odds)
    # Adjust each implied probability
    adjusted_probabilities = [(1 / o) - adjustment_factor for o in odds]
    return np.array(adjusted_probabilities)


def find_true_probabilities_power(odds):
    # Convert odds to implied probabilities
    probabilities = np.array([1 / o for o in odds])

    # Define the objective function to minimize
    def objective(k):
        adj_probs = probabilities**k
        return (1 - np.sum(adj_probs)) ** 2

    # Initial guess for k
    initial_k = [1.0]
    # Bounds for k, ensuring k is not zero
    bounds = [(0.001, None)]
    # Minimize the objective function
    result = minimize(objective, initial_k)
    # Calculate the true probabilities using the optimized k
    adjusted_true_probabilities = probabilities ** (result.x[0])
    return adjusted_true_probabilities
