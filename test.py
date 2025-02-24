import wthisj

# initialize a column perimeter
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "I",
                                      overhang_x = 12,
                                      overhang_y = 12,
                                      L_studrail = 0)

# add openings
# column1.add_opening(dx=0, dy=-80, width=36, height=24)
# column1.add_opening(dx=80, dy=0, width=12, height=12)

# preview geometry
#column1.preview()

# calculate punching shear stress
results = column1.solve(P = -120,
                        Mx = 0,
                        My = 400,
                        consider_Pe=False,
                        auto_rotate=True, 
                        verbose=True)

# plot results
#column1.plot_results()
column1.plot_results_3D()




