import printcore
from time import sleep

def grip(iniX, iniY, endX, endY):

	iniGrip = 'G1 X%f Y%f' % (iniX, iniY)
	endGrip = 'G1 X%f Y%f' % (endX, endY)

	gcode = ['M43 P4 S10', 'G4 P500', 'G1 F9000', 'G4 P500']
	gcode +=  [iniGrip, 'M43 P4 S40', 'G4 P500','M43 P4 S45', 'G4 P500','M43 P4 S50', 'G4 P500','M43 P4 S55', 'G4 P500','M43 P4 S60', 'G4 P500']
	gcode += ['M43 P4 S65', 'G4 P500','M43 P4 S70', 'G4 P500',endGrip, 'M43 P4 S65', 'G4 P500','M43 P4 S60', 'G4 P500','M43 P4 S55', 'G4 P500']
	gcode += ['M43 P4 S50', 'G4 P500','M43 P4 S45', 'G4 P500','M43 P4 S40', 'G4 P500','M43 P4 S10']

	return gcode

def putWater(waterX, waterY, dropX, dropY):

	water = 'G1 X%f Y%f' % (waterX, waterY)
	dish = 'G1 X%f Y%f' % (dropX, dropY)

	gcode = ['M43 P1 S180', 'M43 P0 S10', 'G4 P500', water, 'M43 P0 S85', 'G4 P1000', 'M43 P1 S150', 'G4 P4000', 'M43 P0 S10', 'G4 P500', 'M43 P1 S145', 'G4 P500']
	gcode += [dish, 'G4 P500', 'M43 P0 S85', 'G4 P500', 'M43 P1 S150', 'G4 P500', 'M43 P1 S180', 'G4 P2000', 'M43 P0 S10', 'G4 P500']

	return gcode

p = printcore.printcore("/dev/tty.usbserial-A4008eY6",115200)
#p.loud=True
sleep(3)

gcode = ['G28', 'G4 P1000']
gcode += grip(66,24,255,96) + putWater(190,100,190,50) + grip(255,96,66,24)
gcode += grip(66,85,255,96) + putWater(190,100,190,50) + grip(255,96,66,85)
gcode += grip(66,138,255,96) + putWater(190,100,190,50) + grip(255,96,66,138)

p.startprint(gcode)
sleep(3)
