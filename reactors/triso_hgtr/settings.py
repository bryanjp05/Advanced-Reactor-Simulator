import openmc
import numpy as np
import math

def build_settings():

    settings = openmc.Settings()
    settings.batches = 100
    settings.inactive = 10
    settings.particles = 1000
    settings.run_mode = 'eigenvalue'

    # Define a source near the TRISO kernel center (assume TRISO at origin)
    source = openmc.IndependentSource()
    source.space = openmc.stats.Point((0.0, 0.0, 0.0))
    settings.source = source

    # Optional: relax the constraint if needed
    settings.source_rejection_fraction = 1e-4

    settings.export_to_xml()
