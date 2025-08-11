import openmc.model
import materials
import realistic_geometry
import settings2
import os
import glob

for file in ["materials.xml", "geometry.xml", "settings.xml", "tallies.xml", "plots.xml", "summary.h5"]:
    if os.path.exists(file):
        os.remove(file)

# Export XMLs from modular scripts
materials.build_materials()
realistic_geometry.build_geometry()
settings2.build_settings()

# Run OpenMC simulation
openmc.run()

# Find the latest statepoint
latest_sp = sorted(glob.glob('statepoint.*.h5'))[-1]
sp = openmc.StatePoint(latest_sp)


