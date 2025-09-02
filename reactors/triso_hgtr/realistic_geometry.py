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

def in_hex_xy(x, y, flat_to_flat):
    # works for HexagonalPrism(orientation='y')
    a = flat_to_flat/2.0
    return (abs(x) + np.sqrt(3.0)*abs(y)) <= a + 1e-8  # small tol

def in_any_channel(x, y, centers, r):
    for (cx, cy) in centers:
        if (x-cx)**2 + (y-cy)**2 < (r - 1e-6)**2:  # small tol
            return True
    return False

def build_geometry():
    # Load materials
    fuel, buffer, inner_pyc, sic, outer_pyc, matrix, reflector, helium = build_materials()
    layers = [fuel, buffer, inner_pyc, sic, outer_pyc]
    triso_radius = 0.05  # outer radius
    # Define radii for each layer boundary (starting from kernel)
    radii = [0.025, 0.03, 0.035, 0.045, 0.05]  # Adjust these as needed
    triso_universe = make_triso_universe(layers, radii)

    # Hexagonal graphite block
    flat_to_flat = 6.0
    edge_len = flat_to_flat / np.sqrt(3.0)
    half_height = 2.5
    refl_margin = 30.0
    
    # internal planes 
    z_bot_core = openmc.ZPlane(z0=-half_height)
    z_top_core = openmc.ZPlane(z0=+half_height)

    # real vacuum planes pushed away
    t_top = 30.0   # cm graphite above core
    t_bot = 30.0   # cm graphite below core
    z_bot_vac = openmc.ZPlane(z0=-half_height - t_bot, boundary_type='vacuum')
    z_top_vac = openmc.ZPlane(z0=+half_height + t_top,  boundary_type='vacuum')
    hex_refl = HexagonalPrism(edge_length=edge_len + refl_margin, orientation='y', boundary_type='vacuum')
 
    hex_block = HexagonalPrism(edge_length=edge_len, orientation='y')
    
    block_region = -hex_block & +z_bot_core & -z_top_core

    top_refl_region    = -hex_block & +z_top_core & -z_top_vac
    bottom_refl_region = -hex_block & +z_bot_vac & -z_bot_core
    radial_refl_region = (-hex_refl & +z_bot_vac & -z_top_vac) & ~(block_region)
    
    top_refl_cell    = openmc.Cell(region=top_refl_region,    fill=reflector) 
    bottom_refl_cell = openmc.Cell(region=bottom_refl_region, fill=reflector)
    radial_refl_cell = openmc.Cell(region=radial_refl_region, fill=reflector)    

    # Fuel compact dimensions
    r_compact = 0.6
    cyl_compact = openmc.ZCylinder(r=r_compact)
    compact_pack_region = -cyl_compact & block_region

    # --- Lattice bounding box (must match lattice lower_left and pitch) ---
    x_min, x_max = -r_compact,  r_compact
    y_min, y_max = -r_compact,  r_compact
    fuel_box_region = (+openmc.XPlane(x0=x_min) & -openmc.XPlane(x0=x_max) &
                       +openmc.YPlane(y0=y_min) & -openmc.YPlane(y0=y_max) &
                       +z_bot_core & -z_top_core)

    # Keep the box inside the hex block:
    fuel_box_region &= block_region

    # Coolant channels
    ch_r = 0.3
    pitch = 2.3
    h_bot, h_top = -half_height, +half_height
    coolant_centers = [(0.0, 0.0)] + [
        ( pitch, 0.0),
        ( pitch/2,  pitch*np.sqrt(3)/2),
        (-pitch/2,  pitch*np.sqrt(3)/2),
        (-pitch, 0.0),
        (-pitch/2, -pitch*np.sqrt(3)/2),
        ( pitch/2, -pitch*np.sqrt(3)/2),
    ]
    coolant_cyls = [openmc.ZCylinder(x0=x, y0=y, r=ch_r) for (x, y) in coolant_centers]

    # Coolant cells
    eps = 1e-7
    coolant_cells = []
    for c in coolant_cyls:
        ch = openmc.ZCylinder(x0=c.x0, y0=c.y0, r=ch_r-eps)
        ch_region = -c & block_region
        coolant_cells.append(openmc.Cell(fill=helium, region=ch_region))
    """
    # make a Region for each compact and pack spheres there
    all_trisos = []
    for (cx, cy) in coolant_centers:
        cyl = openmc.ZCylinder(x0=cx, y0=cy, r=r_compact)
        pack_region = -cyl & +z_bot_core & -z_top_core
        
        # keep compacts from overlapping coolant holes
        # for ch in coolant_cyls:
            # comp_region &= +ch   # exclude channel voids
        
        # pack TRISOs in THIS compact
        n_this = 4000   # or compute per-compact from your PF target
        raw_centers = pack_spheres(radius=triso_radius, region=pack_region,
                                   num_spheres=n_this, seed=42)
        # filter: stay in hex and out of channels        
        centers = []
        for x, y, z in raw_centers:
            if not in_hex_xy(x, y, flat_to_flat):
                continue
            if in_any_channel(x, y, coolant_centers, ch_r):
                continue
            centers.append((x, y, z))
        
        # build TRISO objects at these centers
        for ctr in centers:
            all_trisos.append(TRISO(triso_radius, triso_universe, ctr))
    """

    # --- Fuel compacts: cylinders placed BETWEEN coolant channels ---
    n_triso_per_compact = 350           # adjust to hit your PF target
    min_edge_clear = r_compact + 0.05   # keep compacts off the hex edge
    min_ch_clear  = ch_r + r_compact + 0.05  # keep compacts out of channels

    # Build a small hexagonal grid of *candidate* compact centers,
    # then keep only those that are inside the block and clear of channels.
    compact_centers = []
    # grid extent slightly smaller than the block
    grid_span = (flat_to_flat*0.5 - min_edge_clear)
    dy = pitch*np.sqrt(3)/2
    y_vals = np.arange(-grid_span, grid_span+1e-9, dy)
    for i, y in enumerate(y_vals):
        # stagger every other row (hex grid)
        x_offset = 0.0 if (i % 2 == 0) else pitch*0.5
        x_vals = np.arange(-grid_span + x_offset, grid_span + x_offset + 1e-9, pitch)
        for x in x_vals:
            if not in_hex_xy(x, y, flat_to_flat): 
                continue
            if in_any_channel(x, y, coolant_centers, min_ch_clear):
                continue
            compact_centers.append((x, y))

    # --- Pack TRISOs *inside each compact* ---
    all_trisos = []
    for (cx, cy) in compact_centers:
        # compact cylinder (full block height)
        comp_cyl = openmc.ZCylinder(x0=cx, y0=cy, r=r_compact)
        comp_region = (-comp_cyl) & (-z_top_core) & (+z_bot_core) 

        # pack N TRISOs in THIS compact region
        raw_centers = pack_spheres(
            radius=triso_radius,
            region=comp_region,
            num_spheres=n_triso_per_compact,
            seed=42
        )

        # (optional) keep away from nearby coolant cylinders by small buffer
        keep = []
        for (x, y, z) in raw_centers:
            if in_any_channel(x, y, coolant_centers, ch_r + 0.02):
                continue
            keep.append((x, y, z))

        for ctr in keep:
            all_trisos.append(TRISO(triso_radius, triso_universe, ctr))


    # one lattice for all particles
    bbox_ll = (-flat_to_flat, -flat_to_flat, h_bot)   # just needs to enclose all compacts
    bbox_pitch = (2*flat_to_flat, 2*flat_to_flat, h_top - h_bot)
    triso_lat = create_triso_lattice(all_trisos, bbox_ll, bbox_pitch, (1,1,1), matrix)

    # fuel matrix region is the UNION of the compacts (no coolant)
    fuel_matrix_region = None
    for (cx, cy) in coolant_centers:
        cyl = openmc.ZCylinder(x0=cx, y0=cy, r=r_compact)
        reg = -cyl & +z_bot_core & -z_top_core & -hex_block
        for ch in coolant_cyls:
            reg &= +ch
        fuel_matrix_region = reg if fuel_matrix_region is None else (fuel_matrix_region | reg)

    fuel_cell = openmc.Cell(region=fuel_matrix_region, fill=triso_lat)

    """

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

    compact_pack_region = -cyl_compact & +z_bot_core & -z_top_core

    # Pack triso into compact region
    est_n = 2500
    centers = pack_spheres(radius=triso_radius, region=compact_pack_region, num_spheres=est_n, seed=42)

    # Filter out any centers that fall inside a coolant cylinder
    def in_channel(x, y):
        for (cx, cy) in coolant_centers:
            if (x-cx)**2 + (y-cy)**2 < ch_r**2:
                return True
        return False

    def in_hex_xy(x, y):
        a = flat_to_flat/2.0
        return (abs(x) + np.sqrt(3.0)*abs(y)) <= a

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

    """

    # --- Union of all compact cylinders (solids) ---
    compacts_union = None
    for (cx, cy) in coolant_centers:
        cyl = openmc.ZCylinder(x0=cx, y0=cy, r=r_compact)
        reg = (-cyl) & +z_bot_core & -z_top_core
        compacts_union = reg if compacts_union is None else (compacts_union | reg)

    # --- Union of all coolant channels (void He) ---
    channels_union = None
    for c in coolant_cyls:
        ch_reg = (-c) & +z_bot_core & -z_top_core & (-hex_block)
        channels_union = ch_reg if channels_union is None else (channels_union | ch_reg)

    # Graphite *block outside compact bore* (i.e., rest of hex block volume not compact nor channels)
    block_graphite_region = block_region & ~compacts_union & ~channels_union
    #for c in coolant_cyls:
    #    block_graphite_region &= +c
    block_graphite_cell = openmc.Cell(region=block_graphite_region, fill=matrix)

    # Outer graphite reflector: hex shell around block
    refl_margin = 2.0
    a_block = flat_to_flat/2.0
    s_block = edge_len
    a_ref   = a_block + refl_margin 
    s_ref   = a_ref / np.cos(np.pi/6)   # edge length for the bigger hex
    hex_refl = HexagonalPrism(edge_length=s_ref, orientation='y', boundary_type='reflective')
    reflector_region = (-hex_refl & +z_bot_core & -z_top_core) & ~block_region
    reflector_cell = openmc.Cell(region=reflector_region, fill=reflector)
    
    # Big outer vacuum boundary
    S_out = openmc.Sphere(r=100.0, boundary_type='vacuum')  # big enough to enclose all

    channels_union = None
    for c in coolant_cyls:
        this_ch = (-c) & (+z_bot_core) & (-z_top_core) & block_region
        channels_union = this_ch if channels_union is None else (channels_union | this_ch)
        #channels_union = (-c if channels_union is None else channels_union | -c)
    #channels_union = (channels_union & block_region)  # channels through the block

    # The “occupied” region by your real cells:
    occupied = (fuel_matrix_region | block_graphite_region | reflector_region | channels_union)
  
    # Catch-all cell: anything inside S_out that isn’t occupied
    outside_region = (-S_out) & ~occupied
    outside_cell   = openmc.Cell(region=outside_region)

    # Root universe
    #root_universe = openmc.Universe(cells=[fuel_cell, block_graphite_cell, reflector_cell, *coolant_cells, outside_cell])
    root_universe = openmc.Universe(cells=[fuel_cell, block_graphite_cell, top_refl_cell, bottom_refl_cell, radial_refl_cell, 
                                           *coolant_cells, outside_cell])
    
    # Geometry
    geom = openmc.Geometry(root_universe)
    geom.export_to_xml()
