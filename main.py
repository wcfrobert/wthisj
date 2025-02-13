import wthisj

# initialize a column perimeter
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "I",
                                      overhang_x=4)
# preview geometry
column1.preview()

# calculate punching shear stress
results = column1.solve(P = 100, 
                        Mx = 500, 
                        My = 90, 
                        gamma_v = 0.4)








# # plot results
# column1.plot_results()

# column1.preview_3D()
column1.plot_results_3D()



