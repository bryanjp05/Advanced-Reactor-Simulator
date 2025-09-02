import openmc
import math
import numpy as np
    
def build_settings():

    # Point source near center of geometry (should be within or close to TRISO particles)
    r_compact = 0.6
    half_height = 2.5
    
    """

    lower = (-r_compact, -r_compact, -half_height)
    upper = ( r_compact,  r_compact,  half_height)

    src = openmc.IndependentSource(
        space=openmc.stats.Box(lower, upper, only_fissionable=True),
        angle=openmc.stats.Isotropic(),
        energy=openmc.stats.Watt(a=0.988e6, b=2.249e-6)
    )

    """
    z_bot_val = -2.5
    z_top_val =  2.5

    pitch = 2.3
    coolant_centers = [(0.0, 0.0)] + [
        ( pitch, 0.0),
        ( pitch/2,  pitch*np.sqrt(3)/2),
        (-pitch/2,  pitch*np.sqrt(3)/2),
        (-pitch, 0.0),
        (-pitch/2, -pitch*np.sqrt(3)/2),
        ( pitch/2, -pitch*np.sqrt(3)/2),
    ]

    sources = []
    for (cx, cy) in coolant_centers:
        box = openmc.stats.Box((cx-r_compact, cy-r_compact, z_bot_val+1e-4),
                               (cx+r_compact, cy+r_compact, z_top_val-1e-4),
                               only_fissionable=True)
        sources.append(openmc.IndependentSource(space=box))

    settings = openmc.Settings()
    settings.run_mode = 'eigenvalue'
    settings.batches = 30
    settings.inactive = 10
    settings.particles = 1000

    # Allow lots of rejections without aborting (since we still sample a box)
    settings.source_rejection_fraction = 1.0e-6
    settings.sources = sources

    settings.export_to_xml()
    
    settings.export_to_xml()

