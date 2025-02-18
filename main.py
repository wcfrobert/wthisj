import wthisj

# initialize a column perimeter - corner condition with studrails
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "I")
# preview geometry
column1.preview()

# calculate punching shear stress
results = column1.solve(P = 100, Mx = 500, My = 90)

# generate 2D plot with matplotlib
column1.plot_results()

# generate interactive 3D plot with plotly
column1.plot_results_3D()

