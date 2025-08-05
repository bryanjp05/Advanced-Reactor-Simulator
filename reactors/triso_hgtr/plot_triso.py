import openmc
import glob
import matplotlib.pyplot as plt 
from PIL import Image

plots = openmc.Plots()

# XY slice at midplane
xy_plot = openmc.Plot()
xy_plot.filename = 'plot_xy'
xy_plot.origin = (0.0, 0.0, 0.0)
xy_plot.width = (4.0, 4.0)
xy_plot.pixels = (600, 600)
xy_plot.color_by = 'material'  # or 'cell'
xy_plot.basis = 'xy'
plots.append(xy_plot)

# XZ slice
xz_plot = openmc.Plot()
xz_plot.filename = 'plot_xz'
xz_plot.origin = (0.0, 0.0, 0.0)
xz_plot.width = (4.0, 4.0)
xz_plot.pixels = (600, 600)
xz_plot.color_by = 'material'
xz_plot.basis = 'xz'
plots.append(xz_plot)

# YZ slice
yz_plot = openmc.Plot()
yz_plot.filename = 'plot_yz'
yz_plot.origin = (0.0, 0.0, 0.0)
yz_plot.width = (4.0, 4.0)
yz_plot.pixels = (600, 600)
yz_plot.color_by = 'material'
yz_plot.basis = 'yz'
plots.append(yz_plot)

# Export and generate plots
plots.export_to_xml()
openmc.plot_geometry()

plot_files = sorted(glob.glob('plot_*.png'))

# Display each plot
for plot_file in plot_files:
    img = Image.open(plot_file)
    plt.figure(figsize=(6, 6))
    plt.imshow(img)
    plt.axis('off')
    plt.title(plot_file)
    plt.show()
