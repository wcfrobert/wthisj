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
- [Validation Problems](#validation-problems)
- [Installation](#installation)
- [Usage](#usage)
- [Theoretical Background](#theoretical-background)
- [Assumptions and Limitations](#assumptions-and-limitations)
- [License](#license)


## Introduction

**wthisj** (what the heck is j?) is a python program that calculates punching shear stress around a column. It does so using the elastic method along with concepts described in <u>ACI 318</u> and <u>ACI 421.1R</u>. Refer to the [theoretical background](#theoretical-background) section for more info. Notable features include:

* Supports all column conditions (**interior, edge, and corner**)
* Ability to add **stud rails** (i.e. polygonal shear perimeters)
* Ability to add **openings**
* Interactive result visualization
* Other advanced features like principal orientation rotation, and consideration of moment induced by eccentricity between column and centroid of critical shear perimeter

## Quick Start

Here's the minimum viable script. Define a shear perimeter, run analysis, and visualize results in 3 lines of python code. 

``` python
import wthisj

# initialize a column perimeter
column1 = wthisj.PunchingShearSection(width = 24, height = 24, slab_depth = 12, condition = "I")

# calculate punching shear stress
results = column1.solve(P = -100, Mx = 400, My = 0)

# plot results (plotly)
column1.plot_results_3D()
```

Here is a more comprehensive quick start script found in `main.py`:

```python
import wthisj

# initialize a column perimeter. 
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "W",
                                      overhang_x = 12,
                                      overhang_y = 0,
                                      L_studrail = 36)

# add openings
column1.add_opening(dx=80, dy=-10, width=18, height=20)

# preview geometry
column1.preview()

# calculate punching shear stress
results = column1.solve(P = -100,
                        Mx = 400,
                        My = 400,
                        consider_Pe=False,
                        auto_rotate=False, 
                        verbose=True)

# plot results (matplotlib)
column1.plot_results()

# plot results (plotly)
column1.plot_results_3D()
```

* There are (9) possible conditions (1 interior, 4 edge, 4 corner) denoted using the cardinal directions (NW, N, NE, W, I, E, SW, S, SE). 
* Units should be in **(KIPS, IN)**. 
* Sign convention for the applied force follows the right-hand rule and is illustrated below. Note **P should be negative** unless you are checking uplift. 

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/signconvention.png?raw=true" alt="fig" style="width: 70%;" />
</div>


Running the main quick start script will produce the following:

* `PunchingShearSection.preview()` plots a preview of the critical shear perimeter along with all of its geometric properties.

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/preview.png?raw=true" alt="fig" style="width: 70%;" />
</div>

* `PunchingShearSection.solve()` runs an analysis and returns a result dataframe. The critical shear section is discretized numerically into many fibers, each row in the dataframe represents one fiber.

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/solve.png?raw=true" alt="fig" style="width: 70%;" />
</div>

* `PunchingShearSection.plot_results()` plots the shear stress contour + a short result summary.

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/results.png?raw=true" alt="fig" style="width: 70%;" />
</div>

* `PunchingShearSection.plot_results_3D()` plots the shear stress contour in an interactive 3D visualization viewable in most web browsers.

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/demo.gif?raw=true" alt="fig" style="width: 70%;" />
</div>




## Validation Problems

TODO



## Installation

**Option 1: Anaconda Python**

Run main.py using your base Anaconda environment. 

1. Download Anaconda python
2. Download this package (click the green "Code" button and download zip file)
3. Open and run "main.py" in Anaconda's Spyder IDE.

The following packages are used:

* Numpy
* Pandas
* Matplotlib
* Plotly


**Option 2: Regular Python**

1. Download this project to a folder of your choosing
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


## Usage

Here are all the public methods available to the user:

**Step 1: Define a Punching Shear Perimeter**

- `PunchingShearSection(width, height, slab_depth, condition, overhang_x=0, overhang_y=0, L_studrail=0, auto_generate_perimeter=True, PATCH_SIZE=0.5)`
- `PunchingShearSection.add_perimeter(start, end, depth)`
- `PunchingShearSection.add_opening(dx, dy, width, height)`
- `PunchingShearSection.rotate(angle)`

**Step 2: Run Analysis**

- `PunchingShearSection.solve(P, Mx, My, gamma_vx="auto", gamma_vy="auto", consider_Pe=True, auto_rotate=True, verbose=True)`


**Step 3: Plotting Results**

- `PunchingShearSection.preview()`
- `PunchingShearSection.plot_results(colormap="jet", cmin="auto", cmax="auto")`
- `PunchingShearSection.plot_results_3D(colormap="jet", cmin="auto", cmax="auto", scale=10)`

If you need guidance at any time, use the help() command to access method docstrings. For example, here is the output for `help(wthisj.PunchingShearSection.add_opening)`

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/help.png?raw=true" alt="fig" style="width: 80%;" />
</div>


### 1. Methods for Defining a Shear Perimeter

**`PunchingShearSection(width, height, slab_depth, condition, overhang_x=0, overhang_y=0, L_studrail=0, auto_generate_perimeter=True, PATCH_SIZE=0.5)`** - Instantiate a punching shear section object.

<u>Arguments:</u>

* width: float
  * Column dimension along x-axis

* height: float
  * Column dimension along y-axis

* slab_depth: float
  * Slab depth from outermost compression fiber to outermost tension rebar. Use the average depth of two orthogonal slab directions.

* condition: string
  * String used to specify interior, edge, or corner column condition. Valid inputs look like the cardinal directions on a compass.
  * "N", "S", "W", "E", "NW", "NE", "SW", "SE"
  * For example, "NW" is a corner condition with slab edge to the top left. "W" is an edge condition with slab edge on the left.

* overhang_x: float (OPTIONAL)
  * Default = 0
  * Slab overhang dimension along the X-axis beyond column face.
  * Based on CRSI recommendations, overhang exceeding b/2 + d are treated as interior condition where d is the slab depth, and b is the column dimension perpendicular to the edge.

* overhang_y: float (OPTIONAL)
  * Default = 0
  * Slab overhang dimension along the Y-axis beyond column face.
  * Based on CRSI recommendations, overhang exceeding b/2 + d are treated as interior condition where d is the slab depth, and b is the column dimension perpendicular to the edge.

* L_studrail: float (OPTIONAL)
  * Default = 0
  * Stud rails may be added to expand the punching shear perimeter into a polygonal pattern. The exact geometry is described in ACI 318-19. We will assume stud rails always exist at the column corners, and that a minimum of two rails exist on each face. Spacing and number of stud rails are irrelevant here because all we care about is the perimeter geometry.

* auto_generate_perimeter: bool (OPTIONAL)
  * Default = True
  * Automatically generate the punching shear perimeter based on the arguments entered by the user above. Alternatively, the user may set this parameter to False, then draw each perimeter line manually using the `.add_perimeter()` method.

* PATCH_SIZE: float (OPTIONAL)
  * Default = 0.5
  * By default, the shear perimeter is numerically discretized into 0.5" fibers. You can specify a smaller fiber size to improve accuracy. 0.5" is small enough for most cases.

<u>Returns:</u>

* PunchingShearSection object

```python
# define a top-left corner column (24"x24") supporting a slab with rebar depth of 12". 
# Add 36" long stud rails on the inner faces. Slab overhang is 12" in both directions.
column1 = wthisj.PunchingShearSection(width = 24,
                                      height = 24,
                                      slab_depth = 12,
                                      condition = "NW",
                                      overhang_x = 12,
                                      overhang_y = 12,
                                      L_studrail = 36)
```



**`PunchingShearSection.add_opening(dx, dy, width, height)`** - Add an opening nearby. The column center is always located at (0,0).

<u>Arguments:</u>

* dx: float
  * x-offset from column center (0,0) to the bottom left corner of opening
* dy: float
  * y-offset from column center (0,0) to the bottom left corner of opening
* width: float
  * opening width
* height: float
  * opening height

<u>Returns:</u>

* None

```python
# add a 18" x 20" opening with bottom-left corner located 80" left and 10" below the column center.
column1.add_opening(dx=80, dy=-10, width=18, height=20)
```





### 2. Method for Running Analysis

**`PunchingShearSection.solve(P, Mx, My, gamma_vx="auto", gamma_vy="auto", consider_Pe=True, auto_rotate=True, verbose=True)`** - Run analysis routine.

<u>Arguments:</u>

* P: float
* Mx: float
* My: float
* gamma_vx: float or string (OPTIONAL)
* gamma_vy: float or string (OPTIONAL)
* consider_Pe: bool (OPTIONAL)
* auto_rotate: bool (OPTIONAL)
* verbose: bool (OPTIONAL)

<u>Returns:</u>

* df_perimeter: dataframe

```python
results = column1.solve(P = -100,
                        Mx = 400,
                        My = 400,
                        consider_Pe=False,
                        auto_rotate=False, 
                        verbose=True)
```



### 3. Methods for Result Visualization

**`PunchingShearSection.preview()`** - Preview critical shear perimeter, along with openings, slab edges, and other contexts. Geometric properties like $b_o$ and $I_x$ are also shown.

<u>Arguments:</u>

* None

<u>Returns:</u>

* fig: matplotlib figure object

```python
# visualize what the shear perimeter looks like
fig1 = column1.preview()
```



**`PunchingShearSection.plot_results(colormap="jet", cmin="auto", cmax="auto")`** - Visualize punching shear calculation results in a 2D format using matplotlib.

<u>Arguments:</u>

* colormap: string (OPTIONAL)
* cmin: float or string (OPTIONAL)
* cmax: float or string (OPTIONAL)

<u>Returns:</u>

* fig: matplotlib figure object

```python
# visualize shear stress plot. Use the "turbo" colormap instead. Set cmax to 160 psi so that anything higher is colored red.
fig2 = column1.plot_results(colormap="turbo", cmax=160)
```



**`PunchingShearSection.plot_results_3D(colormap="jet", cmin="auto", cmax="auto", scale=10)`** - Visualize punching shear calculation results in an interactive 3D format using plotly.

<u>Arguments:</u>

* colormap: string (OPTIONAL)
* cmin: float or string (OPTIONAL)
* cmax: float or string (OPTIONAL)
* scale: float (OPTIONAL)

<u>Returns:</u>

* fig: plotly figure object

```python
# visualize shear stress. Use the "plasma" colormap. Change scale to 5 so the stress vectors are not too large.
fig3 = column1.plot_results_3D(colormap="plasma", scale=5)
```





### 4. Advanced Features

**`PunchingShearSection.add_perimeter(start, end, depth)`** - Draw a shear perimeter line. This is an advanced feature used by users who wish to draw highly customized shear perimeter. Not needed in most cases because the `auto_generate_perimeter` parameter is set to True during initialization.

<u>Arguments:</u>

* start: [float]
  * [x, y] coordinate of the start point
* end: [float]
  * [x, y] coordinate of the end point
* depth: float
  * slab depth along this line

<u>Returns:</u>

* None

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

**`PunchingShearSection.rotate(angle)`** - Rotate the shear section by a specified angle. This is an advanced feature not needed in most cases because the `auto_rotate` argument in `.solve()` is set to True by default. In other words, sections will automatically be rotated to its principal orientation. Equilibrium check will NOT pass unless shear perimeter is in its principal orientation - because superposition of stress due to bi-axial moment is only valid when Ixy = 0. Refer to the theoretical background section for more info.

<u>Arguments:</u>

* angle: float
  * rotate shear perimeter by a specified **DEGREE** measured counter clockwise from the +X axis.

<u>Returns:</u>

* None

```python
# rotate the column by 45 degrees counter-clockwise from +X axis.
column1.rotate(angle=45)
```








## Theoretical Background

TODO













## Assumptions and Limitations

TODO








## License

MIT License

Copyright (c) 2025 Robert Wang
