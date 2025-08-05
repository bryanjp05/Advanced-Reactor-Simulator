import openmc
from openmc.model import TRISO, create_triso_lattice

from materials import build_materials

def build_geometry():
    # Load materials
    fuel, buffer, inner_pyc, sic, outer_pyc, matrix = build_materials()
    layers = [fuel, buffer, inner_pyc, sic, outer_pyc]
 
    radii = [0.01, 0.015, 0.02, 0.025, 0.03]  # cm, for example

    layer_cells = []
    prev_radius = 0.0
    for mat, r in zip(layers, radii):
        sphere_outer = openmc.Sphere(r=r)
        region = -sphere_outer
        if prev_radius > 0.0:
            sphere_inner = openmc.Sphere(r=prev_radius)
            region = +sphere_inner & -sphere_outer
        cell = openmc.Cell(fill=mat, region=region)
        layer_cells.append(cell)
        prev_radius = r

    triso_universe = openmc.Universe(cells=layer_cells)

    # Create a single TRISO particle
    triso_center = (0.0, 0.0, 0.0)
    triso_particle = TRISO(radii[-1], triso_universe, triso_center)
 
    # Define lattice properties
    trisos = [triso_particle] 
    pitch = (0.1, 0.1, 0.1)  # spacing in x, y, z
    shape = (1, 1, 1)        # one TRISO in a single lattice cell
    lower_left = (-0.05, -0.05, -0.05)

    lattice = create_triso_lattice(trisos, lower_left, pitch, shape, matrix)

    # Create a cell that contains the lattice
    lattice_cell = openmc.Cell(fill=lattice)

    # Boundary
    boundary = openmc.Sphere(r=1.0, boundary_type='vacuum')
    lattice_cell.region = -boundary

    # Universe and geometry
    root_universe = openmc.Universe(cells=[lattice_cell])
    geometry = openmc.Geometry(root_universe)
    geometry.export_to_xml()








