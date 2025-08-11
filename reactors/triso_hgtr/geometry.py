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
    fuel, buffer, inner_pyc, sic, outer_pyc, matrix, reflector, helium = build_materials()
    layers = [fuel, buffer, inner_pyc, sic, outer_pyc]
    triso_radius = 0.05  # outer radius
    # Define radii for each layer boundary (starting from kernel)
    radii = [0.025, 0.03, 0.035, 0.045, 0.05]  # Adjust these as needed
    triso_universe = make_triso_universe(layers, radii)

    # Define the region using planes
    r_compact = 0.5
    h_compact = 1.0
    left     = openmc.XPlane(x0=-r_compact, boundary_type='reflective')
    right    = openmc.XPlane(x0=+r_compact, boundary_type='reflective')
    bottom   = openmc.YPlane(y0=-r_compact, boundary_type='reflective')
    top      = openmc.YPlane(y0=+r_compact, boundary_type='reflective')
    bottom_z = openmc.ZPlane(z0=-r_compact, boundary_type='reflective')
    top_z    = openmc.ZPlane(z0=+r_compact, boundary_type='reflective')

    # Combine them into a Region object
    fuel_region = +left & -right & +bottom & -top & +bottom_z & -top_z

    # Define region for reflector
    outer = 1.0
    outer_left   = openmc.XPlane(x0=-outer, boundary_type='reflective') 
    outer_right  = openmc.XPlane(x0= outer, boundary_type='reflective')
    outer_bottom = openmc.YPlane(y0=-outer, boundary_type='reflective')
    outer_top    = openmc.YPlane(y0= outer, boundary_type='reflective')
    outer_bottom_z = openmc.ZPlane(z0=-outer, boundary_type='vacuum')
    outer_top_z    = openmc.ZPlane(z0= outer, boundary_type='vacuum')

    reflector_region = +outer_left & -outer_right & +outer_bottom & -outer_top & +outer_bottom_z & -outer_top_z & ~fuel_region
    
    # Define coolant region as the space between fuel and outer cube
    coolant_region = +outer_left & -outer_right & +outer_bottom & -outer_top \
                     & +outer_bottom_z & -outer_top_z & ~fuel_region

    # Create TRISO templates
    trisos = []
    num_trisos = 500

    # Pack spheres
    centers = pack_spheres(
        radius=triso_radius,
        region=fuel_region,
        num_spheres=num_trisos
    )

    for center in centers:
        triso = TRISO(triso_radius, triso_universe, center)
        trisos.append(triso)

    # Create lattice
    lower_left = (-r_compact, -r_compact, -r_compact)
    shape = (1, 1, 1)
    pitch = (2 * r_compact, 2 * r_compact, 2 * r_compact)
    lattice = create_triso_lattice(trisos, lower_left, pitch, shape, matrix)

    # Wrap the lattice in a cell
    fuel_cell = openmc.Cell(region=fuel_region, fill=lattice)
    reflector_cell = openmc.Cell(region=reflector_region, fill=reflector)
    coolant_cell = openmc.Cell(region=coolant_region, fill=helium)
    root_universe = openmc.Universe(cells=[fuel_cell, reflector_cell, coolant_cell])

    geometry = openmc.Geometry(root_universe)
    geometry.export_to_xml()

