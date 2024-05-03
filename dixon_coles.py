import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson

from bettools import calculate_ev_from_odds, kelly_criterion


def rho_correction(x, y, lambda_x, mu_y, rho):
    if x == 0 and y == 0:
        return 1 - (lambda_x * mu_y * rho)
    elif x == 0 and y == 1:
        return 1 + (lambda_x * rho)
    elif x == 1 and y == 0:
        return 1 + (mu_y * rho)
    elif x == 1 and y == 1:
        return 1 - rho
    else:
        return 1.0


def dc_log_like(x, y, alpha_x, beta_x, alpha_y, beta_y, rho, gamma):
    lambda_x, mu_y = np.exp(alpha_x + beta_y + gamma), np.exp(alpha_y + beta_x)
    return (
        np.log(rho_correction(x, y, lambda_x, mu_y, rho))
        + np.log(poisson.pmf(x, lambda_x))
        + np.log(poisson.pmf(y, mu_y))
    )


def solve_parameters(
    dataset,
    debug=False,
    init_vals=None,
    options={"disp": True, "maxiter": 100},
    constraints=[{"type": "eq", "fun": lambda x: sum(x[:20]) - 20}],
    **kwargs
):
    teams = np.sort(dataset["HomeTeam"].unique())
    # check for no weirdness in dataset
    away_teams = np.sort(dataset["AwayTeam"].unique())
    if not np.array_equal(teams, away_teams):
        raise ValueError("Something's not right")
    n_teams = len(teams)
    if init_vals is None:
        # random initialisation of model parameters
        init_vals = np.concatenate(
            (
                np.random.uniform(0, 1, (n_teams)),  # attack strength
                np.random.uniform(0, -1, (n_teams)),  # defence strength
                np.array([0, 1.0]),  # rho (score correction), gamma (home advantage)
            )
        )

    def dc_log_like(x, y, alpha_x, beta_x, alpha_y, beta_y, rho, gamma):
        lambda_x, mu_y = np.exp(alpha_x + beta_y + gamma), np.exp(alpha_y + beta_x)
        return (
            np.log(rho_correction(x, y, lambda_x, mu_y, rho))
            + np.log(poisson.pmf(x, lambda_x))
            + np.log(poisson.pmf(y, mu_y))
        )

    def estimate_paramters(params):
        score_coefs = dict(zip(teams, params[:n_teams]))
        defend_coefs = dict(zip(teams, params[n_teams : (2 * n_teams)]))
        rho, gamma = params[-2:]
        log_like = [
            dc_log_like(
                row.FTHG,
                row.FTAG,
                score_coefs[row.HomeTeam],
                defend_coefs[row.HomeTeam],
                score_coefs[row.AwayTeam],
                defend_coefs[row.AwayTeam],
                rho,
                gamma,
            )
            for row in dataset.itertuples()
        ]
        return -sum(log_like)

    opt_output = minimize(
        estimate_paramters,
        init_vals,
        options=options,
        constraints=constraints,
        **kwargs
    )
    if debug:
        # sort of hacky way to investigate the output of the optimisation process
        return opt_output
    else:
        return dict(
            zip(
                ["attack_" + team for team in teams]
                + ["defence_" + team for team in teams]
                + ["rho", "home_adv"],
                opt_output.x,
            )
        )


def calc_means(param_dict, homeTeam, awayTeam):
    return [
        np.exp(
            param_dict["attack_" + homeTeam]
            + param_dict["defence_" + awayTeam]
            + param_dict["home_adv"]
        ),
        np.exp(param_dict["defence_" + homeTeam] + param_dict["attack_" + awayTeam]),
    ]


def dixon_coles_simulate_match(params_dict, homeTeam, awayTeam, max_goals=10):
    team_avgs = calc_means(params_dict, homeTeam, awayTeam)
    team_pred = [
        [poisson.pmf(i, team_avg) for i in range(0, max_goals + 1)]
        for team_avg in team_avgs
    ]
    output_matrix = np.outer(np.array(team_pred[0]), np.array(team_pred[1]))
    correction_matrix = np.array(
        [
            [
                rho_correction(
                    home_goals,
                    away_goals,
                    team_avgs[0],
                    team_avgs[1],
                    params_dict["rho"],
                )
                for away_goals in range(2)
            ]
            for home_goals in range(2)
        ]
    )
    output_matrix[:2, :2] = output_matrix[:2, :2] * correction_matrix
    return output_matrix


def dc_log_like_decay(x, y, alpha_x, beta_x, alpha_y, beta_y, rho, gamma, t, xi=0):
    lambda_x, mu_y = np.exp(alpha_x + beta_y + gamma), np.exp(alpha_y + beta_x)
    return np.exp(-xi * t) * (
        np.log(rho_correction(x, y, lambda_x, mu_y, rho))
        + np.log(poisson.pmf(x, lambda_x))
        + np.log(poisson.pmf(y, mu_y))
    )


def solve_parameters_decay(
    dataset,
    xi=0.001,
    debug=False,
    init_vals=None,
    options={"disp": True, "maxiter": 100},
    constraints=[{"type": "eq", "fun": lambda x: sum(x[:20]) - 20}],
    **kwargs
):
    teams = np.sort(dataset["HomeTeam"].unique())
    # check for no weirdness in dataset
    away_teams = np.sort(dataset["AwayTeam"].unique())
    if not np.array_equal(teams, away_teams):
        raise ValueError("something not right")
    n_teams = len(teams)
    if init_vals is None:
        # random initialisation of model parameters
        init_vals = np.concatenate(
            (
                np.random.uniform(0, 1, (n_teams)),  # attack strength
                np.random.uniform(0, -1, (n_teams)),  # defence strength
                np.array([0, 1.0]),  # rho (score correction), gamma (home advantage)
            )
        )

    def dc_log_like_decay(x, y, alpha_x, beta_x, alpha_y, beta_y, rho, gamma, t, xi=xi):
        lambda_x, mu_y = np.exp(alpha_x + beta_y + gamma), np.exp(alpha_y + beta_x)
        return np.exp(-xi * t) * (
            np.log(rho_correction(x, y, lambda_x, mu_y, rho))
            + np.log(poisson.pmf(x, lambda_x))
            + np.log(poisson.pmf(y, mu_y))
        )

    def estimate_paramters(params):
        score_coefs = dict(zip(teams, params[:n_teams]))
        defend_coefs = dict(zip(teams, params[n_teams : (2 * n_teams)]))
        rho, gamma = params[-2:]
        log_like = [
            dc_log_like_decay(
                row.FTHG,
                row.FTAG,
                score_coefs[row.HomeTeam],
                defend_coefs[row.HomeTeam],
                score_coefs[row.AwayTeam],
                defend_coefs[row.AwayTeam],
                rho,
                gamma,
                row.time_diff,
                xi=xi,
            )
            for row in dataset.itertuples()
        ]
        return -sum(log_like)

    opt_output = minimize(
        estimate_paramters, init_vals, options=options, constraints=constraints
    )
    if debug:
        # sort of hacky way to investigate the output of the optimisation process
        return opt_output
    else:
        return dict(
            zip(
                ["attack_" + team for team in teams]
                + ["defence_" + team for team in teams]
                + ["rho", "home_adv"],
                opt_output.x,
            )
        )


def get_1x2_probs(match_score_matrix):
    return dict(
        {
            "H": np.sum(np.tril(match_score_matrix, -1)),
            "A": np.sum(np.triu(match_score_matrix, 1)),
            "D": np.sum(np.diag(match_score_matrix)),
        }
    )


def build_temp_model(dataset, time_diff, xi=0.000, init_params=None):
    test_dataset = dataset[
        (
            (dataset["time_diff"] <= time_diff)
            & (dataset["time_diff"] >= (time_diff - 2))
        )
    ]
    if len(test_dataset) == 0:
        return 0
    train_dataset = dataset[dataset["time_diff"] > time_diff]
    train_dataset["time_diff"] = train_dataset["time_diff"] - time_diff
    params = solve_parameters_decay(train_dataset, xi=xi, init_vals=init_params)
    predictive_score = sum(
        [
            np.log(
                get_1x2_probs(
                    dixon_coles_simulate_match(params, row.HomeTeam, row.AwayTeam)
                )[row.FTR]
            )
            for row in test_dataset.itertuples()
        ]
    )
    return predictive_score


def get_total_score_xi(xi):
    xi_result = [build_temp_model(dc_df, day, xi=xi) for day in range(99, -1, -3)]
    with open("find_xi_1season_{}.txt".format(str(xi)[2:]), "wb") as thefile:
        pickle.dump(xi_result, thefile)


def make_betting_prediction(
    home_odds,
    draw_odds,
    away_odds,
    params,
    home_team,
    away_team,
    bankroll,
    kelly_fraction=0.05,
):
    predicted_probs = get_1x2_probs(
        dixon_coles_simulate_match(params, home_team, away_team, max_goals=10)
    )
    home_ev = calculate_ev_from_odds(home_odds, predicted_probs["H"])
    away_ev = calculate_ev_from_odds(away_odds, predicted_probs["A"])
    draw_ev = calculate_ev_from_odds(draw_odds, predicted_probs["D"])
    max_ev = max([home_ev, away_ev, draw_ev])
    if max_ev == home_ev:
        bet_amount = kelly_criterion(
            predicted_probs["H"], home_odds, bankroll, kelly_fraction=kelly_fraction
        )
        bet_selection = "Home"
    if max_ev == away_ev:
        bet_amount = kelly_criterion(
            predicted_probs["A"], away_odds, bankroll, kelly_fraction=kelly_fraction
        )
        bet_selection = "Away"
    elif max_ev == draw_ev:
        bet_amount = kelly_criterion(
            predicted_probs["D"], draw_odds, bankroll, kelly_fraction=kelly_fraction
        )
        bet_selection = "Draw"
    return bet_selection, bet_amount
