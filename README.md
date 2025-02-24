<h1 align="center">
  <br>
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/logo.png?raw=true" alt="logo" style="width: 60%;" />
  <br>
  Punching Shear Calculation In Python
  <br>
</h1>



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

**wthisj** (what the heck is j?) is a python program that performs punching shear calculations for concrete slab design. It does so using the elastic method along with concepts described in <u>ACI 318</u> and <u>ACI 421.1R</u>. Refer to the [theoretical background](#theoretical-background) section for more info. Notable features include:

* Supports all column conditions (**interior, edge, and corner**)
* Ability to add **stud rails** (i.e. polygonal shear perimeters)
* Ability to add **openings**
* Interactive result visualization
* Other advanced features like principal orientation rotation for corner columns, and consideration of moment induced by eccentricity between column and centroid of critical shear perimeter

## Quick Start

Here's the minimum viable script. Initialize a shear perimeter, run analysis, and visualize results in 3 lines of python code. 

``` python
import wthisj

# initialize a column perimeter
column1 = wthisj.PunchingShearSection(width = 24, height = 24, slab_depth = 12, condition = "I")

# calculate punching shear stress
results = column1.solve(P = -100, Mx = 400, My = 0)

# plot results (plotly)
column1.plot_results_3D()
```

Here is a more comprehensive quick start script (main.py):

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

Notes:

* There are (9) possible conditions (1 interior, 4 edge, 4 corner) denoted using the cardinal directions on a compass. For example, "SE" is a corner condition with slab edge below and to the right. "W" is an edge condition with edge to the left.
  * "NW"     "N"      "NE"
  * "W"         "I"       "E"
  * "SW"      "S"      "SE"
* Sign convention for the applied force follows the right-hand rule. **P should be negative** unless you are checking uplift. 


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

* `PunchingShearSection.plot_results_3D()` plots the shear stress contour in an interactive 3D visualization.

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

**Defining a Punching Shear Perimeter**

- `PunchingShearSection.__init__(width, height, slab_depth, condition, overhang_x=0, overhang_y=0, L_studrail=0, auto_generate_perimeter=True, PATCH_SIZE=0.5)`
- `PunchingShearSection.add_perimeter(start, end, depth)`
- `PunchingShearSection.add_opening(dx, dy, width, height)`
- `PunchingShearSection.rotate(angle)`

**Run Analysis**

- `PunchingShearSection.solve(P, Mx, My, gamma_vx="auto", gamma_vy="auto", consider_Pe=True, auto_rotate=True, verbose=True)`


**Plotting Results**

- `PunchingShearSection.preview()`
- `PunchingShearSection.plot_results(colormap="jet", cmin="auto", cmax="auto")`
- `PunchingShearSection.plot_results_3D(colormap="jet", cmin="auto", cmax="auto", scale=10)`

If you need further guidance at any time, simply use the help() command to access the method docstrings. For example, here is the output for `help(wthisj.PunchingShearSection.add_opening)`

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/help.png?raw=true" alt="fig" style="width: 80%;" />
</div>



## Theoretical Background


TODO



## Assumptions and Limitations

TODO



## License

MIT License

Copyright (c) 2025 Robert Wang
