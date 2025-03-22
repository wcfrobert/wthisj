import time
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
    PunchingShearSection objects are numerical representation of a critical punching 
    shear perimeter around a column in a concrete flat slab floor system.
    
    Args:
        col_width (float):
            Column dimension along x
            
        col_depth (float):
            Column dimension along y
            
        slab_avg_depth (float):
            Slab depth from outermost compression fiber to outer-most tension rebar. 
            Use the average depth of the two orthogonal slab directions.
            
        condition (str):
            Specify interior, edge, or corner condition. Valid inputs looks like cardinal directions on a compass.
                "NW"     "N"     "NE"
                "W"      "I"     "E"
                "SW"     "S"     "SE"   
            for example, "SE" is a corner condition with slab edge below and to the right.  
            
        (OPTIONAL) overhang_x = 0 (float):
            Slab overhang dimension along x beyond column face. Default = 0.
            
        (OPTIONAL) overhang_y = 0 (float):
            Slab overhang dimension along y beyond column face. Default = 0.
            
        (OPTIONAL) studrail_length = 0 (float):
            Stud rail length if applicable. default = 0.
            
        (OPTIONAL) auto_generate_perimeter = True (bool):
            Auto-generate punching shear perimeter based on the other inputs. Default = True.
            Alternatively, the user may draw the perimeters manually using .add_perimeter().
            
        (OPTIONAL) PATCH_SIZE = 0.5 (float):
            Specify how fine to discretize the perimeter. Default = 0.2 inches
    
    Public Methods:
        PunchingShearSection.add_perimeter()
        PunchingShearSection.add_opening()
        PunchingShearSection.rotate()
        PunchingShearSection.preview()
        PunchingShearSection.solve()
        PunchingShearSection.plot_results()
        PunchingShearSection.plot_results_3D()
    """
    def __init__(self, col_width, col_depth, slab_avg_depth, condition, 
                 overhang_x=0, overhang_y=0, studrail_length=0, auto_generate_perimeter=True,
                 PATCH_SIZE=0.5):
        # input arguments. See descriptions in docstring above.
        self.width = col_width
        self.height = col_depth
        self.slab_depth = slab_avg_depth
        self.condition = condition
        self.overhang_x = overhang_x
        self.overhang_y = overhang_y
        self.L_studrail = studrail_length
        self.generate_perimeter = auto_generate_perimeter
        self.PATCH_SIZE = PATCH_SIZE
        
        # parameter related to geometry
        self.perimeter_pts = []                         # list of pts to generate perimeter using auto_generate_perimeters()
        self.openings = []                              # list of openings, each opening is a list of 4 pts
        
        # parameter related to geometry (plotting only)
        self.studrail_pts = []                          # list of pts to plot studrails
        self.slabedge_lines = []                        # list of lines to plot slab edge. Each line is two points
        self.slabedge_pts = []                          # list of pts to plot slab shading
        self.openings_draw_pts = []                     # list of pts in each opening used to draw theta_min and max dotted lines
        self.col_pts = [np.array([-self.width/2, -self.height/2]),      # list of pts to plot column
                        np.array([self.width/2, -self.height/2]),
                        np.array([self.width/2, self.height/2]),
                        np.array([-self.width/2, self.height/2])]                                               
        
        # geometric properties
        self.x_centroid = None                          # centroid x
        self.y_centroid = None                          # centroid y
        self.L = None                                   # total perimeter length
        self.A = None                                   # total area of welds
        self.Ix = None                                  # moment of inertia X
        self.Iy = None                                  # moment of inertia Y
        self.Iz = None                                  # polar moment of inertia = Ix + Iy
        self.Ixy = None                                 # product moment of inertia
        self.theta_p = None                             # angle offset to principal axis in degrees
        self.Sx1 = None                                 # elastic modulus top fiber
        self.Sx2 = None                                 # elastic modulus bottom fiber
        self.Sy1 = None                                 # elastic modulus right fiber
        self.Sy2 = None                                 # elastic modulus left fiber
        
        # applied forces
        self.P = None                                   # applied axial force (we will assume always downwards. Apply abs())
        self.Mx = None                                  # applied moment about X
        self.My = None                                  # applied moment about Y
        self.Pex = None                                 # additional X moment due to eccentricity
        self.Pey = None                                 # additional Y moment due to eccentricity
        self.gamma_vx = None                            # percentage of X unbalanced moment transferred through eccentric shear
        self.gamma_vy = None                            # percentage of Y unbalanced moment transferred through eccentric shear
        self.Mx_final = None                            # final governing moment in x-direction = gamma_v*(Mx + Pey)
        self.My_final = None                            # final governing moment in y-direction = gamma_v*(My + Pex)
        
        # other parameters
        self.has_studrail = False if self.L_studrail==0 else True       # bool for if studrail exists
        self.equilibrium_check_passed = None                            # bool for if equilibrium check passed or not
        self.v_max = None                                               # maximum calculated shear stress
        
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
                           "v_total": [],               # total shear stress is the summation of the above three components
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
        # convert into numpy arrays
        start = np.array(start)
        end = np.array(end)
        position_vector = end-start
        
        # calculate number of segments
        length_line = np.linalg.norm(position_vector)
        segments = int(length_line // self.PATCH_SIZE) if length_line > self.PATCH_SIZE else 1
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
        
        
    def add_opening(self, xo, yo, width, depth):
        """
        Add an opening by specifying the x,y coordinate of the bottom left corner, as well as
        an opening size. Please note the column centroid is always at (0,0). 
        
        Affected perimeter will automatically be removed from the section. A warning will be printed
        to console if the opening is more than 4h away.
        
        Arguments:
            xo              float:: x coordinate to bottom left corner of opening
            yo              float:: y coordinate to bottom left corner of opening
            width           float:: opening width (x-dimension)
            depth           float:: opening depth (y-dimension)
            
        Returns:
            None
        """
        # define opening pts for plotting
        opening_pts = [[xo, yo],
                       [xo+width, yo],
                       [xo+width, yo+depth],
                       [xo, yo+depth]]
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
        """
        Rotate all objects by a user-specified angle.
        
        Args:
            angle           float:: rotate geometry by a specified DEGREE measured counter clockwise from the +x axis.
            
        Returns:
            None
        """
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
        Calculate geometric properties of the shear section. 
        This is a private method called by solve() or preview() or rotate().
        """
        # calculate total perimeter
        self.L = sum(self.perimeter["length"])
        
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
        if math.isclose(self.Ixy, 0, abs_tol=1e-6):
            self.theta_p = 0
        else:
            if math.isclose(self.Ix, self.Iy, abs_tol=1e-6):
                self.theta_p = 45
            else:
                self.theta_p = (  math.atan((self.Ixy)/((self.Ix-self.Iy)/2)) / 2) * 180 / math.pi
    
    
    def preview(self):
        """
        Preview punching shear perimeter. Returns a matplotlib figure.
        """
        # update geometric property
        self.update_properties()
        
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
        axs[1].annotate("X",
                        xy=(self.x_centroid, self.y_centroid), 
                        xytext=(self.x_centroid+1.2*ordinate, self.y_centroid),
                        va="center",
                        ha="center",
                        color="darkblue")
        axs[1].annotate("Y",
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
                                          alpha=0.4, edgecolor="darkblue", zorder=1, lw=0.1))
            
        # annotation for perimeter geometric properties
        xo = 0.12
        yo = 0.95
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
        axs[0].annotate(r"$I_x = {:,.0f} \quad {}^4$".format(self.Ix, unit), 
                        (xo,yo-dy*4), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$I_y = {:,.0f} \quad {}^4$".format(self.Iy, unit), 
                        (xo,yo-dy*5), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        
        axs[0].annotate("Shear Perimeter and Area", 
                        (xo-0.03,yo-dy*6), fontweight="bold",xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$L = {:.1f} \quad {}$".format(self.L, unit), 
                        (xo,yo-dy*7), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$A = {:.1f} \quad {}^2$".format(self.A, unit), 
                        (xo,yo-dy*8), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        
        axs[0].annotate("Section Modulus", 
                        (xo-0.03,yo-dy*9), fontweight="bold",xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{x,top}} = {:,.0f} \quad {}^3$".format(self.Sx1, unit), 
                        (xo,yo-dy*10), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{x,bottom}} = {:,.0f} \quad {}^3$".format(self.Sx2, unit), 
                        (xo,yo-dy*11), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{y,right}} = {:,.0f} \quad {}^3$".format(self.Sy1, unit), 
                        (xo,yo-dy*12), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{y,left}} = {:,.0f} \quad {}^3$".format(self.Sy2, unit), 
                        (xo,yo-dy*13), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        
        axs[0].annotate("Principal Orientation Angle", 
                        (xo-0.03,yo-dy*14), fontweight="bold",xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$\theta_{{p}} = {:.1f} \quad deg$".format(self.theta_p), 
                        (xo,yo-dy*15), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        if abs(self.theta_p) > 0.1:
            axs[0].annotate("WARNING: Section is not in principal orientation.", 
                            (xo-0.03,yo-dy*16), color="darkred", xycoords='axes fraction', fontsize=12, va="top", ha="left", wrap=True)

        # styling
        axs[1].set_aspect('equal', 'datalim')
        fig.suptitle("Punching Shear Perimeter Properties", fontweight="bold", fontsize=16)
        axs[1].set_axisbelow(True)
        axs[0].set_xticks([])
        axs[0].set_yticks([])
        axs[1].grid(linestyle='--')
        plt.tight_layout()
    

    def solve(self, P, Mx, My, gamma_vx="auto", gamma_vy="auto", 
              consider_Pe=True, auto_rotate=True, verbose=True):
        """
        Calculate shear stress at every point along the column perimeter. (ALL UNIT IN KIP, IN)
        
        Args:
            P (float): 
                Applied shear force in KIPS. Should be negative unless you are checking uplift
                
            Mx (float): 
                Applied moment about the X-axis in KIP.IN.
                
            My (float): 
                Applied moment about the Y-axis in KIP.IN.
                
            (OPTIONAL) gamma_vx = "auto" (str or float): 
                Percentage of X moment transferred to the column via shear. By default,
                wthisj automatically calculates this. Alternatively, the user may 
                enter a specific value of gamma_v (e.g. 0.4)
                
            (OPTIONAL) gamma_vy = "auto" (str or float): 
                Percentage of Y moment transferred to the column via shear. By default,
                wthisj automatically calculates this. Alternatively, the user may 
                enter a specific value of gamma_v (e.g. 0.4)
                
            (OPTIONAL) consider_Pe = True (bool): 
                Boolean to consider additional moment due to eccentricity between 
                the column centroid and perimeter centroid. Defaults to True.
            
            (OPTIONAL) auto_rotate = True (bool):
                Boolean to auto-rotate geometry if it is not in principal orientation.
            
            (OPTIONAL) verbose = True (bool):
                Boolean to print out calculations step by step.
                
        Returns:
            df_perimeter (dataframe): 
                Calculation summary table. Each row is a patch of the perimeter.
            
            
        Notes about applied moment:
            The user-specified moment (Mx, My) goes through several rounds of adjustment and may
            not be what the user expects. These rounds are explained more in-depth below.
                1. Rotate moment vector to principal orientation if necessary (i.e. theta_p != 0)
                        (Mx', My')
                2. Additional moment due to eccentricity between column centroid and perimeter centroid
                        (Mx'+Pey , My'+Pex)
                3. Only a fixed % of moment is transferred through shear (gamma_v)
                        (gamma_v*(Mx'+Pey) , gamma_v*(My'+Pex))
            
        (1) Auto rotation to principal orientation:
            The elastic method takes advantage of principle of superposition. In practice, this means
            we can calculate stress due to P/A, then M/S in both directions, then add (superimpose) them
            at the end. However, superposition is NOT valid for asymmetric sections not in its principal
            orientation. This is described in detail in any mechanics of material textbooks. We know a
            section is in its principal orientation if the product of inertia (Ixy) is equal to zero.
            
        
        (2) Additional moment due to Pe:
            Most engineers obtain the applied shear (P) and unbalanced moment (Mx, My) using FEM software that
            reports column reactions. The problem is the column centroid does NOT coincide with the perimeter
            centroid in edge/corner conditions. I am not convinced anyone actually does this adjustment in practice,
            but it is described in detail in ACI 421.1R-20 and I think it makes sense.
            
        
        (3) Notes about gamma_v:
            Unbalanced moment in the slab is transferred to the supporting columns in two ways:
                1. Flexure within a slab "transfer width" (GAMMA_F)
                2. Eccentric Shear (GAMMA_V)
            GAMMA_F and GAMMA_V should add up to 100%. The user can specify a gamma_v value themselves. 
            Alternatively, if gamma_v is set to "auto", it is calculated internally. For more information 
            about how these are calculated, refer to ACI 318-19 and ACI 421.1R-20. 
            
            The fundamental equation is: gamma_v = 1 - 1 / (1 + (2/3)*sqrt(b1/b2)), where b1 is perimeter
            dimension perpendicular to moment vector (i.e. along the span), and b2 is perimeter dimension 
            parallel to moment vector. All gamma_v values are calculated with respect to the original 
            unrotated geometry, except the condition of corner columns with studrails.
                Let:
                    lx = max(xi) - min(xi)
                    ly = max(yi) - min(yi)
                
                For the columns without studrails:
                    gamma_vx = 1 - 1 / (1 + (2/3)*sqrt(ly/lx))
                    gamma_vy = 1 - 1 / (1 + (2/3)*sqrt(lx/ly))
                
                For column WITH studrails:
                    Interior condition (I)
                        gamma_vx = 1 - 1 / (1 + (2/3)*sqrt(ly/lx))
                        gamma_vy = 1 - 1 / (1 + (2/3)*sqrt(lx/ly))
                        
                    Edge condition (N, S)
                        gamma_vx = 1 - 1 / (1 + (2/3)*sqrt(ly/lx - 0.2))
                        gamma_vy = 1 - 1 / (1 + (2/3)*sqrt(lx/ly))
                        
                    Edge condition (W, E)
                        gamma_vx = 1 - 1 / (1 + (2/3)*sqrt(ly/lx))
                        gamma_vy = 1 - 1 / (1 + (2/3)*sqrt(lx/ly - 0.2))
                    
                    Corner conditions (NW, NE, SW, SE) - gamma_v caculated in principal orientation
                        gamma_vx = 0.4
                        gamma_vy = 1 - 1 / (1 + (2/3)*sqrt(lx/ly - 0.2))
                        Assuming moment vector Mx points at or away from the column, otherwise flip gamma_vx and gamma_vy
                    
                For custom-defined perimeters:
                    User must provide gamma_v themselves. Program will terminate with a warning if none is provided.
        """
        time_start = time.time()
        
        # update property before analysis
        self.update_properties()
    
        # if perimeter is defined by user, gamma_v must be specified explicitly
        did_not_auto_generate_perimeter = not self.generate_perimeter
        did_not_specify_gamma_v = gamma_vx == "auto" or gamma_vy == "auto"
        if did_not_auto_generate_perimeter and did_not_specify_gamma_v:
            raise RuntimeError("WARNING: Custom perimeter detected. Cannot calculate gamma_v automatically. Please provide it")
        
        # warning if P is positive
        if P > 0:
            print("WARNING: P is positive indicating uplift.")
        
        # calculate gamma_v
        lx = max([xi for xi in self.perimeter["x_centroid"]]) - min([xi for xi in self.perimeter["x_centroid"]])
        ly = max([yi for yi in self.perimeter["y_centroid"]]) - min([yi for yi in self.perimeter["y_centroid"]])
        if self.has_studrail:
            if self.condition == "I":
                g_vx = 1 - (1 / (1 + (2/3)*math.sqrt(ly/lx)))
                g_vy = 1 - (1 / (1 + (2/3)*math.sqrt(lx/ly)))
            elif self.condition == "N" or self.condition == "S":
                g_vx = 1 - (1 / (1 + (2/3)*math.sqrt(ly/lx) - 0.2)) if ly/lx > 0.2 else 0
                g_vy = 1 - (1 / (1 + (2/3)*math.sqrt(lx/ly)))
            elif self.condition == "W" or self.condition == "E":
                g_vx = 1 - (1 / (1 + (2/3)*math.sqrt(ly/lx)))
                g_vy = 1 - (1 / (1 + (2/3)*math.sqrt(lx/ly) - 0.2)) if lx/ly > 0.2 else 0
            else:
                # for corner condition, we will calculate gamma_v after rotation
                pass 
        else:
            g_vx = 1 - (1 / (1 + (2/3)*math.sqrt(ly/lx)))
            g_vy = 1 - (1 / (1 + (2/3)*math.sqrt(lx/ly)))
        
        # rotate geometry and applied moment if not about principal orientation
        required_rotation = self.theta_p
        if abs(required_rotation) > 0.1:
            if auto_rotate:
                self.rotate(required_rotation)
                M_vec = np.array([Mx, My])
                T = np.array([
                    [math.cos(required_rotation*math.pi/180), -math.sin(required_rotation*math.pi/180)],
                    [math.sin(required_rotation*math.pi/180), math.cos(required_rotation*math.pi/180)]
                    ])
                M_vec_rotated = T @ M_vec
                Mx = M_vec_rotated[0]
                My = M_vec_rotated[1]
                
        # update property again after rotation
        self.update_properties()
        
        # for corner condition, gamma_v is calculated in the rotated principal orientation
        if self.has_studrail:
            if self.condition == "NW" or self.condition == "NE" or self.condition == "SW" or self.condition == "SE":
                lx = max([xi for xi in self.perimeter["x_centroid"]]) - min([xi for xi in self.perimeter["x_centroid"]])
                ly = max([yi for yi in self.perimeter["y_centroid"]]) - min([yi for yi in self.perimeter["y_centroid"]])
                if ly > lx:
                    g_vx = 0.4
                    g_vy = 1 - (1 / (1 + (2/3)*math.sqrt(lx/ly) - 0.2)) if lx/ly > 0.2 else 0
                else:
                    g_vx = 1 - (1 / (1 + (2/3)*math.sqrt(ly/lx) - 0.2)) if ly/lx > 0.2 else 0
                    g_vy = 0.4
        
        # do not use the calculated gamma_v value above if user provided their own
        self.gamma_vx = g_vx if gamma_vx=="auto" else gamma_vx
        self.gamma_vy = g_vy if gamma_vy=="auto" else gamma_vy
        
        # calculate Pe moment if applicable
        if consider_Pe:
            Pex = P * self.x_centroid
            Pey = - P * self.y_centroid # i think there is a right-hand rule flip here
        else:
            Pex = 0
            Pey = 0
            
        # calculate and store final applied forces
        self.Mx_final = self.gamma_vx*(Mx + Pey)
        self.My_final = self.gamma_vy*(My + Pex)
        self.P = P
        self.Mx = Mx
        self.My = My
        self.Pex = Pex
        self.Pey = Pey
        
        # loop through every perimeter patch to calculate shear stress using elastic method
        N_patches = len(self.perimeter["x_centroid"])
        for i in range(N_patches):
            dx = self.perimeter["x_centroid"][i] - self.x_centroid
            dy = self.perimeter["y_centroid"][i] - self.y_centroid
            
            # elastic method calculation
            v_axial = self.P / self.A
            v_Mx = self.Mx_final * dy / self.Ix
            v_My = -self.My_final * dx / self.Iy
            v_total = v_axial + v_Mx + v_My
            Fz = v_total * self.perimeter["area"][i]
            Mxi = Fz * dy
            Myi = -Fz * dx
            
            # save results
            self.perimeter["v_axial"].append(v_axial)
            self.perimeter["v_Mx"].append(v_Mx)
            self.perimeter["v_My"].append(v_My)
            self.perimeter["v_total"].append(v_total)
            self.perimeter["Fz"].append(Fz)
            self.perimeter["Mxi"].append(Mxi)
            self.perimeter["Myi"].append(Myi)
        self.v_max = abs(max(self.perimeter["v_total"], key=abs))
        
        # check equilibrium
        # note I am subtracting below because we are specifying the applied force, and deriving the
        # applied stress distribution rather than the reactions. This is all kind of backwards
        # I am used to going from loading --> reaction. In this case, we are goin from:
        # reaction -> loading -> loading distribution
        TOL = 0.1
        sumFz = sum(self.perimeter["Fz"])
        sumMx = sum(self.perimeter["Mxi"])
        sumMy = sum(self.perimeter["Myi"])
        residual_Fz = sumFz - self.P 
        residual_Mx = sumMx - self.Mx_final
        residual_My = sumMy - self.My_final
        flag_Fz = "OK" if abs(residual_Fz) < TOL else "WARNING: NOT OKAY. EQUILIBRIUM NOT SATISFIED"
        flag_Mx = "OK" if abs(residual_Mx) < TOL else "WARNING: NOT OKAY. EQUILIBRIUM NOT SATISFIED"
        flag_My = "OK" if abs(residual_My) < TOL else "WARNING: NOT OKAY. EQUILIBRIUM NOT SATISFIED"
        self.equilibrium_check_passed = flag_Fz =="OK" and flag_Mx =="OK" and flag_My =="OK"


        # convert perimeter dict to dataframe and return
        self.df_perimeter = pd.DataFrame(self.perimeter)
        
        # print out calculations step-by-step
        if verbose:
            print("1. Rotate to principal orientation...")
            if abs(required_rotation) > 0.1:
                if auto_rotate:
                    print("\t\t Rotating section and applied moment by {:.1f} deg".format(required_rotation))
                    print("\t\t\t Done!")
                else:
                    print("\t\t WARNING: Auto rotation is disabled. Shear section is NOT in its principal orientation")
                    print("\t\t WARNING: Equilibrium check will fail unless section is rotated by {:.1f} deg.".format(required_rotation))
            else:
                print("\t\t Already in principal orientation. Rotation not needed.")
                
            print("2. Adjusting applied moment...")
            print("\t\t Given:")
            if abs(required_rotation) > 0.1 and auto_rotate:
                print("\t\t\t Mx = {:.1f} k.in".format(M_vec[0]))
                print("\t\t\t My = {:.1f} k.in".format(M_vec[1]))
                print("\t\t Rotating to principal orientation:")
                print("\t\t\t Mx = {:.1f} k.in".format(M_vec_rotated[0]))
                print("\t\t\t My = {:.1f} k.in".format(M_vec_rotated[1]))
            else:
                print("\t\t\t Mx = {:.1f} k.in".format(Mx))
                print("\t\t\t My = {:.1f} k.in".format(My))
            print("\t\t Adjusting for eccentricity between column and perimeter centroid:")
            print("\t\t\t Mx + Pey = {:.1f} + {:.1f} = {:.1f} k.in".format(Mx, Pey, Mx + Pey))
            print("\t\t\t My + Pex = {:.1f} + {:.1f} = {:.1f} k.in".format(My, Pex, My + Pex))
            print("\t\t Applying gamma_v factor:")
            print("\t\t\t gamma_vx * (Mx + Pey) = {:.1f} * {:.1f} = {:.1f} k.in".format(self.gamma_vx, Mx+Pey, self.Mx_final))
            print("\t\t\t gamma_vy * (My + Pex) = {:.1f} * {:.1f} = {:.1f} k.in".format(self.gamma_vy, My+Pex, self.My_final))
            
            print("3. Calculating shear stress...")
            print("\t\t Maximum shear stress = {:.1f} psi".format(self.v_max*1000))
            
            print("4. Checking equilibrium...")
            print("\t\t {:<8} {:<10} {:<10} {:<10} {:<10}".format("Force", "Applied", "SUM", "Residual", "Equilibrium?"))
            print("\t\t " + "-" * 55)
            print("\t\t {:<8} {:<10.1f} {:<10.1f} {:<10.2f} {:<10}".format("Fz", self.P, sumFz, residual_Fz, flag_Fz))
            print("\t\t {:<8} {:<10.1f} {:<10.1f} {:<10.2f} {:<10}".format("Mx", self.Mx_final, sumMx, residual_Mx, flag_Mx))
            print("\t\t {:<8} {:<10.1f} {:<10.1f} {:<10.2f} {:<10}".format("My", self.My_final, sumMy, residual_My, flag_My))
            elaspsed_time = (time.time() - time_start) * 1000
            if abs(required_rotation) > 0.1 and not auto_rotate:
                print("WARNING: Auto rotation is disabled. Perimeter is NOT in its principal orientation")
                print("WARNING: Equilibrium check will fail unless geometry is rotated by {:.1f} deg.".format(required_rotation))
            print(f"Analysis completed in {elaspsed_time:.0f} ms.")
                  
        return self.df_perimeter
        
    
    def plot_results(self, colormap="jet", cmin="auto", cmax="auto"):
        """
        plot results using matplotlib.
        
        Args:
            colormap        (OPTIONAL) str:: colormap for coloring perimeter. Default = "jet"
                                        https://matplotlib.org/stable/gallery/color/colormap_reference.html
            cmin            (OPTIONAL) str or float:: min shear stress (psi) for color mapping. Default = "auto".
            cmax            (OPTIONAL) str or float:: max shear stress (psi) for color mapping. Default = "auto".
        
        Returns:
            a matplotlib figure
        """
        # initialize figure
        fig, axs = plt.subplots(1,2, figsize=(11,8.5), gridspec_kw={"width_ratios":[2,3]})
        
        # prepare colormap
        cm = plt.get_cmap(colormap)
        cm = cm.reversed()
        magnitude = [v*1000 for v in self.perimeter["v_total"]] # convert to psi
        cmin = min(magnitude) if cmin == "auto" else cmin
        cmax = max(magnitude) if cmax == "auto" else cmax
        stress_is_uniform = math.isclose(cmax-cmin, 0)
        if stress_is_uniform:
            cmin = 0
        v_normalized = [(v-cmin)/(cmax-cmin) for v in magnitude]
        colors = [cm(x) for x in v_normalized]
        

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
            
            # add patch to plot
            axs[1].add_patch(patches.Polygon(np.array(vertices), closed=True, facecolor=colors[i],
                                          alpha=1, edgecolor=colors[i], zorder=3, lw=0.5))
            
        # add a colorbar on the side
        tick_values = np.linspace(cmin,cmax,9)
        norm = mcolors.Normalize(vmin=cmin, vmax=cmax)
        fig.colorbar(mcm.ScalarMappable(norm=norm, cmap=cm), 
                     orientation='vertical',
                     ax=axs[1],
                     ticks=tick_values)
        
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
        
        # plot x-y principal axes
        ordinate = 0.4*max(self.width, self.height)
        axs[1].annotate("",
                        xy=(self.x_centroid+ordinate, self.y_centroid), 
                        xytext=(self.x_centroid, self.y_centroid),
                        color="black",
                        arrowprops=dict(arrowstyle="simple,head_length=0.6,head_width=0.50,tail_width=0.06",
                                            fc="darkblue", ec="darkblue"))
        axs[1].annotate("",
                        xy=(self.x_centroid, self.y_centroid+ordinate), 
                        xytext=(self.x_centroid, self.y_centroid),
                        color="black",
                        arrowprops=dict(arrowstyle="simple,head_length=0.6,head_width=0.50,tail_width=0.06",
                                            fc="darkblue", ec="darkblue"))
        axs[1].annotate("X",
                        xy=(self.x_centroid, self.y_centroid), 
                        xytext=(self.x_centroid+1.1*ordinate, self.y_centroid),
                        va="center",
                        ha="center",
                        color="darkblue")
        axs[1].annotate("Y",
                        xy=(self.x_centroid, self.y_centroid), 
                        xytext=(self.x_centroid, self.y_centroid+1.1*ordinate),
                        va="center",
                        ha="center",
                        color="darkblue")
        
        # plot Cog
        axs[1].plot(self.x_centroid, self.y_centroid, marker="x", c="darkblue",markersize=6, zorder=3, linestyle="none")
        
        # freeze axis range, then plot slab edge
        axs[1].set_aspect('equal', 'datalim')
        axs[1].set_xlim(axs[1].get_xlim())
        axs[1].set_ylim(axs[1].get_ylim())
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
        

        # annotation for perimeter properties
        xo = 0.12
        yo = 0.97
        dy = 0.045
        unit = "in"
        axs[0].annotate("Geometric Properties", 
                        (xo-0.03,yo), fontweight="bold",xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$x_{{cg}} = {:.1f} \quad {}$".format(self.x_centroid, unit), 
                        (xo,yo-dy*1), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$y_{{cg}} = {:.1f} \quad {}$".format(self.y_centroid, unit), 
                        (xo,yo-dy*2), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$L = {:.1f} \quad {}$".format(self.L, unit), 
                        (xo,yo-dy*3), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$A = {:.1f} \quad {}^2$".format(self.A, unit), 
                        (xo,yo-dy*4), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$I_x = {:,.0f} \quad {}^4$".format(self.Ix, unit), 
                        (xo,yo-dy*5), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$I_y = {:,.0f} \quad {}^4$".format(self.Iy, unit), 
                        (xo,yo-dy*6), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{x,top}} = {:,.0f} \quad {}^3$".format(self.Sx1, unit), 
                        (xo,yo-dy*7), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{x,bottom}} = {:,.0f} \quad {}^3$".format(self.Sx2, unit), 
                        (xo,yo-dy*8), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{y,right}} = {:,.0f} \quad {}^3$".format(self.Sy1, unit), 
                        (xo,yo-dy*9), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$S_{{y,left}} = {:,.0f} \quad {}^3$".format(self.Sy2, unit), 
                        (xo,yo-dy*10), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        
        axs[0].annotate("Applied Loading", 
                        (xo-0.03,yo-dy*11), fontweight="bold",xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$M_{{x}} = {:.1f} \quad k.in$".format(self.Mx), 
                        (xo,yo-dy*12), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$M_{{y}} = {:.1f} \quad k.in$".format(self.My), 
                        (xo,yo-dy*13), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$\gamma_{{vx}} = {:.2f}$".format(self.gamma_vx), 
                        (xo,yo-dy*14), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$\gamma_{{vy}} = {:.2f}$".format(self.gamma_vy), 
                        (xo,yo-dy*15), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$Pe_{{x}} = {:.1f} \quad k.in$".format(self.Pex), 
                        (xo,yo-dy*16), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$Pe_{{y}} = {:.1f} \quad k.in$".format(self.Pey), 
                        (xo,yo-dy*17), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$P_{{design}} = {:.1f} \quad kips$".format(self.P), 
                        (xo,yo-dy*18), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$M_{{x,design}} = {:.1f} \quad k.in$".format(self.Mx_final), 
                        (xo,yo-dy*19), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        axs[0].annotate(r"$M_{{y,design}} = {:.1f} \quad k.in$".format(self.My_final), 
                        (xo,yo-dy*20), xycoords='axes fraction', fontsize=12, va="top", ha="left")
        
        
        # warning message if not about principal orientation
        if abs(self.theta_p) > 0.1:
            axs[1].annotate("WARNING: Perimeter is not in principal orientation.\nResult above may not be in equilibrium.", 
                            (0.05,0.07),xycoords='axes fraction', fontsize=12, va="top", ha="left", color="darkred", wrap=True)
        
        # styling
        fig.suptitle("Punching Shear Analysis Results (psi)", fontweight="bold", fontsize=16)
        axs[1].set_axisbelow(True)
        axs[0].set_xticks([])
        axs[0].set_yticks([])
        axs[1].grid(linestyle='--')
        plt.tight_layout()
        
        return fig
    
    
    
    def plot_results_3D(self, colormap="jet", cmin="auto", cmax="auto", scale=10):
        """
        Use plotly to generate an interactive plot.
        
        Args:
            colormap        (OPTIONAL) str:: colormap used to plot stress contour. I like jet and turbo. https://plotly.com/python/builtin-colorscales/
            cmin            (OPTIONAL) str or float:: minimum shear stress for contour (psi). Default = "auto".
            cmax            (OPTIONAL) str or float:: maximum shear stress for contour (psi). Default = "auto".
            scale           (OPTIONAL) float:: used to adjust size of vector plot. Default = 10.
        
        Returns:
            a plotly figure object
        """
        
        #################################################
        # INITIALIZE PLOT
        #################################################
        fig = make_subplots(rows=2, cols=2,
                            subplot_titles=("Shear Perimeter Properties", "Vector Plot", "Applied Loading"),
                            column_widths=[0.3, 0.7],
                            row_heights=[0.55, 0.45],
                            horizontal_spacing=0.02,
                            vertical_spacing=0.01,
                            specs = [[{"type":"table"}, {"type":"scene","rowspan":2}],
                                     [{"type":"table"}, None],
                                     ])
        
        #################################################
        # TABLES
        #################################################
        # perimeter properties table
        table_properties = [r"$x_{{cg}}$",
                     r"$y_{{cg}}$",
                     r"$b_o$",
                     r"$A$",
                     r"$I_{x}$",
                     r"$I_{y}$",
                     r"$S_{{x,top}}$",
                     r"$S_{{x,bottom}}$",
                     r"$S_{{y,right}}$",
                     r"$S_{{y,left}}$"]
        table_values = [r"${:.2f} \quad in$".format(self.x_centroid),
                        r"${:.2f} \quad in$".format(self.y_centroid),
                        r"${:.1f} \quad in$".format(self.L),
                        r"${:,.0f} \quad in^2$".format(self.A),
                        r"${:,.0f} \quad in^3$".format(self.Ix),
                        r"${:,.0f} \quad in^3$".format(self.Iy),
                        r"${:,.0f} \quad in^2$".format(self.Sx1),
                        r"${:,.0f} \quad in^2$".format(self.Sx2),
                        r"${:,.0f} \quad in^2$".format(self.Sy1),
                        r"${:,.0f} \quad in^2$".format(self.Sy2)]
        property_table = go.Table(header_values = ['Parameters', 'Value'],
                                  header_line_color = "black",
                                  header_font_color = "white",
                                  header_fill_color = "#3b3b41",
                                  header_align = "center",
                                  header_font_size = 18,
                                  header_height = 34,
                                  cells_values = [table_properties, table_values],
                                  cells_line_color = "black",
                                  cells_font_color = "black",
                                  cells_fill_color = "white",
                                  cells_align = "center",
                                  cells_font_size = 22,
                                  cells_height = 34)
        fig.add_trace(property_table, row=1, col=1)
        
        # applied force table
        table_properties = [r"$M_x$",
                            r"$M_y$",
                            r"$\gamma_{{vx}}$",
                            r"$\gamma_{{vy}}$",
                            r"$Pe_x$",
                            r"$Pe_y$",
                            r"$P_{{design}}$",
                            r"$M_{{x,design}}$",
                            r"$M_{{y,design}}$"]
        table_values = [r"${:.1f} \quad k.in$".format(self.Mx),
                        r"${:.1f} \quad k.in$".format(self.My),
                        r"${:.2f}$".format(self.gamma_vx),
                        r"${:.2f}$".format(self.gamma_vy),
                        r"${:.1f} \quad k.in$".format(self.Pex),
                        r"${:.1f} \quad k.in$".format(self.Pey),
                        r"${:.1f} \quad kips$".format(self.P),
                        r"${:.1f} \quad k.in$".format(self.Mx_final),
                        r"${:.1f} \quad k.in$".format(self.My_final)]
        property_table = go.Table(header_values = ['Applied Load', 'Value'],
                                  header_line_color = "black",
                                  header_font_color = "white",
                                  header_fill_color = "#3b3b41",
                                  header_align = "center",
                                  header_font_size = 18,
                                  header_height = 34,
                                  cells_values = [table_properties, table_values],
                                  cells_line_color = "black",
                                  cells_font_color = "black",
                                  cells_fill_color = "white",
                                  cells_align = "center",
                                  cells_font_size = 22,
                                  cells_height = 34)
        fig.add_trace(property_table, row=2, col=1)
        
        
        
        #################################################
        # VECTOR PLOTS
        #################################################
        # prep colormap and vector length
        cm = plt.get_cmap(colormap)
        cm = cm.reversed()
        magnitude = [v*1000 for v in self.perimeter["v_total"]] # convert to psi
        cmin = min(magnitude) if cmin == "auto" else cmin
        cmax = max(magnitude) if cmax == "auto" else cmax
        if math.isclose(cmax-cmin, 0):
            cmin = cmin - 1
            cmax - cmax + 1
            
        # plot shear stress quiver contour
        x_lines = []
        y_lines = []
        z_lines = []
        base_dot = [[],[],[]]
        tip_dot = [[],[],[]]
        line_colors = []
        dot_colors = []
        hover_text = []
        LENGTH_SF = scale/max(abs(cmax), abs(cmin))
        for i in range(len(self.perimeter["x_centroid"])):
            # first point (on Z=0 plane)
            x0 = self.perimeter["x_centroid"][i]
            y0 = self.perimeter["y_centroid"][i]
            z0 = 0
            xyz0_array = np.array([x0,y0,z0])
            
            # second point
            u = 0
            v = 0
            w = magnitude[i]
            uvw_array = np.array([u,v,w])
            xyz1_array = xyz0_array + LENGTH_SF * uvw_array
            
            # add to list of plot lines
            x_lines.extend([xyz0_array[0], xyz1_array[0], None])
            y_lines.extend([xyz0_array[1], xyz1_array[1], None])
            z_lines.extend([xyz0_array[2], xyz1_array[2], None])
            
            # add to list of base point
            base_dot[0].append(xyz0_array[0])
            base_dot[1].append(xyz0_array[1])
            base_dot[2].append(xyz0_array[2])
            
            # add to list of tip point
            tip_dot[0].append(xyz1_array[0])
            tip_dot[1].append(xyz1_array[1])
            tip_dot[2].append(xyz1_array[2])
            
            # add to list of colors
            magnitude_normalized = (w-cmin)/(cmax-cmin)
            rgb01 = cm(magnitude_normalized)
            rgb255 = [a * 255 for a in rgb01]
            rgb_str = f"rgb({rgb255[0]},{rgb255[1]},{rgb255[2]})"
            line_colors.append(rgb_str)
            line_colors.append(rgb_str)
            line_colors.append("white")
            dot_colors.append(rgb_str)
            
            # add to list of hoverinfo
            custom_hover = 'V_axial: {:.1f} psi<br>'.format(self.perimeter["v_axial"][i]*1000) +\
                'V_Mx: {:.1f} psi<br>'.format(self.perimeter["v_Mx"][i]*1000) +\
                'V_My: {:.1f} psi<br>'.format(self.perimeter["v_My"][i]*1000) +\
                '<b>V_total: {:.1f} psi</b><br>'.format(w)
            hover_text.append(custom_hover)
        
        # prep work before plotting vectors
        hovertemplate = 'coord: (%{x:.1f}, %{y:.1f}, %{z:.1f})<br>' + '%{text}<extra></extra>'
        tick_interval = np.linspace(cmin, cmax, 9)
        tick_interval_str = [f"{x:.2f}" for x in tick_interval]
        dot_for_colorbar = go.Scatter3d(x=[0],
                                      y=[0],
                                      z=[0],
                                      mode='markers',
                                      showlegend = False,
                                      opacity=0,
                                      marker_colorscale=colormap,
                                      marker_reversescale=True,
                                      marker_showscale=True,
                                      marker_cmin = cmin,
                                      marker_cmax = cmax,
                                      marker_color="rgba(255, 255, 255, 0)",
                                      marker_colorbar=dict(title_text="psi",
                                                           outlinecolor="black",
                                                           outlinewidth=2,
                                                           tickvals=tick_interval,
                                                           ticktext=tick_interval_str,
                                                           xpad=40,
                                                           ypad=40))
        # plot vectors
        vector_line = go.Scatter3d(x=x_lines,
                                      y=y_lines,
                                      z=z_lines,
                                      mode='lines',
                                      line_width = 8,
                                      line_color = line_colors,
                                      showlegend = False,
                                      hoverinfo="none")
        vector_tip = go.Scatter3d(x=tip_dot[0],
                                      y=tip_dot[1],
                                      z=tip_dot[2],
                                      mode='markers',
                                      marker_size = 12,
                                      showlegend = False,
                                      hovertemplate = hovertemplate,
                                      text = hover_text,
                                      hoverlabel_font_size=16,
                                      marker_color=dot_colors,
                                      opacity = 0,)
        vector_base = go.Scatter3d(x=base_dot[0],
                                      y=base_dot[1],
                                      z=base_dot[2],
                                      mode='markers',
                                      marker_symbol = "square",
                                      marker_size = 6,
                                      showlegend = False,
                                      hovertemplate = hovertemplate,
                                      text = hover_text,
                                      hoverlabel_font_size=16,
                                      marker_color=dot_colors,
                                      )
        fig.add_trace(vector_base, row=1, col=2)
        fig.add_trace(vector_tip, row=1, col=2)
        fig.add_trace(vector_line, row=1, col=2)
        fig.add_trace(dot_for_colorbar, row=1, col=2)
        
        
        #################################################
        # PLOT COLUMN AND STUDRAILS
        #################################################
        # plot studrails
        if len(self.studrail_pts) != 0:
            x_studrail = []
            y_studrail = []
            z_studrail = []
            for i in range(len(self.studrail_pts)):
                pt1 = self.studrail_pts[i][0]
                pt2 = self.studrail_pts[i][1]
                x_studrail.extend([pt1[0], pt2[0], None])
                y_studrail.extend([pt1[1], pt2[1], None])
                z_studrail.extend([0, 0, None])
            studrail_line = go.Scatter3d(x=x_studrail,
                                          y=y_studrail,
                                          z=z_studrail,
                                          mode='lines',
                                          line_width = 12,
                                          line_color = "gray",
                                          showlegend = False,
                                          hoverinfo="none")
            fig.add_trace(studrail_line, row=1, col=2)
        
        # plot column (two triangles)
        pt1 = np.append(self.col_pts[0],0)
        pt2 = np.append(self.col_pts[1],0)
        pt3 = np.append(self.col_pts[2],0)
        pt4 = np.append(self.col_pts[3],0)
        mesh_xyz = np.array([pt1,pt2,pt3,pt4])
        col_mesh = go.Mesh3d(x = mesh_xyz[:,0],
                             y = mesh_xyz[:,1],
                             z = mesh_xyz[:,2],
                             i = [0,1],
                             j = [1,2],
                             k = [3,3],
                             color = "darkgray",
                             showlegend = False,
                             hoverinfo="none")
        fig.add_trace(col_mesh, row=1, col=2)
        
        #################################################
        # STYLING AND ORIGIN MARKER
        #################################################
        # plot orgin marker at centroid of perimeter
        xmax = max(self.perimeter["x_centroid"])
        xmin = min(self.perimeter["x_centroid"])
        ymax = max(self.perimeter["y_centroid"])
        ymin = min(self.perimeter["y_centroid"])
        dmax = max(xmax-xmin, ymax-ymin)/1.5
        X = go.Scatter3d(
            x=[self.x_centroid, self.x_centroid + dmax/14],
            y=[self.y_centroid, self.y_centroid],
            z=[0,0],
            mode='lines+text',
            hoverinfo = 'skip',
            showlegend=False,
            line=dict(color='blue', width=5),
            text=["","X"],
            textposition="top center",
            textfont=dict(
                family="Arial",
                size=14,
                color="blue"))
        fig.add_trace(X, row=1, col=2)
        Y = go.Scatter3d(
            x=[self.x_centroid, self.x_centroid],
            y=[self.y_centroid, self.y_centroid + dmax/14],
            z=[0,0],
            mode='lines+text',
            hoverinfo = 'skip',
            line=dict(color='red', width=5),
            text=["","Y"],
            textposition="top center",
            showlegend=False,
            textfont=dict(
                family="Arial",
                size=14,
                color="red"))
        fig.add_trace(Y,row=1, col=2)
        Z = go.Scatter3d(
            x=[self.x_centroid, self.x_centroid],
            y=[self.y_centroid, self.y_centroid],
            z=[0, 0 + dmax/14],
            mode='lines+text',
            hoverinfo = 'skip',
            line=dict(color='green', width=5),
            text=["","Z"],
            textposition="top center",
            showlegend=False,
            textfont=dict(
                family="Arial",
                size=14,
                color="green"))
        fig.add_trace(Z, row=1, col=2)
        # change such that axes are in proportion.
        fig.update_scenes(aspectmode="data")
        
        # add title
        fig.update_layout(title="<b>Punching Shear Analysis Results</b>",
                          title_xanchor="center",
                          title_font_size=22,
                          title_x=0.5, 
                          title_y=0.98,
                          title_font_color="black")
        
        # background color
        fig.update_layout(paper_bgcolor="white",
                          font_color="black")
        
        # adjust zoom level and default camera position
        fig.update_scenes(camera_eye=dict(x=2, y=2, z=2))
        
        # change origin to be on the bottom left corner
        fig.update_scenes(xaxis_autorange="reversed")
        fig.update_scenes(yaxis_autorange="reversed")
        fig.update_scenes(xaxis_backgroundcolor="white",
                          yaxis_backgroundcolor="white",
                          xaxis_gridcolor="grey",
                          yaxis_gridcolor="grey",
                          xaxis_gridwidth=0.5,
                          yaxis_gridwidth=0.5,
                          zaxis_visible=False)
        fig.show()
        return fig




