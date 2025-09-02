import openmc

def build_materials():
    # UCO kernel
    fuel = openmc.Material(name='UCO')
    fuel.add_nuclide('U235', 0.1)
    fuel.add_nuclide('U238', 0.9)
    fuel.add_nuclide('C12', 0.9893 * 1.5)
    fuel.add_nuclide('C13', 0.0107 * 1.5)
    fuel.add_nuclide('O16', 1)
    fuel.set_density('g/cm3', 11.0)
    print(fuel.get_nuclide_atom_densities())

    # Buffer
    buffer = openmc.Material(name='Buffer PyC')
    buffer.add_nuclide('C12', 0.9893)
    buffer.add_nuclide('C13', 0.0107)
    buffer.set_density('g/cm3', 1.0)

    # Inner PyC
    inner_pyc = openmc.Material(name='Inner PyC')
    inner_pyc.add_nuclide('C12', 0.9893)
    inner_pyc.add_nuclide('C13', 0.0107)
    inner_pyc.set_density('g/cm3', 1.9)

    # SiC
    sic = openmc.Material(name='SiC')
    sic.add_nuclide('Si28', 0.9223)
    sic.add_nuclide('Si29', 0.0467)
    sic.add_nuclide('Si30', 0.0310)
    sic.add_nuclide('C12', 0.9893)
    sic.add_nuclide('C13', 0.0107)
    sic.set_density('g/cm3', 3.2)

    # Outer PyC
    outer_pyc = openmc.Material(name='Outer PyC')
    outer_pyc.add_nuclide('C12', 0.9893)
    outer_pyc.add_nuclide('C13', 0.0107)
    outer_pyc.set_density('g/cm3', 1.9)

    # Matrix
    matrix = openmc.Material(name='Graphite Matrix')
    matrix.add_nuclide('C12', 0.9893)
    matrix.add_nuclide('C13', 0.0107)
    matrix.set_density('g/cm3', 1.6)

    # Reflector
    reflector = openmc.Material(name='Graphite Reactor')
    reflector.add_nuclide('C12', 0.9893)
    reflector.add_nuclide('C13', 0.0107)
    reflector.set_density('g/cm3', 1.8)

    #Coolant
    helium = openmc.Material(name='Helium')
    helium.add_nuclide('He4', 1.0)
    helium.set_density('g/cm3', 0.0001786)
    helium.temperature = 900.0

    materials = openmc.Materials([fuel, buffer, inner_pyc, sic, outer_pyc, matrix, reflector, helium])
    materials.export_to_xml()
    
    return fuel, buffer, inner_pyc, sic, outer_pyc, matrix, reflector, helium
 
