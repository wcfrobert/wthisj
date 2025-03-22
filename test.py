import wthisj

# initialize a column perimeter
column1 = wthisj.PunchingShearSection(col_width = 24,
                                      col_depth = 24,
                                      slab_avg_depth = 12,
                                      condition = "W",
                                      overhang_x = 12,
                                      overhang_y = 0,
                                      studrail_length = 36)


# preview geometry
column1.preview()

# calculate punching shear stress
results = column1.solve(Vz = -100,
                        Mx = 0,
                        My = 0,
                        consider_ecc=True,
                        auto_rotate=False, 
                        verbose=True)

# plot results (matplotlib)
column1.plot_results()

# plot results (plotly)
column1.plot_results_3D()
