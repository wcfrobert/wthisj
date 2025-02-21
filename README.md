<h1 align="center">
  <br>
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/logo.png?raw=true" alt="logo" style="width: 60%;" />
  <br>
  Concrete Slab Punching Shear Calculation In Python
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





## Quick Start

Run main.py:

```python
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
```

`PunchingShearSection.preview()`

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/preview.png?raw=true" alt="fig" style="width: 70%;" />
</div>

`PunchingShearSection.solve()`

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/solve.png?raw=true" alt="fig" style="width: 70%;" />
</div>

`PunchingShearSection.plot_results()`

<div align="center">
  <img src="https://github.com/wcfrobert/wthisj/blob/master/doc/results.png?raw=true" alt="fig" style="width: 70%;" />
</div>

`PunchingShearSection.plot_results_3D()`

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

- `PunchingShearSection.preview()`
- `PunchingShearSection.add_perimeter()`
- `PunchingShearSection.add_opening()`
- `PunchingShearSection.rotate()`



**Run Analysis**

- `PunchingShearSection.solve()`




**Plotting Results**

- `PunchingShearSection.preview()`
- `PunchingShearSection.plot_results()`
- `PunchingShearSection.plot_results_3D()`





## Theoretical Background


TODO



## Assumptions and Limitations

TODO



## License

MIT License

Copyright (c) 2025 Robert Wang
