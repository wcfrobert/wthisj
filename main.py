import wthisj


# initialize a punching shear perimeter
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "NW",
                                      overhang_x = 12,
                                      overhang_y = 0,
                                      L_studrail = 0)

# automatically generate critical perimeter 
column1.auto_generate_perimeters()

# # add openings
column1.add_opening(dx=0, dy=-60, width=44, height=24)
column1.add_opening(dx=60, dy=0, width=12, height=12)

# # preview geometry
column1.preview()

# # calculate punching shear stress
# results = column1.solve(P = 100, Mx = 0, My = 0, gamma_v = 0.4)

# # plot results
# column1.plot_results()







# column1.preview_3D()
# column1.plot_results_3D()



