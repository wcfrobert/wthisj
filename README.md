<h1 align="center">
  <br>
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/logo.png?raw=true" alt="logo" style="width: 50%;" />
  <br>
</h1>

<h3 align="center"> Punching Shear Calculation in Python </h3>

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/demo.gif?raw=true" alt="demo" style="width: 100%;" />
</div>


- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Theoretical Background](#theoretical-background)
- [Documentation](#documentation)
- [Assumptions and Limitations](#assumptions-and-limitations)
- [License](#license)


## Introduction

**wthisj** (what the heck is j?) is a python program that that performs punching shear calculations per ACI 318 and ACI 421.1R. Notable Features include:

* Supports all column conditions (interior, edge, and corner)
* Easily add stud rails (i.e. polygonal shear perimeters)
* Easily add openings
* Interactive visualization of shear stresses
* Advanced features like principal axes rotation, consideration of moment due to centroid eccentricity, non-uniform depth shear perimeters, fast numerical approximation of $J_{cx}$ and $J_{cy}$ for any arbitrary sections.



## Quick Start

Here's a quick start script found in `main.py`:

```python
import wthisj

# initialize a critical shear section
column1 = wthisj.PunchingShearSection(col_width = 24,
                                      col_depth = 24,
                                      slab_avg_depth = 12,
                                      condition = "NW",
                                      overhang_x = 12,
                                      overhang_y = 12,
                                      studrail_length = 0)

# add as many openings as you want
column1.add_opening(xo=40, yo=-10, width=18, depth=20)

# preview geometry
column1.preview()

# calculate punching shear stress
results = column1.solve(Vz = -100,
                        Mx = 400,
                        My = 400,
                        consider_ecc=False,
                        auto_rotate=True, 
                        verbose=True)

# plot results (matplotlib)
column1.plot_results()

# plot results (plotly)
column1.plot_results_3D()
```

* There are 9 possible conditions (1 interior, 4 edge, 4 corner), each represented using the cardinal directions on a compass (NW, N, NE, W, I, E, SW, S, SE), except "I" which stands for interior. For example, "NW" represents a top-left corner column.
* Units should be in **(KIPS, IN)**. 
* Sign convention for the applied forces should follows the right-hand rule. Note **Vz should be negative** unless you are checking uplift. 

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/signconvention.png?raw=true" alt="fig" style="width: 70%;" />
</div>


Running the main quick start script will produce the following:

* `PunchingShearSection.preview()` generates a preview of the critical shear perimeter, openings, columns, slab edge, as well as a tabulation of its geometric properties.

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/preview.png?raw=true" alt="fig" style="width: 70%;" />
</div>

* `PunchingShearSection.solve()` runs an analysis and returns a result dataframe. The critical shear section is discretized numerically into many fibers, each row in the data frame represents one fiber. Key calculation results will be printed to console if `verbose` is set to True.

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/solve.png?raw=true" alt="fig" style="width: 90%;" />
</div>



<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/solve_status.png?raw=true" alt="fig" style="width: 50%;" />
</div>





* `PunchingShearSection.plot_results()` generates a shear stress contour plot + a concise calculation summary.

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/results.png?raw=true" alt="fig" style="width: 70%;" />
</div>

* `PunchingShearSection.plot_results_3D()` generates a interactive 3D visualization in html format - viewable in most web browsers.

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/results_3D.png?raw=true" alt="fig" style="width: 70%;" />
</div>


## Installation

**Option 1: Anaconda Python**

Run main.py using your base Anaconda environment. 

1. Download Anaconda python
2. Download this package (click the green "Code" button above or download the latest release)
3. Open and run "main.py" in Anaconda's Spyder IDE.

The following packages are used:

* Numpy
* Pandas
* Matplotlib
* Plotly


**Option 2: Regular Python**

1. Download this project to a folder of your choosing. You can use git, or download one of the tagged releases.
    ```
    git clone https://github.com/wcfrobert/wthisj.git
    ```
2. Change directory into where you downloaded wthisj
    ```
    cd wthisj
    ```
3. Create virtual environment
    ```
    py -m venv venv
    ```
4. Activate virtual environment
    ```
    venv\Scripts\activate
    ```
5. Install requirements
    ```
    pip install -r requirements.txt
    ```
6. run wthisj
    ```
    py main.py
    ```

Pip install is also available.

```
pip install wthisj
```



## Examples

**Example #1 - Interior Condition**

Here's a 24" x 24" interior column supporting a slab with 12" effective depth, subjected to 100 kips of shear, and 400 kip.in of unbalanced moment in the X-axis. 

* Unit should be in **(kip, in)**
* User must provide the slab depth (NOT slab thickness) - with cover already subtracted.
* Sign convention for the applied forces should follows the right-hand rule. **Vz is almost always negative** unless you are considering uplift

```python
import wthisj
shear_section = wthisj.PunchingShearSection(col_width=24, 
                                            col_depth=24, 
                                            slab_avg_depth=12, 
                                            condition="I")
results = shear_section.solve(Vz = -100, Mx = 400, My = 0)
fig1 = shear_section.preview()
fig2 = shear_section.plot_results()
fig3 = shear_section.plot_results_3D()
```


<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/example1.png?raw=true" alt="fig" style="width: 70%;" />
</div>


**Example #2 - Edge Condition**

Here's a 24" x 24" column at the edge of the slab with a 6" overhang beyond the column face. It is subjected to 100 kips of shear, and 400 kip.in of Y-axis unbalanced moment. 

* There are 9 possible conditions (1 interior, 4 edge, 4 corner), each **represented using the cardinal directions** on a compass (**NW, N, NE, W, I, E, SW, S, SE**) - except "I" which stands for interior. In this example, we use "W" to indicate an edge condition with the edge on the left. You can also specify edge condition with: "N", "W", "S", "E".
* Again, pay attention to the signs and follow right-hand rule. In this case, the unbalanced moment exerts additional stress on the right side of the column.

```python
import wthisj
shear_section = wthisj.PunchingShearSection(col_width=24, 
                                            col_depth=24, 
                                            slab_avg_depth=12, 
                                            condition="W")
results = shear_section.solve(Vz = -100, Mx = 0, My = 400)
fig = shear_section.plot_results()
```


<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/example2.png?raw=true" alt="fig" style="width: 70%;" />
</div>


**Example #3 - Corner Condition w/ Principal Axes Rotation**

Here's a 24" x 24" column at a corner condition with 6" overhang beyond the column face. It is subjected to 100 kips of shear, and 400 kip.in of unbalanced moment in both the X and Y-axis. 

* You can specify corner condition with: "NW", "NE", "SW", "SE".
* If you wish to apply moment one axis at a time, just specify zero values for either `Mx` and `My` .
* Tell wthisj to rotate to principal axes by setting `auto_rotate` to True (which is the default).

```python
import wthisj
shear_section = wthisj.PunchingShearSection(col_width=24, 
                                            col_depth=24, 
                                            slab_avg_depth=12, 
                                            condition="NW",
                                            overhang_x=6,
                                            overhang_y=6)
results = shear_section.solve(Vz = -100, Mx = 400, My = 400, auto_rotate = True)
fig = shear_section.plot_results()
```


<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/example3.png?raw=true" alt="fig" style="width: 70%;" />
</div>
**Example #4 - Openings**

Let's repeat example #1, but this time, add an 12" x 24" opening 48 inches away to the right (measured from face of column to edge of opening).

* The user can add as many openings as they want with `PunchingShearSection.add_opening()`. Note that the offset (x, y) is measured from the center of the column (always at 0,0) to the bottom left corner of the opening.

```python
import wthisj
shear_section = wthisj.PunchingShearSection(col_width=24, 
                                            col_depth=24, 
                                            slab_avg_depth=12, 
                                            condition="I")
shear_section.add_opening(xo=60, yo =0, width=12, depth=24)
results = shear_section.solve(Vz = -100, Mx = 400, My = 0)
fig = shear_section.preview()
fig = shear_section.plot_results()
```

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/example4a.png?raw=true" alt="fig" style="width: 70%;" />
</div>

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/example4b.png?raw=true" alt="fig" style="width: 70%;" />
</div>




**Example #5 - Polygonal Shear Perimeter (Stud Rails)**

Repeat example #2, but this time, add 48" long stud rails on all three sides to create a polygonal shear section.

* Creating polygonal shear perimeters is easy. Simply specify a non-zero value for the`studrail_length` argument when initializing a shear section object.
* Shear stress will be calculated for this polygonal perimeter. The internal failure plane that crosses the stud rail is not evaluated.
* wthisj calculates `gamma_vx` and `gamma_vy` based on the recommendations provided in ACI 421.1R, the user may also opt to specify it themselves.

```python 
import wthisj
shear_section = wthisj.PunchingShearSection(col_width=24, 
                                            col_depth=24, 
                                            slab_avg_depth=12, 
                                            condition="W",
                                           	studrail_length = 48)
results = shear_section.solve(Vz = -100, Mx = 0, My = 400, 
                              gamma_vx = "auto", 
                              gamma_vy = 0.4,
                              consider_ecc=False)
fig = shear_section.plot_results()
```

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/example5.png?raw=true" alt="fig" style="width: 70%;" />
</div>


**Example #6 - Centroid Offset Moment Adjustment**

Repeat example #2, but this time, disable moment adjustment due to eccentricity. This adjustment is explained in detail the theoretical background and in ACI 421.1R. In short, the shear section centroid may be misaligned with the column centroid which can generate addition moment.

In some case, the user may be specifying the adjusted moment already, in which case please set `consider_ecc` to False

* This feature is enabled by default. 
* This additional moment can be huge when stud rails are provided...

```python
import wthisj
shear_section = wthisj.PunchingShearSection(col_width=24, 
                                            col_depth=24, 
                                            slab_avg_depth=12, 
                                            condition="W")
results = shear_section.solve(Vz = -100, Mx = 0, My = 1263, consider_ecc = False)
fig = shear_section.plot_results()
```

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/example6.png?raw=true" alt="fig" style="width: 70%;" />
</div>


**Example #7 - Fully Custom Shear Perimeter**

You can also draw a highly customized shear perimeter. Here's a triangular one where one of the sides have a different depth than the other two.

* Draw your own perimeter by turning `auto_generate_perimeter` to False, and using the `.add_perimeter()` method.
* When analyzing a custom shear perimeter, the user must specify gamma_v themselves

```python
import wthisj
shear_section = wthisj.PunchingShearSection(col_width=0, 
                                            col_depth=0, 
                                            slab_avg_depth=12, 
                                            condition="I",
                                           	auto_generate_perimeter = False)

shear_section.add_perimeter(start=(-18,-18), end=(-18,18), depth=12)
shear_section.add_perimeter(start=(-18,18), end=(18,0), depth=12)
shear_section.add_perimeter(start=(18,0), end=(-18,-18), depth=16)

results = shear_section.solve(Vz = -100, Mx = 400, My = 0, gamma_vx = 0.4, gamma_vy = 0.4)
fig2 = shear_section.plot_results()
```

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/example6.png?raw=true" alt="fig" style="width: 70%;" />
</div>

## Theoretical Background

[Link to theoretical background](https://robwang.io/engineering/punching-shear.html)



## Documentation

Here are all the public methods available to the user:

- `PunchingShearSection(col_width, col_height, slab_avg_depth, condition, overhang_x=0, overhang_y=0, studrail_length=0, auto_generate_perimeter=True, PATCH_SIZE=0.5)`
- `PunchingShearSection.add_perimeter(start, end, depth)`
- `PunchingShearSection.add_opening(xo, yo, width, depth)`
- `PunchingShearSection.rotate(angle)`

- `PunchingShearSection.solve(Vz, Mx, My, gamma_vx="auto", gamma_vy="auto", consider_ecc=False, auto_rotate=True, verbose=True)`

- `PunchingShearSection.preview()`
- `PunchingShearSection.plot_results(colormap="jet", cmin="auto", cmax="auto")`
- `PunchingShearSection.plot_results_3D(colormap="jet", cmin="auto", cmax="auto", scale=10)`

If you need guidance at any time, use the help() command to access method docstrings. For example, here is the output for `help(wthisj.PunchingShearSection.add_opening)`

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/help.png?raw=true" alt="fig" style="width: 80%;" />
</div>


### 1.0 Define Shear Perimeter

**`PunchingShearSection(col_width, col_depth, slab_avg_depth, condition, overhang_x=0, overhang_y=0, studrail_length=0, auto_generate_perimeter=True, PATCH_SIZE=0.5)`** - Instantiate and return a PunchingShearSection object.

* col_width: float
  * Column dimension along x-axis

* col_depth: float
  * Column dimension along y-axis

* slab_avg_depth: float
  * Slab depth from outermost compression fiber to outermost tension rebar. Use the average depth of two orthogonal slab directions.

* condition: string
  * String used to specify interior, edge, or corner column condition. Valid inputs look like the cardinal directions on a compass.
  * "N", "S", "W", "E", "NW", "NE", "SW", "SE"
  * For example, "NW" is a corner condition with slab edge to the top left. "W" is an edge condition with slab edge on the left.

* overhang_x: float (OPTIONAL)
  * Default = 0
  * Slab overhang dimension along the X-axis beyond column face.
  * Based on CRSI recommendations, overhang exceeding b/2 + d are treated as interior condition (where d is the slab depth, and b is the column dimension perpendicular to the edge).

* overhang_y: float (OPTIONAL)
  * Default = 0
  * Slab overhang dimension along the Y-axis beyond column face.
  * Based on CRSI recommendations, overhang exceeding b/2 + d are treated as interior condition (where d is the slab depth, and b is the column dimension perpendicular to the edge).

* studrail_length: float (OPTIONAL)
  * Default = 0
  * Stud rails may be added to expand the punching shear perimeter into a polygonal pattern. The exact geometry is described in ACI 318-19. We will assume stud rails always exist at the column corners, and that a minimum of two rails exist on each face. Parameters like spacing and number of stud rails are irrelevant here because all we care about is the perimeter geometry (wthisj does NOT calculate any shear capacities!)

* auto_generate_perimeter: bool (OPTIONAL)
  * Default = True
  * Automatically generate the punching shear perimeter based on the arguments entered by the user above. Alternatively, the user may set this parameter to False, then draw each perimeter line manually using the `.add_perimeter()` method.

* PATCH_SIZE: float (OPTIONAL)
  * Default = 0.5
  * By default, the shear perimeter is numerically discretized into 0.5" fibers. You can specify a smaller fiber size to improve accuracy. 0.5" is small enough for most cases.

```python
# define a top-left corner column (24"x24") supporting a slab with rebar depth of 12". 
# Add 36" long stud rails on the inner faces. Slab overhang is 12" in both directions.
column1 = wthisj.PunchingShearSection(col_width = 24,
                                      col_deptht = 24,
                                      slab_avg_depth = 12,
                                      condition = "NW",
                                      overhang_x = 12,
                                      overhang_y = 12,
                                      studrail_length = 36)
```



> [!NOTE]
> wthisj numerically approximates $I_x$ and $I_y$ by discretizing the perimeter into tiny 0.5 inch fibers, each fiber has an infinitesimal area (dA) which is then summed to approximate the moment of inertia integrals. The default fiber size is usually accurate enough; however, users may opt to reduce the fiber size further by changing the `PATCH_SIZE` argument when initializing a `PunchingShearSection()` object.



> [!NOTE]
> If a `PunchingShearSection()` object has a large enough `overhang_x` or `overhang_y`, it will be automatically converted to an interior condition. The limit is explained in the theoretical background section.





### 2.0 Add Openings

**`PunchingShearSection.add_opening(xo, yo, width, depth)`** - Add a rectangular opening nearby. The column center is always located at (0,0). Specify bottom left corner of opening as well as opening size. You can add an arbitrary number of openings. A warning will be printed to console if the openings is further than 4h away because the specified opening can be ignored. This method modifies the PunchingShearSection object internally and does not return anything.

* xo: float
  * x-offset from column center (0,0) to the bottom left corner of opening
* yo: float
  * y-offset from column center (0,0) to the bottom left corner of opening
* width: float
  * opening width
* depth: float
  * opening height


```python
# add a 18" x 20" opening with bottom-left corner located 80" left and 10" below the column center.
column1.add_opening(xo=80, yo=-10, width=18, depth=20)
```





### 3.0 Run Analysis

**`PunchingShearSection.solve(Vz, Mx, My, gamma_vx="auto", gamma_vy="auto", consider_ecc=True, auto_rotate=True, verbose=True)`** - Start analysis routine. Returns a dataframe where each row is a fiber within the shear perimeter, and the columns are the intermediate calculation results. 

* Vz: float
  * Applied shear force in KIPS. Should always be NEGATIVE unless you are checking uplift
* Mx: float
  * Applied moment about the X-axis in KIP.IN.
* My: float
  * Applied moment about the Y-axis in KIP.IN.
* gamma_vx: float or string (OPTIONAL)
  * Percentage of X moment transferred to the column via shear. wthisj will automatically calculate this in accordance with ACI 421.1R. Or the user may enter a specific value of gamma_vx (e.g. 0.4)
* gamma_vy: float or string (OPTIONAL)
  * Percentage of Y moment transferred to the column via shear. wthisj will automatically calculate this in accordance with ACI 421.1R. Or the user may enter a specific value of gamma_vy (e.g. 0.4)
* consider_ecc: bool (OPTIONAL)
  * Whether or not to consider additional moment due to eccentricity between the column centroid and perimeter centroid. Defaults to True. Refer to the theory section for more info.
* auto_rotate: bool (OPTIONAL)
  * Whether or not to auto-rotate geometry if it is not in principal orientation. Please note equilibrium is only maintained for sections in its principal orientation. Superposition of stress due to bi-axial moment is only valid when Ixy = 0. Refer to the theoretical background section for more info.
* verbose: bool (OPTIONAL)
  * Whether or not to printout calculation result and other helpful messages. Default = True.


```python
# Check punching shear stress for a perimeter subjected to 100 kips of shear, 400 kips.in of moment in both directions.
# Not rotating the section to principal orientation.
# Not considering additional moment due to eccentricity between column and perimeter centroid.
results = column1.solve(Vz = -100,
                        Mx = 400,
                        My = 400,
                        consider_ecc=False,
                        auto_rotate=False, 
                        verbose=True)
```



### 4.0 Preview Geometry

**`PunchingShearSection.preview()`** - Preview critical shear perimeter, openings, slab edges, and other surrounding contexts. Geometric properties like $b_o$ and $I_x$ are also shown. This method returns a matplotlib fig object.

* No argument necessary.

```python
# visualize what the shear perimeter looks like
fig1 = column1.preview()
```



### 5.0 Visualize Results - 2D

**`PunchingShearSection.plot_results(colormap="jet", cmin="auto", cmax="auto")`** - Visualize punching shear calculation results and stress contour. This method returns a matplotlib fig object.

* colormap: string (OPTIONAL)
  * named colormap. Here's a [list of all available colormaps](https://matplotlib.org/stable/gallery/color/colormap_reference.html). "jet" is a common one for stress visualization.
* cmin: float or string (OPTIONAL)
  * specify min range for color mapping. Default = min(stress)
* cmax: float or string (OPTIONAL)
  * specify max range for color mapping. Default = max(stress)

```python
# visualize shear stress plot. Use the "turbo" colormap instead 
# set cmax to 160 psi so that anything higher is colored red
fig2 = column1.plot_results(colormap="turbo", cmax=160)
```



### 6.0 Visualize Results - 3D

**`PunchingShearSection.plot_results_3D(colormap="jet", cmin="auto", cmax="auto", scale=10)`** - Visualize punching shear calculation results in an interactive 3D format using plotly. This method returns a plotly figure object.


* colormap: string (OPTIONAL)
  * named colormap. Here's a [list of all available colormaps](https://matplotlib.org/stable/gallery/color/colormap_reference.html). "jet" is a common one for stress visualization.
* cmin: float or string (OPTIONAL)
  * specify min range for color mapping. Default = min(stress)
* cmax: float or string (OPTIONAL)
  * specify max range for color mapping. Default = max(stress)
* scale: float (OPTIONAL)
  * scaling factor used to adjust the size of vector plot. Default is 10. Which means the max vector is 10" in the Z-dimension.


```python
# visualize shear stress. Use the "plasma" colormap
# change scale to 5 so the stress vectors are not too large.
fig3 = column1.plot_results_3D(colormap="plasma", scale=5)
```





### 7.0 Advanced Features

**`PunchingShearSection.add_perimeter(start, end, depth)`** - Draw a line of shear perimeter. This is an advanced feature for users who wish to draw highly customized perimeter, such as ones with non-uniform depths. This is not needed in most cases because the `auto_generate_perimeter` parameter is set to True during initialization, and a perimeter is automatically generated. This method modifies the PunchingShearSection object internally and does not return anything.

* start: [float]
  * [x, y] coordinate of the start point
* end: [float]
  * [x, y] coordinate of the end point
* depth: float
  * slab depth along this line


```python
# define a 18" x 18" column, but turn auto-generate perimeter off
column1 = wthisj.PunchingShearSection(width = 18,
                                      height = 18,
                                      slab_depth = 12,
                                      condition = "I",
                                      auto_generate_perimeter = False)

# draw a custom perimeter where one side has a slab depth of 6" rather than 12"
column1.add_perimeter(start=[-15,-15], end=[-15,15], depth=12)
column1.add_perimeter(start=[-15,15], end=[12,15], depth=12)
column1.add_perimeter(start=[12,15], end=[12,-15], depth=6)
column1.add_perimeter(start=[12,-15], end=[-15,-15], depth=12)
```

**`PunchingShearSection.rotate(angle)`** - Rotate the section by a specified angle. This is an advanced feature not needed in most cases because the `auto_rotate` argument in `.solve()` is set to True by default. In other words, sections will automatically be rotated to its principal orientation. Please note equilibrium is only maintained for sections in its principal orientation. Superposition of stress due to bi-axial moment is only valid when Ixy = 0. Refer to the theoretical background section for more info. This method modifies the PunchingShearSection object internally and does not return anything. In the backend, the entire geometry is rotated, rather than the moment vector, because the former is easier to implement.

* angle: float
  * rotate shear perimeter by a specified **DEGREE** measured counter clockwise from the +X axis.


```python
# rotate the column by 45 degrees counter-clockwise from +X axis.
column1.rotate(angle=45)
```






## Assumptions and Limitations

* Units should be in **(KIPS, IN)**. 
* wthisj calculates $J_c$ using the recommendations in ACI 421.1R which differs (on the safe side) compared to ACI 318. Refer to section 5 of the Theoretical Background for more info.
* wthisj works by discretizing the critical shear perimeter into tiny **0.5 inch fibers**, each fiber has an infinitesimal area (dA) which is then summed to approximate $J_c$ and other parameters. The default fiber size is usually accurate enough; however, users may opt to reduce the fiber size further by changing the `PATCH_SIZE` argument when initializing a `PunchingShearSection()` object.
* wthisj will only calculate shear stress **demand**. Please calculate concrete shear **capacity** yourself. It should also be noted that wthisj calculates demand using a very specific methodology applicable to the US design practice. Other countries have their own methods of calculating punching shear stress (e.g. EN 1992, fib Model Code 2010). Do NOT mix-and-match building codes when comparing demands to capacity. 
* This is not enterprise software. Please do NOT use it for work. Users assume full risk and responsibility for verifying that the results are accurate.






## License

MIT License

Copyright (c) 2025 Robert Wang
