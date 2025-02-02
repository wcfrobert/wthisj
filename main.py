import wthisj

# initialize a column perimeter
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "I")

# # add openings
column1.add_opening(dx=0, dy=-60, width=24, height=12)

# # preview geometry
column1.preview()

# # calculate punching shear stress
# results = column1.solve(P = 100, Mx = 0, My = 0, gamma_v = 0.4)

# # plot results
# column1.plot_results()




# column1.preview_3D()
# column1.plot_results_3D()



