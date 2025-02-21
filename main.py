import wthisj

# initialize a column perimeter
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "W",
                                      overhang_x = 12,
                                      overhang_y = 0,
                                      L_studrail = 36)

# add openings
column1.add_opening(dx=10, dy=-100, width=48, height=36)
column1.add_opening(dx=80, dy=0, width=12, height=12)

# preview geometry
column1.preview()

# calculate punching shear stress
results = column1.solve(P = 100,
                        Mx = -400,
                        My = -400,
                        consider_Pe=False,
                        auto_rotate=False, 
                        verbose=True)

# plot results
column1.plot_results()
column1.plot_results_3D()
