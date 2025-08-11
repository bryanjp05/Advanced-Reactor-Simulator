#!/usr/bin/env python3
import os, sys, platform, subprocess
import openmc
import glob
from PIL import Image
import matplotlib.pyplot as plt

def open_file(path):
    try:
        if platform.system() == "Darwin":   # macOS
            subprocess.Popen(["open", path])
        elif platform.system() == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print(f"Could not open {path}: {e}")

def main():
    here = os.path.abspath(os.getcwd())
    geom_xml = os.path.join(here, "geometry.xml")
    if not os.path.exists(geom_xml):
        print(f"geometry.xml not found at: {geom_xml}")
        sys.exit(1)

    # Load geometry
    geom = openmc.Geometry.from_xml(geom_xml)

    # Common plot settings
    pixels = (1200, 1200)
    width = 20.0  # cm (adjust to cover your whole model)

    # Build plots
    plots = []
    for basis in ("xy", "xz", "yz"):
        p = openmc.Plot()
        p.basis = basis
        p.pixels = pixels
        p.width = (width, width)
        p.color_by = 'material'   # or 'cell' if you prefer
        p.colors = { openmc.Material(): (255,255,255) }
        p.filename = f"plot_{basis}"
        plots.append(p)

    openmc.Plots(plots).export_to_xml()
    openmc.plot_geometry()   # generates PNGs

    # Open the images
    paths = [os.path.join(here, f"{p.filename}.png") for p in plots]
    for path in paths:
        if os.path.exists(path):
            print(f"Saved: {path}")
            open_file(path)
        else:
            print(f"Did not find expected output: {path}")

    plot_files = sorted(glob.glob('plot_*.png'))
 
if __name__ == "__main__":
    main()

