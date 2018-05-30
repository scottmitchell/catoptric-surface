import tkinter as Tk
from CatoptricRow import CatoptricRow
import csv
import serial
import serial.tools.list_ports
import os.path
import time

serialPortOrder = { "8543931323035121E170" : 1,
					"8543931323035130C092" : 2,
					"85439313230351610262" : 3,
					"75435353934351D052C0" : 4,
					"85436323631351509171" : 5,
					"75435353934351F0C020" : 6,
					"8543931333035160E081" : 7,
					"85439313230351818090" : 8,
					"755333434363519171F0" : 9,
					"8543931333035160F102" : 10,
					"8543931323035161B021" : 11,
					"85439313330351D03160" : 12,
					"85439303133351716221" : 13,
					"85436323631351300201" : 14,
					"75435353934351E07072" : 15,
					"8543931323035170D0C2" : 16 
				}


class CatoptricSurface():

	def __init__(self):
		self.serialPorts = self.getOrderedSerialPorts()
		self.numRows = len(self.serialPorts)
		self.rowInterfaces = dict()

		self.setupRowInterfaces()
		self.reset() 


	# Initializes a Row Interface for each available arduino
	def setupRowInterfaces(self):

		for sP in self.serialPorts:
			name = serialPortOrder[sP.serial_number]
			port = sP.device

			rowLength = 0
			if (name >= 1 and name < 12):
				rowLength = 16
			elif (name >= 12 and name < 17):
				rowLength = 24
			elif (name >= 17 and name < 28):
				rowLength = 17
			elif (name >= 28 and name < 33):
				rowLength = 25

			print ("Initializing Catoptric Row %d with %d mirrors" % (name, rowLength))

			self.rowInterfaces[name] = CatoptricRow(name, rowLength, port)
	

	# Returns a list of serial ports, ordered according to the serialPortOrder dictionary
	def getOrderedSerialPorts(self):

		# Get all serial ports
		allPorts = serial.tools.list_ports.comports()
		
		# Get only ports with arduinos attached
		arduinoPorts = [p for p in allPorts if p.pid == 67]
		print ("\n%d Arduinos Found" % len(arduinoPorts)) 

		# Sort arduino ports by row
		try:
			arduinoPorts.sort(key= lambda x: serialPortOrder[x.serial_number])
		except:
			print("One or more arduino serial number unrecognized")
        
		for a in arduinoPorts:
			try:
				print ("Arduino #%s : Row #%d" % (a.serial_number, serialPortOrder[a.serial_number]))
			except:
				print ("Arduino #%s : Unrecognized Serial Number" % a.serial_number)
		print("\n")

		return arduinoPorts
	

	def reset(self):
		print ("\nResetting all mirrors to default position")
		for r in self.rowInterfaces:
			self.rowInterfaces[r].reset()
		
		self.run()


	def getCSV(self, path):
		# Deleta old CSV data
		self.csvData  = []

		# Read in CSV contents
		with open(path, newline='') as csvfile:
			reader = csv.reader(csvfile, delimiter=',')
			for row in reader:
				x = []
				for i in range(0, len(row)):
					x.append(row[i])
				self.csvData.append(x)
	

	def updateByCSV(self, path):
		self.getCSV(path)

		for i in range(0, len(self.csvData)):
			line = self.csvData[i]
			if (int(line[0]) in self.rowInterfaces):
				self.rowInterfaces[int(line[0])].reorientMirrorAxis(line)
			else:
				print("line %d of csv is addressed to a row that does not exist: %d" % (i, int(line[0])))
		
		self.run()


	def run(self):
		commandsOut = 1

		while (commandsOut > 0):

			for r in self.rowInterfaces:
				self.rowInterfaces[r].update()

			commandsOut = 0
			commandsQueue = 0
			ackCount = 0
			nackCount = 0
			for row in self.rowInterfaces:
				commandsOut += self.rowInterfaces[row].getCurrentCommandsOut()
				ackCount += self.rowInterfaces[row].getCurrentAckCount()
				nackCount += self.rowInterfaces[row].getCurrentNackCount()
				commandsQueue += self.rowInterfaces[row].commandQueue.qsize()

			print ("%d commands out | %d commands in queue | %d acks | %d nacks" % (commandsOut, commandsQueue, ackCount, nackCount), end="\r")

	

			


		
class CatoptricController():
	def __init__(self):
		self.surface = CatoptricSurface()

	def run(self):
		while True:
			c = input("\n'Reset' or enter path to orientation file:\n")

			if (c.lower() == 'reset'):
				self.surface.reset()
			
			if (os.path.exists(c)):
				print ("\nUpdating mirrors with '%s'" % c)
				self.surface.updateByCSV(c)
			else:
				print ("\nFile does not exist")




if __name__ == '__main__':
	c = CatoptricController()
	c.run()