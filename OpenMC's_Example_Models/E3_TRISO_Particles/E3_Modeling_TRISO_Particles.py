#Packages
from math import pi
import numpy as np
import matplotlib.pyplot as plt
import openmc
import openmc.model

#Let's create the materials for our TRISO particles and background
fuel = openmc.Material(name='Fuel')
fuel.set_density('g/cm3', 10.5)
fuel.add_nuclide('U235', 4.6716e-02)
fuel.add_nuclide('U238', 2.8697e-01)
fuel.add_nuclide('O16',  5.0000e-01)
fuel.add_element('C', 1.6667e-01)

buff = openmc.Material(name='Buffer')
buff.set_density('g/cm3', 1.0)
buff.add_element('C', 1.0)
buff.add_s_alpha_beta('c_Graphite')

PyC1 = openmc.Material(name='PyC1')
PyC1.set_density('g/cm3', 1.9)
PyC1.add_element('C', 1.0)
PyC1.add_s_alpha_beta('c_Graphite')

PyC2 = openmc.Material(name='PyC2')
PyC2.set_density('g/cm3', 1.87)
PyC2.add_element('C', 1.0)
PyC2.add_s_alpha_beta('c_Graphite')

SiC = openmc.Material(name='SiC')
SiC.set_density('g/cm3', 3.2)
SiC.add_element('C', 0.5)
SiC.add_element('Si', 0.5)

graphite = openmc.Material()
graphite.set_density('g/cm3', 1.1995)
graphite.add_element('C', 1.0)
graphite.add_s_alpha_beta('c_Graphite')

# Create TRISO universe
spheres = [openmc.Sphere(r=1e-4*r)
    for r in [215., 315., 350., 385.]]
cells = [openmc.Cell(fill=fuel, region=-spheres[0]),
    openmc.Cell(fill=buff, region=+spheres[0] & -spheres[1]),
    openmc.Cell(fill=PyC1, region=+spheres[1] & -spheres[2]),
    openmc.Cell(fill=SiC, region=+spheres[2] & -spheres[3]),
    openmc.Cell(fill=PyC2, region=+spheres[3])]
triso_univ = openmc.Universe(cells=cells)

#region to pack the TRISO particles in. We will use a 1 cm x 1 cm x 1 cm box centered at the origin.
min_x = openmc.XPlane(x0=-0.5, boundary_type='reflective')
max_x = openmc.XPlane(x0=0.5, boundary_type='reflective')
min_y = openmc.YPlane(y0=-0.5, boundary_type='reflective')
max_y = openmc.YPlane(y0=0.5, boundary_type='reflective')
min_z = openmc.ZPlane(z0=-0.5, boundary_type='reflective')
max_z = openmc.ZPlane(z0=0.5, boundary_type='reflective')
region = +min_x & -max_x & +min_y & -max_y & +min_z & -max_z

#select locations for the TRISO particles using openmc.model.pack_spheres
outer_radius = 425.*1e-4
centers = openmc.model.pack_spheres(radius=outer_radius, region=region, pf=0.3, seed=124858351)

#Creating the TRISO particles:
trisos = [openmc.model.TRISO(outer_radius, triso_univ, center) for center in centers]

#print(trisos[0])

#Checking if the particles are in the box
centers = np.vstack([triso.center for triso in trisos])
#print(centers.min(axis=0))
#print(centers.max(axis=0))

#print(len(trisos)*4/3*pi*outer_radius**3)

#Placing particles in a lattice. 
box = openmc.Cell(region=region)
lower_left, upper_right = box.region.bounding_box
shape = (3, 3, 3)
pitch = (upper_right - lower_left)/shape
lattice = openmc.model.create_triso_lattice(
    trisos, lower_left, pitch, shape, graphite)

#Filling the lattice
box.fill = lattice

#Setting up reqirements to run the model:
universe = openmc.Universe(cells=[box])

geometry = openmc.Geometry(universe)
geometry.export_to_xml()

materials = list(geometry.get_all_materials().values())
openmc.Materials(materials).export_to_xml()

settings = openmc.Settings()
settings.run_mode = 'plot'
settings.export_to_xml()

plot = openmc.Plot.from_geometry(geometry)
plot.color_by = 'material'
plot.colors = {graphite: 'gray'}
plot.to_ipython_image()