import marimo

__generated_with = "0.9.18"
app = marimo.App(width="full")


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    from itertools import product
    from pathlib import Path
    return Path, mo, pd, product


@app.cell
def __():
    leagues = ['E0','E1','E2','E3','EC','SC0','SC1','SC2','SC3']
    seasons = ['1617','1718','1819','1920','2021','2122','2223','2324','2425','2526']
    return leagues, seasons


@app.cell
def __(leagues, mo, seasons):
    league_filter = mo.ui.multiselect(
        options=leagues,
        label="Leagues",
    )

    season_filter = mo.ui.multiselect(
        options=seasons,
        label="Seasons",
    )

    filters = (
        mo.md("### League and Season Filters\n\n{league}\n\n{season}")
        .batch(league=league_filter, season=season_filter)
        .form(submit_button_label="Apply filters")
    )

    filters

    return filters, league_filter, season_filter


@app.cell
def __(mo):
    run = mo.ui.run_button(label="Fetch selected ✅")
    run
    return (run,)


@app.cell
def __(Path, filters, mo, pd, product, run):
    # Only proceed once the user has pressed Fetch
    mo.stop(not run.value, "Pick leagues/seasons, click **Apply filters**, then click **Fetch ✅**")

    selected_leagues = filters.value.get("league", [])
    selected_seasons = filters.value.get("season", [])

    mo.stop(not selected_leagues or not selected_seasons,
            "You need at least **one league** and **one season** selected")

    RAW_DATA_DIR = "data/raw"

    def load_league_season(league: str, season: str) -> pd.DataFrame:
        df = pd.read_csv(f'https://www.football-data.co.uk/mmz4281/{season}/{league}.csv')
        return df

    errors = []

    for league, season in product(selected_leagues, selected_seasons):
        try:
            df = load_league_season(league, season)
            p = Path(f'data/raw/{league}')
            p.mkdir(parents=True, exist_ok=True)
            df.to_csv(p / f'{season}.csv', index=False)
        except Exception as e:
            errors.append({"league": league, "season": season, "error": str(e)})

    if errors:
        mo.md("### ⚠️ Errors")
        pd.DataFrame(errors)

    return (
        RAW_DATA_DIR,
        df,
        errors,
        league,
        load_league_season,
        p,
        season,
        selected_leagues,
        selected_seasons,
    )


if __name__ == "__main__":
    app.run()
