import cv2 as cv
import cv2
import ParticleFilterSquare as pf
import numpy as np
from random import uniform

fourcc = cv2.VideoWriter_fourcc(*'X264')
outvideo = cv2.VideoWriter("test.avi", fourcc, 20.0, (700,500))

width, height = 400, 600
num_particles = 1000
condensation = pf.Condensation(num_particles, 0, 0, height, width)
condensation.addTarget()

car = (int(uniform(200,400)),int( uniform(100,300)))
obstacle = (500,500)
#car = (600,0)

def draw_particles(track, applyweight=0):
    trackc = track.copy()
    for col in condensation.particles:
        for particle in col:
            x = particle.x * uniform(0.99, 1.01) + 50
            y = particle.y * uniform(0.99, 1.01) + 50
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

def laser_car(car):
    out = min(car[0], car[1], 600-car[0], 400-car[1]) 

    return min(car[0], car[1], 600-car[0], 400-car[1]) 

canvas = np.ones((500,700,3)) * 255
canvas = cv.rectangle( canvas, (50,50, 600, 400), 0, 5)
cv.line(canvas, (350,450), (350,250), 0, 5)


step = 0
while step < 100:
    canvasp = draw_particles(canvas)
    cv.circle(canvasp, ( car[0]+50, car[1]+50 ), 10, (0,200,0), -1)
    cv.imshow("particles", canvasp)
    cv.waitKey(1000)
    for i in range(3):
        outvideo.write(canvasp.astype('uint8'))
   
    measurement = laser_car(car)
    condensation.updateWeights( measurement )
    condensation.estimateState()
    ex = condensation.estimation[0]['x'] + 50
    ey = condensation.estimation[0]['y'] + 50 
    canvasp = draw_particles(canvas,1)
    cv.circle(canvasp, ( int(ex), int(ey) ), 15, (200,0,0), 2)
    #cv.imshow("weights", canvasp)
    #cv.waitKey(200)
    
    condensation.reSampling()
    canvasp = draw_particles(canvas)
    cv.circle(canvasp, ( car[0]+50, car[1]+50 ), 10, (0,200,0), -1)
    cv.circle(canvasp, ( int(ex), int(ey) ), 15, (200,0,0), 2)
    #cv.imshow("resampling", canvasp)
    #cv.waitKey(200)
    
    oldcar = car
    newx = car[0] + int(uniform(-50,50))
    newx = max(0, newx)
    newx = min(newx, 600)
    newy = car[1] + int(uniform(-50,50))
    newy = max(0, newy)
    newy = min(newy, 400)
    car = ( newx,newy)
    vector = (car[1]-oldcar[1], car[0]-oldcar[0])
    condensation.propagate(vector)
    canvasp = draw_particles(canvas)
    cv.circle(canvasp, ( car[0]+50, car[1]+50 ), 10, (0,200,0), -1)

    #cv.imshow("propagate", canvasp)
    #cv.waitKey(500)
    step +=1

outvideo.release()
cv2.destroyAllWindows()
