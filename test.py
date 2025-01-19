import wthisj


# initialize a punching shear perimeter
column1 = wthisj.PunchingShearSection()

# define critical perimeter 
column1.add_support(b, h, d)
column1.add_perimeter()
column1.add_perimeter()
column1.add_perimeter()
column1.add_perimeter()



# add openings
column1.add_opening(dx=60, dy=60, width=36, height=12)

# preview geometry
column1.preview()
column1.preview_3D()

# calculate punching shear stress
results = column1.solve(P=100, Mx=0, My=0)

# plot results
column1.plot_results()
column1.plot_results_3D()