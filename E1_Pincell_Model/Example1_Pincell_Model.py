#Packages
from IPython.display import Image
import matplotlib.pyplot as plt
import openmc
import os

##### 1. Materials ####
#Assigning and viewing Uranium dioxide.
uo2 = openmc.Material(1, "uo2")
#print(uo2)

#Pulling help from OpenMC's help class on adding a nuclide to UO2.
#help(uo2.add_nuclide)

# Add nuclides to uo2
uo2.add_nuclide('U235', 0.03)
uo2.add_nuclide('U238', 0.97)
uo2.add_nuclide('O16', 2.0)

#Setting the total density for UO2.
uo2.set_density('g/cm3', 10.0)

#print(uo2)

#Adding Zr, notice here we used element instead of defining a nuclide.
zirconium = openmc.Material(name="zirconium")
zirconium.add_element('Zr', 1.0)
zirconium.set_density('g/cm3', 6.6)

##Water settings
#Adding h20, material we just created will only use free-atom cross sections.
water = openmc.Material(name="h2o")
water.add_nuclide('H1', 2.0)
water.add_nuclide('O16', 1.0)
water.set_density('g/cm3', 1.0)

#Bound atom cross section is used at thermal energies. Note the use of the GND-style name "c_H_in_H2O".
water.add_s_alpha_beta('c_H_in_H2O')

# Let's now use the element class.
water.remove_nuclide('O16')
water.add_element('O', 1.0)

# Create a Materials collection and export to materials.xml
materials = openmc.Materials([uo2, zirconium, water])
materials.export_to_xml()

# Retrieve the file path from the environment variable.
file_path = os.getenv('OPENMC_CROSS_SECTIONS')

if file_path and os.path.exists(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Replicate: !cat $OPENMC_CROSS_SECTIONS | head -n 10
    #for line in lines[:10]:
        #print(line, end='')

    # Replicate: print('    ...')
    #print('    ...')

    # Replicate: !cat $OPENMC_CROSS_SECTIONS | tail -n 10
    #for line in lines[-10:]:
        #print(line, end='')
else:
    print("Error: OPENMC_CROSS_SECTIONS environment variable is not set or file path is invalid.")

##Enrichment
#Note that the add_element() method has a special argument enrichment that can be used for Uranium.
'''
uo2_three = openmc.Material()
uo2_three.add_element('U', 1.0, enrichment=3.0)
uo2_three.add_element('O', 2.0)
uo2_three.set_density('g/cc', 10.0)
'''

##Mixtures
''' 
# Create PuO2 material.
puo2 = openmc.Material()
puo2.add_nuclide('Pu239', 0.94)
puo2.add_nuclide('Pu240', 0.06)
puo2.add_nuclide('O16', 2.0)
puo2.set_density('g/cm3', 11.5)

# Create the mixture.
mox = openmc.Material.mix_materials([uo2, puo2], [0.97, 0.03], 'wo')
'''
'''
The 'wo' argument in the mix_materials() method specifies that the fractions are weight fractions. 
Materials can also be mixed by atomic and volume fractions with 'ao' and 'vo', respectively. 
For 'ao' and 'wo' the fractions must sum to one. For 'vo', 
if fractions do not sum to one, the remaining fraction is set as void.
'''

#### 2. Geometry ####

#Creating a sphere (centered at the origin).
sphere = openmc.Sphere(r=1.0)

inside_sphere = -sphere
outside_sphere = +sphere

#print((0,0,0) in inside_sphere, (0,0,2) in inside_sphere)
#print((0,0,0) in outside_sphere, (0,0,2) in outside_sphere)
#Expect True False; False True.

#let's say we want to define a region that is the top part of the sphere (all points inside the sphere that have  z>0.
z_plane = openmc.ZPlane(0)
northern_hemisphere = -sphere & +z_plane
#print(northern_hemisphere.bounding_box)

#Creating volume using cells.
cell = openmc.Cell()
cell.region = northern_hemisphere

# or...
#cell = openmc.Cell(region=northern_hemisphere)

cell.fill = water

#A collection of cells is called a universe.
universe = openmc.Universe()
universe.add_cell(cell)

# this also works.
#universe = openmc.Universe(cells=[cell])

#Plotting the universe (saved as a pdf)
universe.plot(width=(2.0, 2.0), basis='xz', colors={cell: 'fuchsia'})
plt.savefig("north_hemi_water.png")
plt.show()

##Pincell Geometry
#Each is a cylinder where it is parallel to the z-axis.
fuel_outer_radius = openmc.ZCylinder(r=0.39)
clad_inner_radius = openmc.ZCylinder(r=0.40)
clad_outer_radius = openmc.ZCylinder(r=0.46)

#Creating the regions.
fuel_region = -fuel_outer_radius
gap_region = +fuel_outer_radius & -clad_inner_radius
clad_region = +clad_inner_radius & -clad_outer_radius

#create corresponding cells that assign materials to these regions.
fuel = openmc.Cell(name='fuel')
fuel.fill = uo2
fuel.region = fuel_region

gap = openmc.Cell(name='air gap')
gap.region = gap_region

clad = openmc.Cell(name='clad')
clad.fill = zirconium
clad.region = clad_region

#To handle the coolant outside our fuel pin, we do the following:
pitch = 1.26
left = openmc.XPlane(-pitch/2, boundary_type='reflective')
right = openmc.XPlane(pitch/2, boundary_type='reflective')
bottom = openmc.YPlane(-pitch/2, boundary_type='reflective')
top = openmc.YPlane(pitch/2, boundary_type='reflective')

#water region is going to be everything outside of the clad outer radius 
# and within the box formed as the intersection of four half-spaces.
water_region = +left & -right & +bottom & -top & +clad_outer_radius

moderator = openmc.Cell(name='moderator')
moderator.fill = water
moderator.region = water_region

#box = openmc.model.RectangularPrism(width=pitch, height=pitch,
    #boundary_type='reflective')
#print(type(box))

#water_region = -box & +clad_outer_radius

#Assigning Cells to the universe and establishing the "root" universe in the geometry.
root_universe = openmc.Universe(cells=(fuel, gap, clad, moderator))

#geometry = openmc.Geometry(root_universe)

# or...
geometry = openmc.Geometry()
geometry.root_universe = root_universe

geometry.export_to_xml()

#Creating plot instances:
plot = openmc.Plot()
plot.filename = 'pinplot'
plot.width = (pitch, pitch)
plot.pixels = (200, 200)
plot.color_by = 'material'
plot.colors = {uo2: 'yellow', water: 'blue'}

#Exporting the plots to xml
plots = openmc.Plots([plot])
plots.export_to_xml()

openmc.plot_geometry()

plot.to_ipython_image()

#### 3. Source/ Settings ####

# Create a point source
point = openmc.stats.Point((0, 0, 0))
source = openmc.IndependentSource(space=point)

#Setting up our setttings:
settings = openmc.Settings()
settings.source = source
settings.batches = 100
settings.inactive = 10
settings.particles = 1000

settings.export_to_xml()

##User-defined tallies
#cell filter specifying the fuel cell.
cell_filter = openmc.CellFilter(fuel)

#Tally where?
tally = openmc.Tally(1)
tally.filters = [cell_filter]

#Tally what?
tally.nuclides = ['U235']
tally.scores = ['total', 'fission', 'absorption', '(n,gamma)']

#Exporting tallies xml file.
tallies = openmc.Tallies([tally])
tallies.export_to_xml()

#openmc.run()



