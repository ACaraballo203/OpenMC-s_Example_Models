#Packages
from IPython.display import Image
import matplotlib.pyplot as plt
import openmc
import os

#Set up materials for our universes
fuel = openmc.Material(name='fuel')
fuel.add_nuclide('U235', 1.0)
fuel.set_density('g/cm3', 10.0)

fuel2 = openmc.Material(name='fuel2')
fuel2.add_nuclide('U238', 1.0)
fuel2.set_density('g/cm3', 10.0)

water = openmc.Material(name='water')
water.add_nuclide('H1', 2.0)
water.add_nuclide('O16', 1.0)
water.set_density('g/cm3', 1.0)

materials = openmc.Materials((fuel, fuel2, water))
materials.export_to_xml()

#Creating our pincells (and our universes):
r_pin = openmc.ZCylinder(r=0.25)
fuel_cell = openmc.Cell(fill=fuel, region=-r_pin)
water_cell = openmc.Cell(fill=water, region=+r_pin)
pin_universe = openmc.Universe(cells=(fuel_cell, water_cell))

r_big_pin = openmc.ZCylinder(r=0.5)
fuel2_cell = openmc.Cell(fill=fuel2, region=-r_big_pin)
water2_cell = openmc.Cell(fill=water, region=+r_big_pin)
big_pin_universe = openmc.Universe(cells=(fuel2_cell, water2_cell))

all_water_cell = openmc.Cell(fill=water)
outer_universe = openmc.Universe(cells=(all_water_cell,))

#Creating our lattice using the Hexlattice class:
lattice = openmc.HexLattice()

#lattice requirements
lattice.center = (0., 0.)
lattice.pitch = (1.25,)
lattice.outer = outer_universe

#Displaying our lattice for visuals
#print(lattice.show_indices(num_rings=4))

#Setting up our lattice, where the first element in each ring is the big pin universe 
# and all other elements are regular pin universes
outer_ring = [big_pin_universe] + [pin_universe]*17 # Adds up to 18

ring_1 = [big_pin_universe] + [pin_universe]*11 # Adds up to 12

ring_2 = [big_pin_universe] + [pin_universe]*5 # Adds up to 6

inner_ring = [big_pin_universe]

lattice.universes = [outer_ring, 
    ring_1, 
    ring_2,
    inner_ring]
#print(lattice)

#Setting our lattice in a circular cell
outer_surface = openmc.ZCylinder(r=5.0, boundary_type='vacuum')
main_cell = openmc.Cell(fill=lattice, region=-outer_surface)
geometry = openmc.Geometry([main_cell])

# Change the orientation of the lattice and re-export the geometry
#lattice.orientation = 'x'

geometry.export_to_xml()

#create a plot to see what our geometry looks like
plot = openmc.Plot.from_geometry(geometry)
plot.color_by = 'material'
plot.colors = colors = {
    water: 'blue',
    fuel: 'olive',
    fuel2: 'yellow'
}

main_cell.region = -openmc.model.HexagonalPrism(
    edge_length=4*lattice.pitch[0],
    orientation='x',
    boundary_type='vacuum'
)

# Run OpenMC in plotting mode
plot.color_by = 'cell'
plot.to_ipython_image()

# At this point, if we wanted to simulate the model, we would need to create an instance of openmc.
# Settings, export it to XML, and run.

