import wthisj


# initialize a punching shear perimeter
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "SW",
                                      overhang_x = 16,
                                      overhang_y = 16,
                                      L_studrail = 24)

# automatically generate critical perimeter 
column1.auto_generate_perimeters()

# # add openings
# column1.add_opening(dx=60, dy=60, width=36, height=12)

# # preview geometry
column1.preview()
# column1.preview_3D()

# # calculate punching shear stress
# results = column1.solve(P = 100, Mx = 0, My = 0)

# # plot results
# column1.plot_results()
# column1.plot_results_3D()