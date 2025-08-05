import openmc
import numpy as np
from openmc.model import TRISO, pack_spheres, create_triso_lattice
from materials import build_materials

def make_triso_universe(layers, radii):
    # Create spherical surfaces
    surfaces = [openmc.Sphere(r=r) for r in radii]
    surfaces[-1].boundary_type = 'transmission'

    cells = []
    for i, mat in enumerate(layers):
        if i == 0:
            region = -surfaces[0]
        else:
            region = +surfaces[i-1] & -surfaces[i]
        cell = openmc.Cell(fill=mat, region=region)
        cells.append(cell)

    # Make the universe from these cells
    return openmc.Universe(cells=cells)

def build_geometry():
    # Load materials
    fuel, buffer, inner_pyc, sic, outer_pyc, matrix = build_materials()
    layers = [fuel, buffer, inner_pyc, sic, outer_pyc]
    triso_radius = 0.05  # outer radius
    # Define radii for each layer boundary (starting from kernel)
    radii = [0.025, 0.03, 0.035, 0.045, 0.05]  # Adjust these as needed
    triso_universe = make_triso_universe(layers, radii)

    # Define the region using planes
    left     = openmc.XPlane(x0=-0.6, boundary_type='reflective')
    right    = openmc.XPlane(x0=0.6,  boundary_type='reflective')
    bottom   = openmc.YPlane(y0=-0.6, boundary_type='reflective')
    top      = openmc.YPlane(y0=0.6,  boundary_type='reflective')
    bottom_z = openmc.ZPlane(z0=-0.6, boundary_type='reflective')
    top_z    = openmc.ZPlane(z0=0.6,  boundary_type='reflective')

    # Combine them into a Region object
    region = +left & -right & +bottom & -top & +bottom_z & -top_z

    # Create TRISO templates
    trisos = []
    num_trisos = 323

    # Pack spheres
    centers = pack_spheres(
        radius=triso_radius,
        region=region,
        num_spheres=num_trisos
    )

    for center in centers:
        triso = TRISO(triso_radius, triso_universe, center)
        trisos.append(triso)

    # Create lattice
    r_compact = 0.6
    h_compact = 1.0
    lower_left = (-r_compact, -r_compact, -r_compact)
    shape = (1, 1, 1)
    pitch = (2 * r_compact, 2 * r_compact, 2 * r_compact)
    lattice = create_triso_lattice(trisos, lower_left, pitch, shape, matrix)

    # Wrap the lattice in a cell
    outer_sphere = openmc.Sphere(r=2.0, boundary_type='vacuum')
    cell = openmc.Cell(region=-outer_sphere, fill=lattice)
    root_universe = openmc.Universe(cells=[cell])

    geometry = openmc.Geometry(root_universe)
    geometry.export_to_xml()

