# Overview
- The project centers on implementing and analysing the Dixon–Coles football model alongside supporting betting utilities. Core functionality lives in `dixon_coles.py`, which fits attack/defence parameters, simulates score matrices, and derives betting recommendations via Kelly staking.【F:dixon_coles.py†L1-L292】
- Supporting helpers in `bettools.py` cover season generation, remote data ingestion, Poisson outcome maths, and bankroll tools that other modules depend on.【F:bettools.py†L1-L160】

# Environment & dependencies
- The repository is Python-focused and leans on a scientific stack including NumPy, SciPy, pandas, statsmodels, seaborn, and Jupyter tooling listed in `requirements.txt`; ensure compatible versions when adding packages.【F:requirements.txt†L1-L136】

# External data access
- Data retrieval functions fetch CSVs from `football-data.co.uk` over HTTPS, with fallbacks for encoding differences—plan for network access or provide local substitutes when modifying callers.【F:bettools.py†L56-L81】

# Coding standards
- Existing modules use NumPy/SciPy vectorisation and dictionary-based parameter storage; preserve these patterns when extending modelling logic to keep compatibility with the optimisation routines and match simulators.【F:dixon_coles.py†L30-L137】【F:process_chunk.py†L45-L191】

# Testing & validation
- There is no dedicated automated test suite; model validation currently happens through helper routines like `build_temp_model`/`get_total_score_xi` that score held-out matches. Plan manual or notebook-based verification when changing model code.【F:dixon_coles.py†L229-L257】【F:process_chunk.py†L126-L154】

# Notebook etiquette
- Several notebooks (`predict_with_dc.ipynb`, `validate_dc.ipynb`, etc.) support exploration, with the README guiding newcomers toward them. Avoid unnecessary re-execution artefacts when editing these notebooks to keep diffs manageable.【F:README.md†L1-L12】

# Shared logic awareness
- Dixon–Coles helpers (`rho_correction`, `dc_log_like`, `solve_parameters_decay`, and simulators) are duplicated between `dixon_coles.py` and `process_chunk.py`; consider consolidating or updating both locations to prevent drift.【F:dixon_coles.py†L8-L257】【F:process_chunk.py†L23-L191】

# Known pitfalls
- Both `dixon_coles.py` and `process_chunk.py` call `pickle.dump` without importing `pickle`, which will raise a `NameError` if those paths run—add the import alongside other dependencies when touching these modules.【F:dixon_coles.py†L1-L257】【F:process_chunk.py†L1-L154】
