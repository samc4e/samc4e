# How this profile README works

The whole profile is two self-hosted SVGs, so nothing depends on a third-party
stats server staying up.

| File | What it is | How to change it |
| --- | --- | --- |
| `assets/hero.svg` | Animated banner: name, typing roles, terminal, stack ticker | Edit the lists at the top of `scripts/build_hero.py`, then run `python3 scripts/build_hero.py` and commit |
| `assets/stats.svg` | Contributions, merged PRs, streak, heatmap, top languages | Regenerated daily by `.github/workflows/stats.yml` — run it manually from the **Actions** tab any time |

`scripts/generate_stats.py` uses the workflow's built-in `GITHUB_TOKEN`; no
secrets to set up. If a run fails, the last good card stays in place.

To hide a language from the breakdown, edit `HIDE_LANGS` in
`scripts/generate_stats.py`.
