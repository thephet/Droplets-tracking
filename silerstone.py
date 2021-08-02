import cv2 as cv
import ParticleFilterUserClicks as pf
import numpy as np
from random import uniform

class GridClickData:

    def __init__(self):
        self.drawing = False # True if mouse is pressed
        self.ix, self.iy = -1, -1 # first click, or top left corner
        self.points = [0, 0, 0, 0] # Platform coordinates
        self.finished = False # True when user releases click


    def grid_callback(self, event, x, y, flags, param):
        '''mouse callback function. See OpenCV documentation example'''

        if event == cv.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.points = [x, y, x, y]
            self.ix, self.iy = x,y

        elif event == cv.EVENT_MOUSEMOVE:
            if self.drawing == True:
                self.points = [self.ix, self.iy, x, y]

        elif event == cv.EVENT_LBUTTONUP:
            self.drawing = False
            self.points = [self.ix, self.iy, x, y]
            self.finished = True


    def get_platform_corners(self, frame, name=""):
        '''Given a frame, it will let the user click on the platform corners
        in order to obtain its coordinates: 
        top left corner, bottom right corner'''

        cv.namedWindow('Choose grid '+name)
        cv.setMouseCallback('Choose grid '+name, self.grid_callback)
        unmodified = frame.copy()

        # grid_callback sets finished to True once the user selects both corners
        while(self.finished is False):
            frame = unmodified.copy()
            cv.imshow('Choose grid '+name, frame)
            cv.waitKey(10)

        cv.destroyWindow('Choose grid '+name)

click_grid = GridClickData()   

track = cv.imread("silverstone.png")
# make it smaller
track = cv.resize(track, ( track.shape[1]//3, track.shape[0]//3 ) )
# convert to either white or black
track = cv.cvtColor(track, cv.COLOR_BGR2GRAY)
track[track>0] = 255

# Perform the distance transform algorithm
dist = cv.distanceTransform(track, cv.DIST_L2, 3)
#cv.normalize(dist, dist, 0, 1.0, cv.NORM_MINMAX)

width, height = track.shape
num_particles = 500
condensation = pf.Condensation(num_particles, 0, 0, height, width)
condensation.addTarget()

car = (760,380)

track = cv.cvtColor(track, cv.COLOR_GRAY2BGR)

def draw_particles(track, applyweight=0):
    trackc = track.copy()
    for col in condensation.particles:
        for particle in col:
            x = particle.x * uniform(0.99, 1.01)
            y = particle.y * uniform(0.99, 1.01)
            if applyweight == 0:
                cv.circle(trackc, (int(x), int(y)), 
                        int(2), (0,0,200), -1)
            else:
                size = 300*particle.weight
                if size < 2:
                    size = 2
                cv.circle(trackc, (int(x), int(y)), 
                        int(size), (0,0,200), -1)

    return trackc


step = 0
while True:
    trackc = draw_particles(track)
    cv.circle(trackc, ( car ), 10, (0,200,0), -1)
    click_grid.get_platform_corners(trackc)
    click_grid.finished = False
    p = np.array(click_grid.points)
    
    condensation.updateWeights(dist, p)
    condensation.estimateState()
    ex = condensation.estimation[0]['x']
    ey = condensation.estimation[0]['y']
    trackc = draw_particles(track,1)
    cv.circle(trackc, ( int(ex), int(ey) ), 15, (200,0,0), 2)
    cv.imshow("weights", trackc)
    cv.waitKey(1000)
    
    condensation.reSampling()
    trackc = draw_particles(track)
    cv.circle(trackc, ( car ), 10, (0,200,0), 2)
    cv.circle(trackc, ( int(ex), int(ey) ), 15, (200,0,0), 2)
    cv.imshow("resampling", trackc)
    cv.waitKey(1000)
    
    cv.circle(trackc, ( car ), 10, (0,200,0), 2)
    click_grid.get_platform_corners(trackc)
    click_grid.finished = False
    p = np.array(click_grid.points)
    condensation.propagate(p)
    car = (p[2], p[3])
    cv.circle(trackc, ( car ), 10, (0,200,0), 2)


    cv.imshow("propagate", trackc)
    cv.waitKey(1000)
