import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import matplotlib.cm as mcm
import math
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
pio.renderers.default = "browser"


class PunchingShearSection:
    """
    PunchingShear Section objects are numerical representation of a critical punching 
    shear perimeter around a column in a concrete slab.
    
    Input Args:
        width                       float:: Column support dimension along x
        height                      float:: Column support dimension along y
        slab_depth                  float:: Slab depth from outermost compression fiber to outer-most tension rebar (average of two directions)
        condition                   str::   Specify interior, edge, or corner condition. 
                                            For example, "SE" is a corner condition with slab edge below and to the right.
                                            Valid input include.
                                                "NW"   "N"   "NE"
                                                 "W"   "I"   "E"
                                                "SW"   "S"   "SE"                   
        overhang_x                  (OPTIONAL) float:: slab overhang dimension along x beyond column face. Default = 0.
        overhang_y                  (OPTIONAL) float:: slab overhang dimension along y beyond column face. Default = 0.
        L_studrail                  (OPTIONAL) float:: stud rail length if applicable. default = 0.
        auto_generate_perimeter     (OPTIONAL) bool:: auto-generate punching shear perimeter based on above input. Default = True.
                                                        The user may wish to draw their own perimeter using the .add_perimeter() method.
    
    Public Methods:
        PunchingShearSection.add_perimeter()
        PunchingShearSection.add_opening()
        PunchingShearSection.rotate()
        PunchingShearSection.preview()
        PunchingShearSection.preview_3D()
        PunchingShearSection.solve()
        PunchingShearSection.plot_results()
        PunchingShearSection.plot_results_3D()
    """
    def __init__(self, width, height, slab_depth, condition, overhang_x=0, overhang_y=0, L_studrail=0, auto_generate_perimeter=True):
        # input arguments. See descriptions in docstring above.
        self.width = width
        self.height = height
        self.slab_depth = slab_depth
        self.condition = condition
        self.overhang_x = overhang_x
        self.overhang_y = overhang_y
        self.L_studrail = L_studrail
        self.generate_perimeter = auto_generate_perimeter
        
        # parameters related to column and slab geometry
        self.has_studrail = False if self.L_studrail==0 else True       # bool for if studrail exists
        self.perimeter_pts = []                                         # list of pts to generate perimeter using auto_generate_perimeters()
        self.studrail_pts = []                                          # list of pts to plot studrails
        self.slabedge_lines = []                                        # list of lines to plot slab edge. Each line is two points
        self.slabedge_pts = []                                          # list of pts to plot slab shading
        self.openings = []                                              # list of openings, each opening is a list of 4 pts
        self.openings_draw_pts = []                                     # list of pts in each opening used to draw theta_min and max dotted lines
        self.col_pts = [np.array([-self.width/2, -self.height/2]),      # list of pts to plot column
                        np.array([self.width/2, -self.height/2]),
                        np.array([self.width/2, self.height/2]),
                        np.array([-self.width/2, self.height/2])]                                               
        
        # geometric properties
        self.x_centroid = None                          # centroid x
        self.y_centroid = None                          # centroid y
        self.L = None                                   # total perimeter length
        self.Le = None                                  # total perimeter length (normalized by slab depth)
        self.A = None                                   # total area of welds
        self.Ix = None                                  # moment of inertia X
        self.Iy = None                                  # moment of inertia Y
        self.Iz = None                                  # polar moment of inertia = Ix + Iy
        self.Ixy = None                                 # product moment of inertia
        self.theta_p = None                             # angle offset to principal axis
        self.Sx1 = None                                 # elastic modulus top fiber
        self.Sx2 = None                                 # elastic modulus bottom fiber
        self.Sy1 = None                                 # elastic modulus right fiber
        self.Sy2 = None                                 # elastic modulus left fiber
        
        # applied forces
        self.P = None                                   # applied axial force (we will assume always downwards. Apply abs())
        self.Mx = None                                  # applied moment about X
        self.My = None                                  # applied moment about Y
        self.adjust_eccentric_P = None                  # if user-specified P is at column centroid rather than shear perimeter centroid. Adjust for additional moment
        self.Pex = None                                 # additional moment due to P * eccentricity between col centroid and perimeter centroid
        self.Pey = None                                 # additional moment due to P * eccentricity between col centroid and perimeter centroid
        self.Mx_total = None                            # final governing moment in x-direction (= Mx + Pey)
        self.My_total = None                            # final governing moment in y-direction (= My + Pex)
        
        # dictionary storing perimeter information
        self.perimeter = {"x_centroid":[],              # x coordinate of centroid of patch
                           "y_centroid":[],             # y coordinate of centroid of patch
                           "x_start":[],                # x coordinate of start node
                           "y_start":[],                # y coordinate of start node
                           "x_end":[],                  # x coordinate of end node
                           "y_end":[],                  # y coordinate of end node
                           "depth":[],                  # patch depth
                           "length":[],                 # patch length
                           "area":[],                   # patch area = length * thickness
                           
                           "v_axial": [],               # shear stress from axial demand P
                           "v_Mx": [],                  # shear stress from moment about X
                           "v_My": [],                  # shear stress from moment about Y
                           "v_total": [],               # total shear stress is the summation of the above three components. (not always additive)
                           "Fz":[],                     # used to verify equilibrium sum_Fz = 0
                           "Mxi":[],                    # used to verify equilibrium sum_Mx = 0
                           "Myi":[],                    # used to verify equilibrium sum_My = 0
                           }
        self.df_perimeter = None                        # dict above is converted to dataframe for return to user
        
        # automatically generate punching shear perimeter if applicable
        if auto_generate_perimeter:
            self.auto_generate_perimeters()
        
    
    def add_perimeter(self, start, end, depth):
        """
        Add punching perimeter line by specifying two points. 
        
        Arguments:
            start           list:: [x, y] coordinate of first point
            end             list:: [x, y] coordiante of the second point
            depth           float:: slab depth along this perimeter

        Return:
            None
        """
        MIN_PATCH_SIZE = 0.5  # 0.5 inches default patch size
        
        # convert into numpy arrays
        start = np.array(start)
        end = np.array(end)
        position_vector = end-start
        
        # calculate number of segments
        length_line = np.linalg.norm(position_vector)
        segments = int(length_line // MIN_PATCH_SIZE) if length_line > MIN_PATCH_SIZE else 1
        length_segments = length_line / (segments)
        
        # discretize into N segments (N+1 end points)
        alpha = np.linspace(0, 1, segments+1)
        x_ends = start[0] + alpha * position_vector[0]
        y_ends = start[1] + alpha * position_vector[1]
        x_center = [(x_ends[i] + x_ends[i+1]) / 2 for i in range(len(x_ends)-1)]
        y_center = [(y_ends[i] + y_ends[i+1]) / 2 for i in range(len(y_ends)-1)]
        
        # add to dictionary storing discretization
        self.perimeter["x_centroid"] = self.perimeter["x_centroid"] + list(x_center)
        self.perimeter["y_centroid"] = self.perimeter["y_centroid"] + list(y_center)
        self.perimeter["x_start"] = self.perimeter["x_start"] + list(x_ends[:-1])
        self.perimeter["y_start"] = self.perimeter["y_start"] + list(y_ends[:-1])
        self.perimeter["x_end"] = self.perimeter["x_end"] + list(x_ends[1:])
        self.perimeter["y_end"] = self.perimeter["y_end"] + list(y_ends[1:])
        self.perimeter["length"] = self.perimeter["length"] + [length_segments] * segments
        self.perimeter["depth"] = self.perimeter["depth"] + [depth] * segments
        self.perimeter["area"] = self.perimeter["area"] + [depth * length_segments] * segments
    
    
    def auto_generate_perimeters(self):
        """
        Auto generate punching shear perimeter based on info provided by user during initialization.
        
        Alternatively, the user may specify custom perimeter can calling .add_perimeter() themselves.
        """
        # shorthand variable
        b = self.width
        h = self.height
        d = self.slab_depth
        L = self.L_studrail
        
        # switch-case for all 9 conditions
        SLAB_EXTENT_FACTOR = 4
        if self.condition == "N":
            self.slabedge_lines.append([[-b/2-L-SLAB_EXTENT_FACTOR*b, h/2+self.overhang_y]   ,    [b/2+L+SLAB_EXTENT_FACTOR*b, h/2+self.overhang_y]])
            self.slabedge_pts.append([-b/2-L-SLAB_EXTENT_FACTOR*b, h/2+self.overhang_y])
            self.slabedge_pts.append([b/2+L+SLAB_EXTENT_FACTOR*b, h/2+self.overhang_y])
            self.slabedge_pts.append([b/2+L+SLAB_EXTENT_FACTOR*b, -h/2-L-SLAB_EXTENT_FACTOR*h*1.5])
            self.slabedge_pts.append([-b/2-L-SLAB_EXTENT_FACTOR*b, -h/2-L-SLAB_EXTENT_FACTOR*h*1.5])
            if self.has_studrail:
                self.perimeter_pts.append([-b/2-L-d/2   ,   h/2+self.overhang_y])
                self.perimeter_pts.append([-b/2-L-d/2  ,    -h/2-d/2])
                self.perimeter_pts.append([-b/2-d/2    ,   -h/2-L-d/2])
                self.perimeter_pts.append([b/2+d/2     ,   -h/2-L-d/2])
                self.perimeter_pts.append([b/2+L+d/2   ,   -h/2-d/2])
                self.perimeter_pts.append([b/2+L+d/2   ,    h/2+self.overhang_y])

                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2, -h/2-L]]) # bot
                self.studrail_pts.append([[b/2, -h/2]   ,    [b/2, -h/2-L]]) # bot
                self.studrail_pts.append([[b/2, h/2]   ,    [b/2+L, h/2]]) # right
                self.studrail_pts.append([[b/2, -h/2]  ,    [b/2+L, -h/2]]) # right
                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2-L, h/2]]) # left
                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2-L, -h/2]]) # left
            else:
                # based on CRSI design guide. If overhang exceeds b/2 + d, treat as interior condition
                if self.overhang_y > b/2 + d:
                    self.perimeter_pts.append([-b/2-d/2   ,   h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2   ,    h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,   h/2+d/2])
                else:
                    self.perimeter_pts.append([-b/2-d/2   ,   h/2+self.overhang_y])
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   h/2+self.overhang_y])
        
        
        elif self.condition == "S":
            self.slabedge_lines.append([[-b/2-L-SLAB_EXTENT_FACTOR*b, -h/2-self.overhang_y]   ,    [b/2+L+SLAB_EXTENT_FACTOR*b, -h/2-self.overhang_y]])
            self.slabedge_pts.append([-b/2-L-SLAB_EXTENT_FACTOR*b, -h/2-self.overhang_y])
            self.slabedge_pts.append([b/2+L+SLAB_EXTENT_FACTOR*b, -h/2-self.overhang_y])
            self.slabedge_pts.append([b/2+L+SLAB_EXTENT_FACTOR*b, h/2+L+SLAB_EXTENT_FACTOR*h*1.5])
            self.slabedge_pts.append([-b/2-L-SLAB_EXTENT_FACTOR*b, h/2+L+SLAB_EXTENT_FACTOR*h*1.5])
            if self.has_studrail:
                self.perimeter_pts.append([b/2+L+d/2   ,    -h/2-self.overhang_y])
                self.perimeter_pts.append([b/2+L+d/2   ,    h/2+d/2])
                self.perimeter_pts.append([b/2+d/2     ,    h/2+L+d/2])
                self.perimeter_pts.append([-b/2-d/2    ,    h/2+L+d/2])
                self.perimeter_pts.append([-b/2-L-d/2  ,    h/2+d/2])
                self.perimeter_pts.append([-b/2-L-d/2   ,   -h/2-self.overhang_y])

                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2, h/2+L]]) # top
                self.studrail_pts.append([[b/2, h/2]    ,    [b/2, h/2+L]]) # top
                self.studrail_pts.append([[b/2, h/2]   ,    [b/2+L, h/2]]) # right
                self.studrail_pts.append([[b/2, -h/2]  ,    [b/2+L, -h/2]]) # right
                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2-L, h/2]]) # left
                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2-L, -h/2]]) # left
            else:
                # based on CRSI design guide. If overhang exceeds b/2 + d, treat as interior condition
                if self.overhang_y > b/2 + d:
                    self.perimeter_pts.append([-b/2-d/2   ,   h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2   ,    h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,   h/2+d/2])
                else:
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-self.overhang_y])
                    self.perimeter_pts.append([-b/2-d/2   ,   h/2+d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   h/2+d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-self.overhang_y])
        
        
        elif self.condition == "W":
            self.slabedge_lines.append([[-b/2-self.overhang_x, -h/2-L-h*SLAB_EXTENT_FACTOR]   ,    [-b/2-self.overhang_x, h/2+L+h*SLAB_EXTENT_FACTOR]])
            self.slabedge_pts.append([-b/2-self.overhang_x, -h/2-L-h*SLAB_EXTENT_FACTOR])
            self.slabedge_pts.append([-b/2-self.overhang_x, h/2+L+h*SLAB_EXTENT_FACTOR])
            self.slabedge_pts.append([b/2+SLAB_EXTENT_FACTOR*b*1.5, h/2+L+h*SLAB_EXTENT_FACTOR])
            self.slabedge_pts.append([b/2+SLAB_EXTENT_FACTOR*b*1.5, -h/2-L-h*SLAB_EXTENT_FACTOR])
            if self.has_studrail:
                self.perimeter_pts.append([-b/2-self.overhang_x   ,    -h/2-L-d/2])
                self.perimeter_pts.append([b/2+d/2     ,   -h/2-L-d/2])
                self.perimeter_pts.append([b/2+L+d/2   ,   -h/2-d/2])
                self.perimeter_pts.append([b/2+L+d/2   ,    h/2+d/2])
                self.perimeter_pts.append([b/2+d/2     ,    h/2+L+d/2])
                self.perimeter_pts.append([-b/2-self.overhang_x   ,    h/2+L+d/2])

                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2, h/2+L]]) # top
                self.studrail_pts.append([[b/2, h/2]    ,    [b/2, h/2+L]]) # top
                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2, -h/2-L]]) # bot
                self.studrail_pts.append([[b/2, -h/2]   ,    [b/2, -h/2-L]]) # bot
                self.studrail_pts.append([[b/2, h/2]   ,    [b/2+L, h/2]]) # right
                self.studrail_pts.append([[b/2, -h/2]  ,    [b/2+L, -h/2]]) # right
            else:
                # based on CRSI design guide. If overhang exceeds h/2 + d, treat as interior condition
                if self.overhang_x > h/2 + d:
                    self.perimeter_pts.append([-b/2-d/2   ,   h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2   ,    h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,   h/2+d/2])
                else:
                    self.perimeter_pts.append([-b/2-self.overhang_x   ,    -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+d/2])
                    self.perimeter_pts.append([-b/2-self.overhang_x   ,    h/2+d/2])
        
        
        elif self.condition == "E":
            self.slabedge_lines.append([[b/2+self.overhang_x, -h/2-L-h*SLAB_EXTENT_FACTOR]   ,    [b/2+self.overhang_x, h/2+L+h*SLAB_EXTENT_FACTOR]])
            self.slabedge_pts.append([b/2+self.overhang_x, -h/2-L-h*SLAB_EXTENT_FACTOR])
            self.slabedge_pts.append([b/2+self.overhang_x, h/2+L+h*SLAB_EXTENT_FACTOR])
            self.slabedge_pts.append([-b/2-L-SLAB_EXTENT_FACTOR*b*1.5, h/2+L+h*SLAB_EXTENT_FACTOR])
            self.slabedge_pts.append([-b/2-L-SLAB_EXTENT_FACTOR*b*1.5, -h/2-L-h*SLAB_EXTENT_FACTOR])
            if self.has_studrail:
                self.perimeter_pts.append([b/2+self.overhang_x   ,    h/2+L+d/2])
                self.perimeter_pts.append([-b/2-d/2    ,    h/2+L+d/2]) #6
                self.perimeter_pts.append([-b/2-L-d/2  ,    h/2+d/2])   #7
                self.perimeter_pts.append([-b/2-L-d/2  ,    -h/2-d/2])  #8
                self.perimeter_pts.append([-b/2-d/2    ,   -h/2-L-d/2]) #1
                self.perimeter_pts.append([b/2+self.overhang_x   ,    -h/2-L-d/2])

                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2, h/2+L]]) #top
                self.studrail_pts.append([[b/2, h/2]    ,    [b/2, h/2+L]]) #top
                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2, -h/2-L]]) #bot
                self.studrail_pts.append([[b/2, -h/2]   ,    [b/2, -h/2-L]]) #bot
                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2-L, h/2]]) #left
                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2-L, -h/2]]) #left
            else:
                # based on CRSI design guide. If overhang exceeds h/2 + d, treat as interior condition
                if self.overhang_x > h/2 + d:
                    self.perimeter_pts.append([-b/2-d/2   ,   h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2   ,    h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,   h/2+d/2])
                else:
                    self.perimeter_pts.append([b/2+self.overhang_x   ,    h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+self.overhang_x   ,    -h/2-d/2])
        
        
        elif self.condition == "I":
            if self.has_studrail:
                self.perimeter_pts.append([-b/2-d/2    ,   -h/2-L-d/2]) #1
                self.perimeter_pts.append([b/2+d/2     ,   -h/2-L-d/2]) #2
                self.perimeter_pts.append([b/2+L+d/2   ,   -h/2-d/2])   #3
                self.perimeter_pts.append([b/2+L+d/2   ,    h/2+d/2])   #4
                self.perimeter_pts.append([b/2+d/2     ,    h/2+L+d/2]) #5
                self.perimeter_pts.append([-b/2-d/2    ,    h/2+L+d/2]) #6
                self.perimeter_pts.append([-b/2-L-d/2  ,    h/2+d/2])   #7
                self.perimeter_pts.append([-b/2-L-d/2  ,    -h/2-d/2])  #8
                self.perimeter_pts.append([-b/2-d/2    ,   -h/2-L-d/2]) #1
                
                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2, h/2+L]]) #top
                self.studrail_pts.append([[b/2, h/2]    ,    [b/2, h/2+L]]) #top
                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2, -h/2-L]]) #bot
                self.studrail_pts.append([[b/2, -h/2]   ,    [b/2, -h/2-L]]) #bot
                self.studrail_pts.append([[b/2, h/2]   ,    [b/2+L, h/2]]) #right
                self.studrail_pts.append([[b/2, -h/2]  ,    [b/2+L, -h/2]]) #right
                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2-L, h/2]]) #left
                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2-L, -h/2]]) #left
            else:
                self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2]) #2
                self.perimeter_pts.append([b/2+d/2    ,    h/2+d/2]) #3
                self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2]) #4
                self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
            
            
        elif self.condition == "NW":
            self.slabedge_lines.append([[-b/2-self.overhang_x, h/2+self.overhang_y]   ,  [b/2+L+SLAB_EXTENT_FACTOR*b, h/2+self.overhang_y]])
            self.slabedge_lines.append([[-b/2-self.overhang_x, h/2+self.overhang_y]   ,  [-b/2-self.overhang_x, -h/2-L-SLAB_EXTENT_FACTOR*h]])
            self.slabedge_pts.append([-b/2-self.overhang_x, h/2+self.overhang_y])
            self.slabedge_pts.append([b/2+L+SLAB_EXTENT_FACTOR*b, h/2+self.overhang_y])
            self.slabedge_pts.append([b/2+L+SLAB_EXTENT_FACTOR*b, -h/2-L-SLAB_EXTENT_FACTOR*h])
            self.slabedge_pts.append([-b/2-self.overhang_x, -h/2-L-SLAB_EXTENT_FACTOR*h])
            if self.has_studrail:
                self.perimeter_pts.append([-b/2-self.overhang_x   ,    -h/2-L-d/2])
                self.perimeter_pts.append([b/2+d/2     ,   -h/2-L-d/2]) #2
                self.perimeter_pts.append([b/2+L+d/2   ,   -h/2-d/2])   #3
                self.perimeter_pts.append([b/2+L+d/2   ,    h/2+self.overhang_y])

                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2, -h/2-L]]) #bot
                self.studrail_pts.append([[b/2, -h/2]   ,    [b/2, -h/2-L]]) #bot
                self.studrail_pts.append([[b/2, h/2]   ,    [b/2+L, h/2]]) #right
                self.studrail_pts.append([[b/2, -h/2]  ,    [b/2+L, -h/2]]) #right
            else:
                # based on CRSI design guide. If overhang exceeds h/2 + d, treat as interior condition
                if (self.overhang_x > h/2 + d) and (self.overhang_y > b/2 + d):
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2]) #2
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+d/2]) #3
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2]) #4
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                elif (self.overhang_x > h/2 + d):
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+self.overhang_y])
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2]) #2
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+self.overhang_y])
                elif (self.overhang_y > b/2 + d):
                    self.perimeter_pts.append([-b/2-self.overhang_x   ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2]) #2
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+d/2]) #3
                    self.perimeter_pts.append([-b/2-self.overhang_x   ,    h/2+d/2])
                else:
                    self.perimeter_pts.append([-b/2-self.overhang_x   ,    -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2                ,    -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2                ,     h/2+self.overhang_y])
        
        
        elif self.condition == "NE":
            self.slabedge_lines.append([[b/2+self.overhang_x, h/2+self.overhang_y]   ,  [-b/2-L-SLAB_EXTENT_FACTOR*b, h/2+self.overhang_y]])
            self.slabedge_lines.append([[b/2+self.overhang_x, h/2+self.overhang_y]   ,  [b/2+self.overhang_x, -h/2-L-SLAB_EXTENT_FACTOR*h]])
            self.slabedge_pts.append([b/2+self.overhang_x, h/2+self.overhang_y])
            self.slabedge_pts.append([-b/2-L-SLAB_EXTENT_FACTOR*b, h/2+self.overhang_y])
            self.slabedge_pts.append([-b/2-L-SLAB_EXTENT_FACTOR*b, -h/2-L-SLAB_EXTENT_FACTOR*h])
            self.slabedge_pts.append([b/2+self.overhang_x, -h/2-L-SLAB_EXTENT_FACTOR*h])
            if self.has_studrail:
                self.perimeter_pts.append([-b/2-L-d/2   ,    h/2+self.overhang_y])
                self.perimeter_pts.append([-b/2-L-d/2  ,    -h/2-d/2])  #8
                self.perimeter_pts.append([-b/2-d/2    ,   -h/2-L-d/2]) #1
                self.perimeter_pts.append([b/2+self.overhang_x   ,    -h/2-L-d/2])

                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2, -h/2-L]]) #bot
                self.studrail_pts.append([[b/2, -h/2]   ,    [b/2, -h/2-L]]) #bot
                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2-L, h/2]]) #left
                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2-L, -h/2]]) #left
            else:
                # based on CRSI design guide. If overhang exceeds h/2 + d, treat as interior condition
                if (self.overhang_x > h/2 + d) and (self.overhang_y > b/2 + d):
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2]) #2
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+d/2]) #3
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2]) #4
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                elif (self.overhang_x > h/2 + d):
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+self.overhang_y])
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2]) #2
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+self.overhang_y])
                elif (self.overhang_y > b/2 + d):
                    self.perimeter_pts.append([b/2+self.overhang_x   ,   h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2]) #4
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                    self.perimeter_pts.append([b/2+self.overhang_x   ,    -h/2-d/2])
                else:
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+self.overhang_y])
                    self.perimeter_pts.append([-b/2-d/2   ,    -h/2-d/2])
                    self.perimeter_pts.append([b/2+self.overhang_x   ,    -h/2-d/2])
        
        
        elif self.condition == "SW":
            self.slabedge_lines.append([[-b/2-self.overhang_x, -h/2-self.overhang_y]   ,  [b/2+L+SLAB_EXTENT_FACTOR*b, -h/2-self.overhang_y]])
            self.slabedge_lines.append([[-b/2-self.overhang_x, -h/2-self.overhang_y]   ,  [-b/2-self.overhang_x, h/2+L+SLAB_EXTENT_FACTOR*h]])
            self.slabedge_pts.append([-b/2-self.overhang_x, -h/2-self.overhang_y])
            self.slabedge_pts.append([b/2+L+SLAB_EXTENT_FACTOR*b, -h/2-self.overhang_y])
            self.slabedge_pts.append([b/2+L+SLAB_EXTENT_FACTOR*b, h/2+L+SLAB_EXTENT_FACTOR*h])
            self.slabedge_pts.append([-b/2-self.overhang_x, h/2+L+SLAB_EXTENT_FACTOR*h])
            if self.has_studrail:
                self.perimeter_pts.append([b/2+L+d/2   ,    -h/2-self.overhang_y])
                self.perimeter_pts.append([b/2+L+d/2   ,    h/2+d/2])   #4
                self.perimeter_pts.append([b/2+d/2     ,    h/2+L+d/2]) #5
                self.perimeter_pts.append([-b/2-self.overhang_x   ,    h/2+L+d/2])

                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2, h/2+L]]) #top
                self.studrail_pts.append([[b/2, h/2]    ,    [b/2, h/2+L]]) #top
                self.studrail_pts.append([[b/2, h/2]   ,    [b/2+L, h/2]]) #right
                self.studrail_pts.append([[b/2, -h/2]  ,    [b/2+L, -h/2]]) #right
            else:
                # based on CRSI design guide. If overhang exceeds h/2 + d, treat as interior condition
                if (self.overhang_x > h/2 + d) and (self.overhang_y > b/2 + d):
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2]) #2
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+d/2]) #3
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2]) #4
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                elif (self.overhang_x > h/2 + d):
                    self.perimeter_pts.append([b/2+d/2   ,     -h/2-self.overhang_y])
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+d/2]) #3
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2]) #4
                    self.perimeter_pts.append([-b/2-d/2    ,   -h/2-self.overhang_y])
                elif (self.overhang_y > b/2 + d):
                    self.perimeter_pts.append([-b/2-self.overhang_x   ,   -h/2-d/2])
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2]) #2
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+d/2]) #3
                    self.perimeter_pts.append([-b/2-self.overhang_x   ,    h/2+d/2])
                else:
                    self.perimeter_pts.append([b/2+d/2   ,    -h/2-self.overhang_y])
                    self.perimeter_pts.append([b/2+d/2                ,     h/2+d/2])
                    self.perimeter_pts.append([-b/2-self.overhang_x     ,     h/2+d/2])
        
        
        elif self.condition == "SE":
            self.slabedge_lines.append([[b/2+self.overhang_x, -h/2-self.overhang_y]   ,  [-b/2-L-SLAB_EXTENT_FACTOR*b, -h/2-self.overhang_y]])
            self.slabedge_lines.append([[b/2+self.overhang_x, -h/2-self.overhang_y]   ,  [b/2+self.overhang_x, h/2+L+SLAB_EXTENT_FACTOR*h]])
            self.slabedge_pts.append([b/2+self.overhang_x, -h/2-self.overhang_y])
            self.slabedge_pts.append([-b/2-L-SLAB_EXTENT_FACTOR*b, -h/2-self.overhang_y])
            self.slabedge_pts.append([-b/2-L-SLAB_EXTENT_FACTOR*b, h/2+L+SLAB_EXTENT_FACTOR*h])
            self.slabedge_pts.append([b/2+self.overhang_x, h/2+L+SLAB_EXTENT_FACTOR*h])
            if self.has_studrail:
                self.perimeter_pts.append([b/2+self.overhang_x   ,    h/2+L+d/2])
                self.perimeter_pts.append([-b/2-d/2    ,    h/2+L+d/2]) #6
                self.perimeter_pts.append([-b/2-L-d/2  ,    h/2+d/2])   #7
                self.perimeter_pts.append([-b/2-L-d/2   ,    -h/2-self.overhang_y])

                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2, h/2+L]]) #top
                self.studrail_pts.append([[b/2, h/2]    ,    [b/2, h/2+L]]) #top
                self.studrail_pts.append([[-b/2, h/2]   ,    [-b/2-L, h/2]]) #left
                self.studrail_pts.append([[-b/2, -h/2]  ,    [-b/2-L, -h/2]]) #left
            else:
                # based on CRSI design guide. If overhang exceeds h/2 + d, treat as interior condition
                if (self.overhang_x > h/2 + d) and (self.overhang_y > b/2 + d):
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                    self.perimeter_pts.append([b/2+d/2    ,   -h/2-d/2]) #2
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+d/2]) #3
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2]) #4
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                elif (self.overhang_x > h/2 + d):
                    self.perimeter_pts.append([b/2+d/2   ,     -h/2-self.overhang_y])
                    self.perimeter_pts.append([b/2+d/2    ,    h/2+d/2]) #3
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2]) #4
                    self.perimeter_pts.append([-b/2-d/2    ,   -h/2-self.overhang_y])
                elif (self.overhang_y > b/2 + d):
                    self.perimeter_pts.append([b/2+self.overhang_x   ,   h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2]) #4
                    self.perimeter_pts.append([-b/2-d/2   ,   -h/2-d/2]) #1
                    self.perimeter_pts.append([b/2+self.overhang_x   ,    -h/2-d/2])
                else:
                    self.perimeter_pts.append([b/2+self.overhang_x   ,    h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2   ,    h/2+d/2])
                    self.perimeter_pts.append([-b/2-d/2     ,     -h/2-self.overhang_y])
        
        
        else:
            raise RuntimeError('ERROR: condition must be one of "N", "S", "W", "E", "I", "NW", "NE", "SW", "SE"')
        
        # draw perimeter
        for i in range(len(self.perimeter_pts)-1):
            pt1 = self.perimeter_pts[i]
            pt2 = self.perimeter_pts[i+1]
            self.add_perimeter(pt1, pt2, self.slab_depth)
        
        
    def add_opening(self, dx, dy, width, height):
        """
        Add an opening nearby. Affected perimeter will automatically be removed.
        
        Arguments:
            dx              float:: x-offset from column center (0,0) to bottom left corner of opening
            dy              float:: y-offset from column center (0,0) to bottom left corner of opening
            width           float:: opening width
            height          float:: opening height
            
        Returns:
            None
        """
        # define opening pts for plotting
        opening_pts = [[dx, dy],
                       [dx+width, dy],
                       [dx+width, dy+height],
                       [dx, dy+height]]
        self.openings.append(opening_pts)
        
        
        # ACI recommends opening more than 4h away need not be considered. Allow user to add opening but provide warning.
        # first find closest point to column (out of the four that defines the opening)
        index_closest_pt = None
        min_distance = math.inf
        for i in range(len(opening_pts)):
            length = math.sqrt( (opening_pts[i][0]-0)**2   +  (opening_pts[i][1]-0)**2 )
            if length < min_distance:
                min_distance = length
                index_closest_pt = i
        pt2 = opening_pts[index_closest_pt]
        
        # now loop through every perimeter patch to find minimum distance
        h = (self.slab_depth + 2) # assume 2" cover
        min_length = math.inf
        for i in range(len(self.perimeter["x_centroid"])):
            x = self.perimeter["x_centroid"][i]
            y = self.perimeter["y_centroid"][i]
            pt1 = np.array([x,y])
            length = math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
            if length < min_length:
                min_length = length
        if min_length > 4*h:
            print("Opening is more than 4h away from column perimeter and may be ignored per ACI 318")
    
    
        # to determine which portion of perimeter to remove. Convert to radial coordinate and calculate acceptable theta range
        thetas = []
        for pt in opening_pts:
            thetas.append(math.atan2(pt[1], pt[0])) # returns within -pi to +pi rad
        theta_min = min(thetas)
        theta_max = max(thetas)
        min_idx = thetas.index(theta_min)
        max_idx = thetas.index(theta_max)
        self.openings_draw_pts.append([opening_pts[min_idx],opening_pts[max_idx]])
        
        # delete perimeter patches within theta range
        delete_idx = []
        for i in range(len(self.perimeter["x_centroid"])):
            x = self.perimeter["x_centroid"][i]
            y = self.perimeter["y_centroid"][i]
            theta = math.atan2(y, x)
            if theta_min < theta and theta < theta_max:
                delete_idx.append(i)
        
        # delete from largest index first to prevent shifting
        delete_idx.reverse()
        for idx in delete_idx:
            del self.perimeter["x_centroid"][idx]
            del self.perimeter["y_centroid"][idx]
            del self.perimeter["x_start"][idx]
            del self.perimeter["y_start"][idx]
            del self.perimeter["x_end"][idx]
            del self.perimeter["y_end"][idx]
            del self.perimeter["depth"][idx]
            del self.perimeter["length"][idx]
            del self.perimeter["area"][idx]
    
    
    def rotate(self, angle):
        """rotate all objects by a user-specified angle in DEGREES counter-clockwise"""
        # rotation matrix
        rotation_rad = angle * math.pi / 180
        T = np.array([
            [math.cos(rotation_rad), -math.sin(rotation_rad)],
            [math.sin(rotation_rad), math.cos(rotation_rad)]
            ])
        
        # rotate shear perimeter patches
        x_centroid_new = []
        y_centroid_new = []
        x_start_new = []
        x_end_new = []
        y_start_new = []
        y_end_new = []
        for i in range(len(self.perimeter["x_centroid"])):
            center = np.array([self.perimeter["x_centroid"][i], self.perimeter["y_centroid"][i]])
            start = np.array([self.perimeter["x_start"][i], self.perimeter["y_start"][i]])
            end = np.array([self.perimeter["x_end"][i], self.perimeter["y_end"][i]])
            center_r = T @ center
            start_r = T @ start
            end_r = T @ end
            x_centroid_new.append(center_r[0])
            y_centroid_new.append(center_r[1])
            x_start_new.append(start_r[0])
            x_end_new.append(end_r[0])
            y_start_new.append(start_r[1])
            y_end_new.append(end_r[1])
        self.perimeter["x_centroid"] = x_centroid_new
        self.perimeter["y_centroid"] = y_centroid_new
        self.perimeter["x_start"] = x_start_new
        self.perimeter["y_start"] = y_start_new
        self.perimeter["x_end"] = x_end_new
        self.perimeter["y_end"] = y_end_new
        
        # rotate openings
        openings_t = []
        for opening in self.openings:
            inner_list = []
            for i in range(4):
                pt_t = T @ np.array(opening[i])
                inner_list.append(pt_t)
            openings_t.append(inner_list)
        self.openings = openings_t
        
        # rotate openings effective line
        openings_draw_pts_t = []
        for draw_pts in self.openings_draw_pts:
            inner_list = []
            for i in range(2):
                pt_t = T @ np.array(draw_pts[i])
                inner_list.append(pt_t)
            openings_draw_pts_t.append(inner_list)
        self.openings_draw_pts = openings_draw_pts_t
         
        # rotate studrails
        studrail_pts_t = []
        for studrail in self.studrail_pts:
            inner_list = []
            for i in range(2):
                pt_t = T @ np.array(studrail[i])
                inner_list.append(pt_t)
            studrail_pts_t.append(inner_list)
        self.studrail_pts = studrail_pts_t
        
        # rotate columns
        col_pts_t = []
        for pt in self.col_pts:
            pt_t = T @ np.array(pt)
            col_pts_t.append(pt_t)
        self.col_pts = col_pts_t
        
        # rotate slab extent
        slabedge_pts_t = []    
        for pt in self.slabedge_pts:
            pt_t = T @ np.array(pt)
            slabedge_pts_t.append(pt_t)
        self.slabedge_pts = slabedge_pts_t
        
        # rotate slab extent lines
        slabedge_lines_t = []
        for slabedge in self.slabedge_lines:
            slabedge_lines_t2 = []
            for i in range(2):
                pt_t = T @ np.array(slabedge[i])
                slabedge_lines_t2.append(pt_t)
            slabedge_lines_t.append(slabedge_lines_t2)
        self.slabedge_lines = slabedge_lines_t
        
        # re-calculate geometric properties
        self.update_properties() 
    
    
    def update_properties(self):
        """
        Calculate geometric properties of the punching shear section. This is a private method called by solve() or preview() or rotate().
        """
        # calculate total perimeter
        self.L = sum(self.perimeter["length"])
        
        # calculate effective perimeter (normalized by min slab depth)
        d_min = min(self.perimeter["depth"])
        modified_length = [d/d_min * L for d,L in zip(self.perimeter["depth"], self.perimeter["length"])]
        self.perimeter["length_effective"] = modified_length
        self.Le = sum(self.perimeter["length_effective"])
        
        # centroid
        xA = sum([x*A for x,A in zip(self.perimeter["x_centroid"],self.perimeter["area"])])
        yA = sum([y*A for y,A in zip(self.perimeter["y_centroid"],self.perimeter["area"])])
        self.A = sum(self.perimeter["area"])
        self.x_centroid = xA / self.A
        self.y_centroid = yA / self.A
        
        # moment of inertia
        self.Ix = sum([ A * (y - self.y_centroid)**2 for y,A in zip(self.perimeter["y_centroid"],self.perimeter["area"]) ])
        self.Iy = sum([ A * (x - self.x_centroid)**2 for x,A in zip(self.perimeter["x_centroid"],self.perimeter["area"]) ])
        self.Ixy = sum([ A * (y - self.y_centroid) * (x - self.x_centroid) for x,y,A in zip(self.perimeter["x_centroid"],self.perimeter["y_centroid"],self.perimeter["area"]) ])
        self.Iz = self.Ix + self.Iy
        
        # section modulus
        all_x = self.perimeter["x_centroid"] + self.perimeter["x_start"] + self.perimeter["x_end"]
        all_y = self.perimeter["y_centroid"] + self.perimeter["y_start"] + self.perimeter["y_end"]
        self.Sx1 = self.Ix / abs(max(all_y) - self.y_centroid)
        self.Sx2 = self.Ix / abs(min(all_y) - self.y_centroid)
        self.Sy1 = self.Iy / abs(max(all_x) - self.x_centroid)
        self.Sy2 = self.Iy / abs(min(all_x) - self.x_centroid)
        
        # principal axes via Mohr's circle
        if self.Ix == self.Iy:
            self.theta_p = 0
        else:
            self.theta_p = (  math.atan((self.Ixy)/((self.Ix-self.Iy)/2)) / 2) * 180 / math.pi
    
    
    def preview(self):
        """
        preview punching shear perimeter. Returns a matplotlib figure.
        """
        # update geometric property
        self.update_properties()
        
        # check if perimeter is in its principal axes
        if abs(self.theta_p) > 0.1:
            print("WARNING: GEOMETRY IS NOT IN PRINCIPAL ORIENTATION!")
            print("Please rotate geometry by {:.1f} degrees using the .rotate() method".format(self.theta_p))
        
        # initialize figure
        fig, axs = plt.subplots(1,2, figsize=(11,8.5), gridspec_kw={"width_ratios":[2,3]})
        
        # plot column
        pt1 = self.col_pts[0]
        pt2 = self.col_pts[1]
        pt3 = self.col_pts[2]
        pt4 = self.col_pts[3]
        vertices = [pt1, pt2, pt3, pt4, pt1]
        axs[1].add_patch(patches.Polygon(np.array(vertices), closed=True, facecolor="darkgrey",
                                      alpha=0.8, edgecolor="black", zorder=2, lw=1.5))
        
        # plot studrails
        if len(self.studrail_pts) != 0:
            for i in range(len(self.studrail_pts)):
                pt1 = self.studrail_pts[i][0]
                pt2 = self.studrail_pts[i][1]
                axs[1].plot([pt1[0], pt2[0]], [pt1[1], pt2[1]], marker="none", c="black", zorder=2, linestyle="-", lw=3)
        
        
        # plot slab edge
        if self.condition == "I":
            axs[1].set_facecolor((0.77, 0.77, 0.77, 0.45))
        else:
            if len(self.slabedge_lines) != 0:
                for i in range(len(self.slabedge_lines)):
                    pt1 = self.slabedge_lines[i][0]
                    pt2 = self.slabedge_lines[i][1]
                    axs[1].plot([pt1[0], pt2[0]], [pt1[1], pt2[1]], marker="none", c="black", zorder=2, linestyle="-")
            if len(self.slabedge_pts) != 0:
                pt1 = np.array(self.slabedge_pts[0])
                pt2 = np.array(self.slabedge_pts[1])
                pt3 = np.array(self.slabedge_pts[2])
                pt4 = np.array(self.slabedge_pts[3])
                vertices = [pt1, pt2, pt3, pt4, pt1]
                axs[1].add_patch(patches.Polygon(np.array(vertices), closed=True, facecolor=(0.77, 0.77, 0.77, 0.45),
                                              alpha=0.45, edgecolor=(0.77, 0.77, 0.77, 0.45), zorder=1, lw=2, linestyle="--"))
        
        
        # plot opening
        if len(self.openings) != 0:
            for i in range(len(self.openings)):
                pt1 = np.array(self.openings[i][0])
                pt2 = np.array(self.openings[i][1])
                pt3 = np.array(self.openings[i][2])
                pt4 = np.array(self.openings[i][3])
                vertices = [pt1, pt2, pt3, pt4, pt1]
                axs[1].add_patch(patches.Polygon(np.array(vertices), closed=True, facecolor="white",
                                              alpha=1, edgecolor="darkred", zorder=3, lw=2))
                axs[1].plot([pt1[0], pt3[0]], [pt1[1], pt3[1]], marker="none", c="darkred", zorder=3, linestyle="-")
                axs[1].plot([pt2[0], pt4[0]], [pt2[1], pt4[1]], marker="none", c="darkred", zorder=3, linestyle="-")
                axs[1].plot([0,self.openings_draw_pts[i][0][0]], 
                            [0,self.openings_draw_pts[i][0][1]], 
                            marker="none", c="darkred", zorder=3, linestyle="--", lw=1)
                axs[1].plot([0,self.openings_draw_pts[i][1][0]], 
                            [0,self.openings_draw_pts[i][1][1]], 
                            marker="none", c="darkred", zorder=3, linestyle="--", lw=1)
        
        # plot x-y principal axes
        ordinate = 0.4*max(self.width, self.height)
        axs[1].annotate("",
                        xy=(self.x_centroid+ordinate, self.y_centroid), 
                        xytext=(self.x_centroid, self.y_centroid),
                        color="black",
                        arrowprops=dict(arrowstyle="simple,head_length=0.4,head_width=0.30,tail_width=0.06",
                                            fc="darkblue", ec="darkblue"))
        axs[1].annotate("",
                        xy=(self.x_centroid, self.y_centroid+ordinate), 
                        xytext=(self.x_centroid, self.y_centroid),
                        color="black",
                        arrowprops=dict(arrowstyle="simple,head_length=0.4,head_width=0.30,tail_width=0.06",
                                            fc="darkblue", ec="darkblue"))
        axs[1].annotate("X'",
                        xy=(self.x_centroid, self.y_centroid), 
                        xytext=(self.x_centroid+1.2*ordinate, self.y_centroid),
                        va="center",
                        ha="center",
                        color="darkblue")
        axs[1].annotate("Y'",
                        xy=(self.x_centroid, self.y_centroid), 
                        xytext=(self.x_centroid, self.y_centroid+1.2*ordinate),
                        va="center",
                        ha="center",
                        color="darkblue")
        
        # plot Cog
        axs[1].plot(self.x_centroid, self.y_centroid, marker="x", c="darkblue",markersize=6, zorder=3, linestyle="none")
        
        # plot perimeter mesh with polygon patches
        DEFAULT_THICKNESS = 1  # for display
        t_min = min(self.perimeter["depth"])
        line_thicknesses = [t/t_min * DEFAULT_THICKNESS for t in self.perimeter["depth"]]
        for i in range(len(self.perimeter["x_start"])):
            x0 = self.perimeter["x_start"][i]
            x1 = self.perimeter["x_end"][i]
            y0 = self.perimeter["y_start"][i]
            y1 = self.perimeter["y_end"][i]
            
            # calculate perpendicular direction vector to offset by thickness
            u = np.array([x1,y1]) - np.array([x0,y0])
            u_unit = u / np.linalg.norm(u)
            v_unit = np.array([u_unit[1], -u_unit[0]])
            
            # plot using polygon patches
            pt1 = np.array([x0, y0]) + v_unit * line_thicknesses[i]
            pt2 = np.array([x0, y0]) - v_unit * line_thicknesses[i]
            pt3 = np.array([x1, y1]) - v_unit * line_thicknesses[i]
            pt4 = np.array([x1, y1]) + v_unit * line_thicknesses[i]
            vertices = [pt1, pt2, pt3, pt4, pt1]
            axs[1].add_patch(patches.Polygon(np.array(vertices), closed=True, facecolor="blue",
                                          alpha=0.4, edgecolor="darkblue", zorder=1, lw=0.5))
            
        # annotation for perimeter geometric properties
        xo = 0.12
        yo = 0.90
        dy = 0.045
        unit = "in"
        axs[0].annotate("Centroid", 
                        (xo-0.03,yo), fontweight="bold",xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$x_{{cg}} = {:.1f} \quad {}$".format(self.x_centroid, unit), 
                        (xo,yo-dy*1), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$y_{{cg}} = {:.1f} \quad {}$".format(self.y_centroid, unit), 
                        (xo,yo-dy*2), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        
        axs[0].annotate("Moment of Inertias", 
                        (xo-0.03,yo-dy*3), fontweight="bold",xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$J_x = {:,.0f} \quad {}^3$".format(self.Ix, unit), 
                        (xo,yo-dy*4), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$J_y = {:,.0f} \quad {}^3$".format(self.Iy, unit), 
                        (xo,yo-dy*5), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        
        axs[0].annotate("Shear Perimeter", 
                        (xo-0.03,yo-dy*6), fontweight="bold",xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$L = {:.1f} \quad {}$".format(self.L, unit), 
                        (xo,yo-dy*7), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        
        axs[0].annotate("Section Modulus", 
                        (xo-0.03,yo-dy*8), fontweight="bold",xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{x,top}} = {:,.0f} \quad {}^2$".format(self.Sx1, unit), 
                        (xo,yo-dy*9), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{x,bottom}} = {:,.0f} \quad {}^2$".format(self.Sx2, unit), 
                        (xo,yo-dy*10), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{y,right}} = {:,.0f} \quad {}^2$".format(self.Sy1, unit), 
                        (xo,yo-dy*11), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{y,left}} = {:,.0f} \quad {}^2$".format(self.Sy2, unit), 
                        (xo,yo-dy*12), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        
        axs[0].annotate("Principal Orientation Angle", 
                        (xo-0.03,yo-dy*13), fontweight="bold",xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$\theta_{{p}} = {:.1f} \quad deg$".format(self.theta_p), 
                        (xo,yo-dy*14), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        if abs(self.theta_p) > 0.1:
            axs[0].annotate("WARNING: Not in principal orientation.", 
                            (xo,yo-dy*15), color="darkred", xycoords='axes fraction', fontsize=12, va="top", ha="left", wrap=True)

        # styling
        axs[1].set_aspect('equal', 'datalim')
        fig.suptitle("Punching Shear Perimeter", fontweight="bold", fontsize=16)
        axs[1].set_axisbelow(True)
        axs[0].set_xticks([])
        axs[0].set_yticks([])
        axs[1].grid(linestyle='--')
        plt.tight_layout()
    

    def solve(self, P, Mx, My, gamma_v, auto_adjust_ecc=False):
        """
        Run punching shear stress analysis.
        
        Arguments:
            P                   float:: applied shear force (Always positive. Always downwards in gravity direction)
            Mx                  float:: applied moment about X-axis
            My                  float:: applied moment about Y-axis
            gamma_v             float:: percentage of applied unbalanced moment transferred via shear. Usually around 40%.
                                        In ACI 318-19, gamma_v is calculated as:
                                                b1 = column dimension parallel to span
                                                b2 = column dimension perpendicular to span
                                                gamma_f = 1 + (2/3)*sqrt(b1/b2)
                                                gamma_v = 1 - 1 / gamma_f
                                        ACI 421.1R-20 has more guidance for gamma_v for perimeters with studrails
            auto_adjust_ecc     (OPTIONAL) bool:: modify moment based on eccentricity between column centroid and perimeter centroid. 
            
        Important note about auto_adjust_ecc and governing moment:
            
        Returns:
            df_perimeter        dataframe:: calculation summary table
        """
        pass
    
    def check_equilibrium(self):
        pass
    
    def plot_results(self):
        pass
    
    
    
    
    
    
    def preview_3D(self):
        pass
    
    def plot_results_3D(self):
        pass




