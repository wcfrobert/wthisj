import wthisj

# initialize a column perimeter
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "W",
                                      overhang_x = 12,
                                      overhang_y = 12,
                                      L_studrail = 0,
                                      auto_generate_perimeter = True)

# add openings
#column1.add_opening(dx=0, dy=-80, width=36, height=24)
# column1.add_opening(dx=80, dy=0, width=12, height=12)

# rotate geometry
#column1.rotate(45)

# preview geometry
column1.preview()

# calculate punching shear stress
results = column1.solve(P = 120, Mx = 0, My = -900, consider_Pe=False, auto_rotate=False, verbose=True)

# plot results
column1.plot_results_3D()







# column1.preview_3D()
#column1.plot_results_3D()



