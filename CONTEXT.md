# Context: IBM Z Hackathon 2026 setup

Environment: Windows 11, Python 3.14.5, git 2.54 (Git for Windows with Git Credential Manager).

## What's been set up

- **Jupyter Notebook 7.6.3** installed via pip (user install). Note: its scripts folder
  (`C:\Users\Manny\AppData\Roaming\Python\Python314\Scripts`) is **not on PATH**, so use
  `python -m notebook` / `python -m jupyterlab` to launch, and `python -m nbconvert`
  (not `jupyter nbconvert`) to execute notebooks headlessly.
- **Private GitHub repo `SenorE7/IBM_Z_hackathon2026`** cloned to
  `C:\Users\Manny\Documents\IBM_Z_hackathon2026`. Default branch is `main`.
  Repo was near-empty (just a `README.md`).
- Authenticated using a **fine-grained personal access token** (single-repo,
  Contents read/write, 7-day expiry) cached in the local git config. Token must be
  revoked at https://github.com/settings/tokens when done (or expires in 7 days).
- Created **`notebook.ipynb`** in the repo: a markdown title cell, a setup code cell
  (`import sys; print(sys.version)`), and a scratch section.
- **Verified** it executes (cell ran, output `3.14.5 ...`), then committed and
  **pushed to `main`**.
  Live at https://github.com/SenorE7/IBM_Z_hackathon2026/blob/main/notebook.ipynb

## Working loop (confirmed)

Edit `.ipynb` cells directly → run via
`python -m nbconvert --to notebook --execute --inplace notebook.ipynb` → commit → push
to the real repo.

## Next step

Decide what the hackathon project is and start building it out in the notebook.
