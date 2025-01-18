import ezweld

# initialize a weld group
weld_group = ezweld.WeldGroup()

# draw welds
weld_group.add_line(start=(0,0), end=(0,10), thickness=5/16)
weld_group.add_line(start=(5,0), end=(5,10), thickness=5/16)

# preview geometry
weld_group.preview()

# calculate weld stress (k/in) with elastic method
results = weld_group.solve(Vx=0, Vy=-50, Vz=0, Mx=200, My=0, Mz=0)

# plot results
weld_group.plot_results()

# plot results in 3D
weld_group.plot_results_3D()