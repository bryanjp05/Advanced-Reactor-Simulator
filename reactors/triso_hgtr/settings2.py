import openmc

def build_settings():
    settings = openmc.Settings()
    settings.batches = 100
    settings.inactive = 10
    settings.particles = 10000

    # Point source near center of geometry (should be within or close to TRISO particles)
    source = openmc.Source()
    source.space = openmc.stats.Box(
        lower_left=(-0.3, -0.3, -0.3),
        upper_right=(0.3, 0.3, 0.3),
        only_fissionable=True  # ensures points fall in fissionable regions
    )
    settings.source = source

    # Optional: loosen rejection fraction
    settings.source_rejection_fraction = 0.001

    settings.output = {'tallies': False}
    settings.run_mode = 'eigenvalue'
    settings.export_to_xml()
