# advanced-reactor-sim

A playground for **advanced reactor** Monte Carlo analyses with **OpenMC**, including MSR, SFR, and HTGR models, depletion, and post-processing tools.

## Features

- Modular per-reactor folders (`msr`, `sfr`, `htgr`) with shared utilities in `reactors/common`
- Depletion (CECM) helper with clean API
- Plotting helpers (k-effective vs time, spectra)
- Scripts to export results to CSV/PNG

## Quick start

```bash
conda env create -f env/environment.yml
conda activate openmc-adv

# Set your cross sections
export OPENMC_CROSS_SECTIONS=/path/to/cross_sections.xml

# Run a simple MSR eigenvalue case
python -m reactors.msr.runs.run_msr

# Run with depletion
python -m reactors.msr.runs.run_msr --deplete   # (add argparse if you like)

