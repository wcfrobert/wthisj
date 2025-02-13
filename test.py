import wthisj

# initialize a column perimeter
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "W",
                                      overhang_x = 12,
                                      overhang_y = 12,
                                      L_studrail = 24,
                                      auto_generate_perimeter = True)

# add openings
column1.add_opening(dx=0, dy=-80, width=36, height=24)
column1.add_opening(dx=80, dy=0, width=12, height=12)

# rotate geometry
#column1.rotate(-41.5)

# preview geometry
column1.preview()



# calculate punching shear stress
#results = column1.solve(P = 100, Mx = 0, My = 0, gamma_v = 0.4)

# # plot results
# column1.plot_results()







# column1.preview_3D()
#column1.plot_results_3D()



