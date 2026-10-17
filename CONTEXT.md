# Ghazipur Landfill Fire & Contamination Shield

**IBM Z Datathon 2026 — Theme 1: Real-time AI for critical decisions**

## The project

A real-time decision system for the Ghazipur landfill (Delhi). It predicts fires before
they start, decides what to dig first, and tells people what to do about it.

Four parts:

1. **Model (ML)** — predicts which of the **12 landfill zones** will catch fire in the
   next 24h, from: methane, surface temp, humidity, wind, days since rain.
2. **Rules layer (not ML)** — highest-risk zone = dig first; excavated waste is split
   across processing plants by capacity.
3. **GenAI** — writes plain-English smoke/health alerts for residents downwind, and a
   daily action plan for site crews.
4. **Dashboard** — map of the 12 zones coloured by risk, simulated live sensor readings,
   an action panel, and an alert panel.

## Compute split

- **Model training/inference runs on IBM LinuxONE** (Jupyter Lab).
- **Laptop is for data, dashboard, and prototyping only.**

## Data

- Synthetic sensor data (clearly disclosed as synthetic).
- Real **NASA FIRMS** fire detections and **Open-Meteo** weather as supporting evidence.

## Deadline rule

If the **map + model + alert** aren't working together **by 8pm**, **cut the rules layer.**

---

# Repo / environment setup

Environment: Windows 11 Pro, Python 3.14.5, pip 26.1.1, git 2.54 (Git for Windows with
Git Credential Manager). User: SenorE7 / eobehie@gmail.com.

## Tooling

- **Jupyter Notebook 7.6.3** installed via pip (user install). Its scripts folder
  (`C:\Users\Manny\AppData\Roaming\Python\Python314\Scripts`) is **not on PATH**, so use
  `python -m notebook` / `python -m jupyterlab` to launch, and `python -m nbconvert`
  (not `jupyter nbconvert`) to execute notebooks headlessly.
- Repo: **`SenorE7/IBM_Z_hackathon2026`**, cloned to
  `C:\Users\Manny\Documents\IBM_Z_hackathon2026`. Default branch `main`.
- Auth via a fine-grained PAT (single-repo, Contents read/write, 7-day expiry) cached in
  the local git config. Revoke at https://github.com/settings/tokens when done.

## Folder structure

```
data/        synthetic + real data and generators
models/      trained models + training/inference code (runs on LinuxONE)
dashboard/   risk map, sensor readings, action + alert panels
notebooks/   exploration / prototyping notebooks
docs/        write-up, data disclosure, submission material
```

## Working loop (confirmed)

Edit code / `.ipynb` → run (`python script.py` or
`python -m nbconvert --to notebook --execute --inplace nb.ipynb`) → `git commit` →
`git push origin main`.

## Progress

- [x] Jupyter installed, repo connected, working loop verified
- [x] Project defined, folder structure created
- [x] `data/generate_data.py` — synthetic hourly sensor dataset for 12 zones over 90 days
- [ ] Fire-prediction model (on LinuxONE)
- [ ] Rules layer (dig order + plant allocation)
- [ ] GenAI alerts + daily action plan
- [ ] Dashboard (map + sensors + action + alert panels)
- [ ] Integrate NASA FIRMS + Open-Meteo supporting evidence
