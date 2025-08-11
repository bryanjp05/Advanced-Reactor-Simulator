import openmc
import math
    
def build_settings():

    # Point source near center of geometry (should be within or close to TRISO particles)
    r_compact = 2.0
    half_height = 10.0

    r_in = r_compact/math.sqrt(2.0)
    lower_left  = (-r_in*0.95, -r_in*0.95, -half_height*0.95)
    upper_right = ( r_in*0.95,  r_in*0.95,  half_height*0.95)

    src = openmc.IndependentSource(
        space=openmc.stats.Box(lower_left, upper_right, only_fissionable=True),
        angle=openmc.stats.Isotropic(),
        energy=openmc.stats.Watt(a=0.988, b=2.249)
    ) 

    settings = openmc.Settings()
    settings.run_mode = 'eigenvalue'
    settings.batches = 30
    settings.inactive = 10
    settings.particles = 2000

    # Allow lots of rejections without aborting (since we still sample a box)
    settings.source_rejection_fraction = 1.0e-6
    settings.sources = [src]

    # Optional: speed up lost-particle diagnostics
    settings.max_lost_particles = 1_000_000

    settings.export_to_xml()
    
    settings.export_to_xml()

