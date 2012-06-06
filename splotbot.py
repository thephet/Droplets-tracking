import printcore
from time import sleep

class Splotbot:

	def __init__(self, configInfo):

		self.p = printcore.printcore(configInfo['port'],115200)
		sleep(3)
		self.ci = configInfo

	# EACH OF THE FOLLOWING FUNCTIONS RETURNS A STRING
	# THIS STRING MUST LATER BE SENT TO THE ROBOT FOR EXECUTION
	# IT'S DONE THIS WAY TO QUICKLY CONCATENATE A SEQUENCE OF ACTIONS

	def home(self):
		''' homes the robot'''

	def move(self, x, y):
		''' moves the robot to the x,y position '''

	def pause(self, time):
		''' pauses the robot for time ms '''

	def setSpeed(self, speed):
		''' sets robot's speed, in mm per minute '''

	def grip(self):
		''' grips a dish'''

	def releaseGrip(self):
		''' releases the grip'''

	def moveDish(self, Xini, Yini, Xend, Yend):

		return move(Xini, Yini) + grip() + move(Xend, Yend) + releaseGrip()

	def moveDishTo(self, dish, Xend, Yend):
		''' moves the dish 'dish' to the desired XY position'''

		d = '%d' % dish
		Xini = self.ci['dishes'][d]['x']
		Yini = self.ci['dishes'][d]['y']
		
		moveDish(Xini, Yini, Xend, Yend)

	def moveDishFrom(self, dish, Xini, Yini):
		''' moves the dish from XY positions to its original position'''

		d = '%d' % dish
		Xend = self.ci['dishes'][d]['x']
		Yend = self.ci['dishes'][d]['y']
		
		moveDish(Xini, Yini, Xend, Yend)

	def dishToCam(self, dish):
		''' grips and moves the dish 'dish' over the webcam'''
		
		d = '%d' % dish
		Xini = self.ci['dishes'][d]['x']
		Yini = self.ci['dishes'][d]['y']
		Xend = self.ci['webcam']['grip']['x']
		Yend = self.ci['webcam']['grip']['y']

		moveDish(Xini, Yini, Xend, Yend)

	def dishFromCam(self, dish):
		''' grips and moves the dish 'dish' from the webcam
		to its original position'''
		
		d = '%d' % dish
		Xend = self.ci['dishes'][d]['x']
		Yend = self.ci['dishes'][d]['y']
		Xini = self.ci['webcam']['grip']['x']
		Yini = self.ci['webcam']['grip']['y']

		moveDish(Xini, Yini, Xend, Yend)

	def plunger(self, syringe, iniAngle, endAngle, step = 0, stepPause = 0):
		''' sets the syringe plunger's servo at iniAngle
		moves syringe's plunger until endAngle doing [abs(endAngle-iniAngle) / step] steps
		it waits for stepPause ms between each step.
		If step is it goes from iniAngle to endAngle in one step
		If stepPause is 0 it does not pause between steps'''

	def syringeDown(self, syringe, endAngle):
		''' moves the syringe down until endAngle'''

	def syringeUp(self, syringe):
		'''moves syringe up'''

	def absorbAir(self, syringe):
		''' absorbs some air for transportation'''

	def releaseAir(self, syringe):
		''' releases absorbed air'''

	def background(self):
		''' moves the background panel over the webcam'''
		return move(self.ci['background']['x'], self.ci['background']['x'])

	def moveWater(self, waterX, waterY, dropX, dropY, syringe, iniAngle, endAngle, step = 0, stepPause = 0):
		''' moves water from waterXY to dropXY based on plunger()'''
		instructions = move(waterX, waterY) + 
		instructions += syringeDown(syringe, 60) + plunger(syringe, iniAngle, endAndle, step, stepPause)
		instructions += syringeUp(syringe) + absorbAir(syringe) + move(dropX, dropY) + releaseAir(syringe)
		instructions += syringeDown(syringe, 60) + plunger(syringe, endAngle, iniAndle, step, stepPause)
		instructions += syrungeUp(syringe)
		return instructions

	def moveFromLiquid(self, liquid, dropX, dropY, syringe, iniAngle, endAngle, step = 0, stepPause = 0):
		''' moves the liquid 'liquid' to the desired XY position defined by dropX dropY'''
		
		syr = '%d' % syringe
		waterX = self.ci['liquids'][syr]['x']
		waterY = self.ci['liquids'][syr]['y']
		moveWater(waterX, waterY, dropX, dropY, syringe, iniAngle, endAngle, step, stepPause):

	def dropToCam(self, waterX, waterY, syringe, iniAngle, endAngle, step = 0, stepPause = 0):
		''' moves some liquid from the desired waterXY position to over the webcam'''

		syr = '%d' % syringe
		dropX = self.ci['webcam'][syr]['x']
		dropY = self.ci['webcam'][syr]['y']
		moveWater(waterX, waterY, dropX, dropY, syringe, iniAngle, endAngle, step, stepPause):

	def liquidTocam(self, liquid, syringe, iniAngle, endAngle, step = 0, stepPause = 0):
		''' moves the liquid 'liquid' over the webcam'''

		syr = '%d' % syringe
		waterX = self.ci['liquids'][syr]['x']
		waterY = self.ci['liquids'][syr]['y']
		dropX = self.ci['webcam'][syr]['x']
		dropY = self.ci['webcam'][syr]['y']
		moveWater(waterX, waterY, dropX, dropY, syringe, iniAngle, endAngle, step, stepPause):

	def execute(self, instructions):
		''' execute the instructions in the input array'''
		self.p.startprint(instructions)
		sleep(3)


if __name__ == "__main__":

	# an exemple of moving droplets around and placing water on them
	config = {
				# one syringe given number 0. its plunger uses pin 0, its upDown servo pin 1
				'syringes' : { '0': { 'plunger': 0, 'upDown': 1 } },
				'dishes' : { '0': {'x': 10, 'y': 10}, '1': {'x': 10, 'y': 40}} #ini positions to grip
				'grip' : 2, #the grip uses pin 2
				'background': {'x': 250, 'y': 60, 'pin': 3}, #panel set in pin 3 will go to 250,60
				'webcam' : { 'grip': {'x', 240, 'y':50}, #position where the grip can release to place over cam
							'0': {'x':220, 'y': 50}, #position where the webcam is respect to syringe 0
							}, 
				'liquids' : {'0': {'0': {'x': 120, 'y':30}}}, #position of liquid 0 respect to syringe 0
			}

	robot = Splotbot(config)

	experiment = home() + dishToCam(0) + liquidTocam(0, 0, 180, 100, 5, 500)
	experiment += pause(10000) + dishFromCam(0) + dishToCam(1)
	experiment += liquidTocam(0, 0, 180, 100, 5, 500) + pause(10000)
	experiment += dishFromCam(1)

	robot.execute(experiment)
