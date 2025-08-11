import openmc
import numpy as np
from openmc.model import TRISO, pack_spheres, create_triso_lattice, HexagonalPrism
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

    # Hexagonal graphite block
    flat_to_flat = 12.0
    edge_len = flat_to_flat / np.sqrt(3.0)
    half_height = 10.0
    
    hex_block = HexagonalPrism(edge_length=edge_len, orientation='y')
    z_bot = openmc.ZPlane(z0=-half_height, boundary_type='reflective')
    z_top = openmc.ZPlane(z0=+half_height, boundary_type='reflective')
    block_region = -hex_block & +z_bot & -z_top

    # Fuel compact dimensions
    r_compact = 2.0
    cyl_compact = openmc.ZCylinder(r=r_compact)
    compact_pack_region = -cyl_compact & block_region

    # --- Lattice bounding box (must match lattice lower_left and pitch) ---
    x_min, x_max = -r_compact,  r_compact
    y_min, y_max = -r_compact,  r_compact
    fuel_box_region = (+openmc.XPlane(x0=x_min) & -openmc.XPlane(x0=x_max) &
                       +openmc.YPlane(y0=y_min) & -openmc.YPlane(y0=y_max) &
                       +z_bot & -z_top)

    # Keep the box inside the hex block:
    fuel_box_region &= block_region

    # Coolant channels
    ch_r = 0.5
    pitch = 3.0
    coolant_centers = [(0.0, 0.0)] + [
        ( pitch, 0.0),
        ( pitch/2,  pitch*np.sqrt(3)/2),
        (-pitch/2,  pitch*np.sqrt(3)/2),
        (-pitch, 0.0),
        (-pitch/2, -pitch*np.sqrt(3)/2),
        ( pitch/2, -pitch*np.sqrt(3)/2),
    ]
    coolant_cyls = [openmc.ZCylinder(x0=x, y0=y, r=ch_r) for (x, y) in coolant_centers]

    # Fuel matrix region (compact region minus the channels 
    eps = 1e-7
    fuel_matrix_region = fuel_box_region
    for c in coolant_cyls:
        fuel_matrix_region &= +c

    # Coolant cells
    coolant_cells = []
    for c in coolant_cyls:
        ch = openmc.ZCylinder(x0=c.x0, y0=c.y0, r=ch_r-eps)
        ch_region = -c & block_region   
        coolant_cells.append(openmc.Cell(fill=helium, region=ch_region))

    compact_pack_region = -cyl_compact & +z_bot & -z_top

    # Pack triso into compact region
    est_n = 5000
    centers = pack_spheres(radius=triso_radius, region=compact_pack_region, num_spheres=est_n, seed=42)

    # Filter out any centers that fall inside a coolant cylinder
    def in_channel(x, y):
        for (cx, cy) in coolant_centers:
            if (x-cx)**2 + (y-cy)**2 < ch_r**2:
                return True
        return False

    def in_hex_xy(x, y):
        a = flat_to_flat /2.0
        return (abs(x) + np.sqrt(3.0)*abs(y)) <= a

    """
    filtered = [ctr for ctr in centers_triso if in_hex_xy(ctr[0], ctr[1]) and not in_channel(ctr[0], ctr[1])]
    if len(filtered) < len(centers_triso):
        print(f"Filtered {len(centers_triso)-len(filtered)} TRISOs that landed in coolant holes.")
    centers_triso = np.array(filtered)
    """

    centers_triso = np.array([c for c in centers
                          if in_hex_xy(c[0], c[1]) and not in_channel(c[0], c[1])])

    # Build TRISOs at those centers (as TRISO objects using the TRISO-universe fill)
    trisos = [TRISO(triso_radius, triso_universe, ctr) for ctr in centers_triso]

    # Lattice bounding box for the compact (one element lattice that delegates tracking to TRISO)
    lower_left = (-r_compact, -r_compact, -half_height)
    pitch = (2*r_compact, 2*r_compact, 2*half_height)
    shape = (1, 1, 1)
    lattice = create_triso_lattice(trisos, lower_left, pitch, shape, matrix)

    # ---- Cells / Universes ----
    # Fuel matrix (graphite + TRISOs)
    fuel_cell = openmc.Cell(region=fuel_matrix_region, fill=lattice)

    # Graphite *block outside compact bore* (i.e., rest of hex block volume not compact nor channels)
    block_graphite_region = block_region & ~fuel_box_region
    for c in coolant_cyls:
        block_graphite_region &= +c
    block_graphite_cell = openmc.Cell(region=block_graphite_region, fill=matrix)

    # Outer graphite reflector: hex shell around block
    refl_margin = 2.0
    a_block = flat_to_flat/2.0
    s_block = edge_len
    a_ref   = a_block + refl_margin 
    s_ref   = a_ref / np.cos(np.pi/6)   # edge length for the bigger hex
    hex_refl = HexagonalPrism(edge_length=s_ref, orientation='y')
    reflector_region = (-hex_refl & +z_bot & -z_top) & ~block_region
    reflector_cell = openmc.Cell(region=reflector_region, fill=reflector)
    
    # Big outer vacuum boundary
    S_out = openmc.Sphere(r=100.0, boundary_type='vacuum')  # big enough to enclose all

    channels_union = None
    for c in coolant_cyls:
        channels_union = (-c if channels_union is None else channels_union | -c)
    channels_union = (channels_union & block_region)  # channels through the block

    # The “occupied” region by your real cells:
    occupied = (fuel_matrix_region | block_graphite_region | reflector_region | channels_union)
  
    # Catch-all cell: anything inside S_out that isn’t occupied
    outside_region = (-S_out) & ~occupied
    outside_cell   = openmc.Cell(region=outside_region)

    # Root universe
    root_universe = openmc.Universe(cells=[fuel_cell, block_graphite_cell,  reflector_cell, *coolant_cells, outside_cell])

    # Geometry
    world = openmc.Sphere(r=100.0, boundary_type='vacuum')
    world_cell = openmc.Cell(region=-world, fill=root_universe)
    top = openmc.Universe(cells=[world_cell])
    geom = openmc.Geometry(root_universe)
    geom.export_to_xml()
