#!/usr/bin/env python3
'''
PyThermostat
'''

from tkinter import *
from tkinter import messagebox
import datetime
from pathlib import Path
import configparser
import board
from adafruit_bme280 import basic as adafruit_bme280
import RPi.GPIO as GPIO

class Program(Tk):
	def __init__ (self):
		Tk.__init__(self)
		self._frame = None

		# Window Setup
		self.title('Thermostat')
		self.configure(background = 'black', cursor='none')
		# w,h = self.winfo_screenwidth(), self.winfo_screenheight()	# Gathering the size of the screen
		w,h = [800,480]
		self.geometry(f'{w}x{h}+0+0')			# Changing the Program size to match the screen
		self.attributes('-fullscreen', True)	# Fullscreen window
		self.bind('<Escape>', self.onClosing)

		# Setup vars
		self.config = configparser.ConfigParser()
		self.config.read('config.ini')
		self.tempVar = IntVar(self, 0)
		self.humVar = IntVar(self, 0)
		self.presVar = IntVar(self, 0)
		self.setTempVar = IntVar(self, self.config['DEFAULT']['TempuratureInt'])
		self.fanVar = StringVar(self, 'Off')
		self.pumpVar = StringVar(self, 'Off')
		self.speed = GPIO.HIGH
		
		# Setup widgets
		self.tempFrame = Frame(self, background='black')
		self.tempLabel = Label(self.tempFrame, bg='black', fg='green', font=('Noto Sans Mono', 150), width=2, textvariable=self.tempVar)
		self.tempDegreeLabel = Label(self.tempFrame, bg='black', fg='green', font=('Noto Sans Mono', 150), text='°')
		
		self.humPresFrame = Frame(self.tempFrame, background='black')
		self.humLabel = Label(self.humPresFrame, bg='black', fg='green', font=('Noto Sans Mono', 16), textvariable=self.humVar)
		self.humPercentLabel = Label(self.humPresFrame, bg='black', fg='green', font=('Noto Sans Mono', 16), text='%')
		self.presLabel = Label(self.humPresFrame, bg='black', fg='green', font=('Noto Sans Mono', 16), textvariable=self.presVar)
		self.presUnitLabel = Label(self.humPresFrame, bg='black', fg='green', font=('Noto Sans Mono', 16), text='inHg')

		self.setFrame = Frame(self, background='black')
		self.setLabel = Label(self.setFrame, bg='black', fg='green', font=('Noto Sans Mono', 48), textvariable=self.setTempVar)
		self.setDegreeLabel = Label(self.setFrame, bg='black', fg='green', font=('Noto Sans Mono', 48), text='°')
		self.setPlusButton = Button(self.setFrame, activebackground='black', activeforeground='green', bg='black', borderwidth=0, fg='green', 
			font=('Noto Sans Mono', 48), highlightthickness=0, text='+', command=lambda: self.setTemp('+'))
		self.setMinusButton = Button(self.setFrame, activebackground='black', activeforeground='green', bg='black', borderwidth=0, fg='green', 
			font=('Noto Sans Mono', 48), highlightthickness=0, text='-', command=lambda: self.setTemp('-'))

		self.rightFrame = Frame(self, background='black')
		self.fanFrame = Frame(self.rightFrame, background='black')
		self.fanLabel = Label(self.fanFrame, bg='black', fg='green', font=('Noto Sans Mono', 32), text='Fan')
		self.fanButton = Button(self.fanFrame, activebackground='black', activeforeground='green', bg='black', borderwidth=0, fg='green', 
			font=('Noto Sans Mono', 32), highlightthickness=0, width=4, textvariable=self.fanVar, command=self.setFan)

		self.pumpFrame = Frame(self.rightFrame, background='black')
		self.pumpLabel = Label(self.pumpFrame, bg='black', fg='green', font=('Noto Sans Mono', 32), text='Pump')
		self.pumpButton = Button(self.pumpFrame, activebackground='black', activeforeground='green', bg='black', borderwidth=0, fg='green', 
			font=('Noto Sans Mono', 32), highlightthickness=0, width=4, textvariable=self.pumpVar, command=self.setPump)

		# Setup weights
		self.columnconfigure(0, weight=2)
		self.columnconfigure(1, weight=1)
		self.rowconfigure(0, weight=2)
		self.rowconfigure(1, weight=1)
		self.rightFrame.columnconfigure(0, weight=1)
		self.rightFrame.rowconfigure(0, weight=1)
		self.rightFrame.rowconfigure(1, weight=1)

		# Place widgets
		self.tempFrame.grid(column=0, row=0)
		self.tempLabel.grid(column=0, row=0)
		self.tempDegreeLabel.grid(column=1, row=0)

		self.humPresFrame.grid(column=0, row=1, columnspan=2, sticky='WE')
		self.humLabel.pack(side=LEFT)
		self.humPercentLabel.pack(side=LEFT)
		self.presUnitLabel.pack(side=RIGHT)
		self.presLabel.pack(side=RIGHT)

		self.setFrame.grid(column=0, row=1)
		self.setMinusButton.pack(side=LEFT)
		self.setLabel.pack(side=LEFT)
		self.setDegreeLabel.pack(side=LEFT)
		self.setPlusButton.pack(side=LEFT)

		self.rightFrame.grid(column=1, row=0, rowspan=2, sticky='NSEW')
		self.fanFrame.grid(column=0, row=0)
		self.fanLabel.pack()
		self.fanButton.pack(side=LEFT)

		self.pumpFrame.grid(column=0, row=1)
		self.pumpLabel.pack()
		self.pumpButton.pack(side=LEFT)

		# Setup the hardware and continue on
		self.pumpRelay = 26		# Relay pins (BCM)
		self.fanRelay = 20
		self.speedRelay = 21
		GPIO.setwarnings(False)
		GPIO.setup(self.pumpRelay, GPIO.OUT)
		GPIO.setup(self.fanRelay, GPIO.OUT)
		GPIO.setup(self.speedRelay, GPIO.OUT)
		GPIO.output(self.pumpRelay, GPIO.HIGH)
		GPIO.output(self.fanRelay, GPIO.HIGH)
		GPIO.output(self.speedRelay, GPIO.HIGH)

		self.logCounter = 0

		self.i2c = board.I2C()
		self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(self.i2c)
		self.after(1000, self.thermostat)

	def setTemp(self, sign):
		'''
		Adjusts setTempVar.  
		This is used to set your prefered tempurature.  
		'''
		if sign == '+':
			if self.setTempVar.get() >= 80:
				pass
			else:
				self.setTempVar.set(self.setTempVar.get() + 1)
				self.config['DEFAULT']['TempuratureInt'] = str(self.setTempVar.get())
		else:
			if self.setTempVar.get() <= 65:
				pass
			else:
				self.setTempVar.set(self.setTempVar.get() - 1)
				self.config['DEFAULT']['TempuratureInt'] = str(self.setTempVar.get())

	def setFan(self):
		'''
		Adjusts fanVar.  
		This adjusts the fans setting (off, low, high, auto).  
		'''
		if self.fanVar.get() == 'Off':
			self.fanVar.set('Low')
		elif self.fanVar.get() == 'Low':
			self.fanVar.set('High')
		elif self.fanVar.get() == 'High':
			self.fanVar.set('Auto')
		else:
			self.fanVar.set('Off')

	def setPump(self):
		'''
		Adjusts pumpVar.  
		This adjusts the pump setting (off, on, auto).  
		'''
		if self.pumpVar.get() == 'Off':
			self.pumpVar.set('On')
		elif self.pumpVar.get() == 'On':
			self.pumpVar.set('Auto')
		else:
			self.pumpVar.set('Off')

	def thermostat(self):
		'''
		Closed loop control of the swamp cooler.  
		Loops every second and uses the sensor readings to control the AC.
		'''
		TEMP_DIFFERENTIAL = int(self.config['DEFAULT']['TempDifferential'])		# +- difference of when the AC turns on and off
		SCHEDULE = eval(self.config['DEFAULT']['Schedule'])						# Schedule AC times

		# Read from the sensor
		temp = (self.bme280.temperature * 9/5) + 32						# Temp read in as Celsius, F = (C × 9/5) + 32
		hum = int(round(self.bme280.relative_humidity, 0))
		pres = int(round(self.bme280.pressure * .0295, 0))				# Pres read in as HectoPascals, 1 hPa = 0.0295 inHg
		self.tempVar.set(int(round(temp, 0)))
		self.humVar.set(hum)
		self.presVar.set(pres)
		therm = self.setTempVar.get()
		fan = self.fanVar.get()
		pump = self.pumpVar.get()

		if fan == 'Off':
			GPIO.output(self.speedRelay, GPIO.HIGH)		# Fan Off
			GPIO.output(self.fanRelay, GPIO.HIGH)
		elif fan == 'Low':
			GPIO.output(self.speedRelay, GPIO.HIGH)		# Fan Low
			GPIO.output(self.fanRelay, GPIO.LOW)
		elif fan == 'High':
			GPIO.output(self.speedRelay, GPIO.LOW)		# Fan High
			GPIO.output(self.fanRelay, GPIO.LOW)
		elif fan == 'Auto':
			now = datetime.datetime.now().hour
			weekday = datetime.datetime.today().weekday()
			if now >= SCHEDULE[0] and now <= SCHEDULE[1] and weekday >= SCHEDULE[2] and weekday <= SCHEDULE[3]:		# During the schedule period
				if temp >= therm + TEMP_DIFFERENTIAL:
					if temp >= therm + TEMP_DIFFERENTIAL + 2:		# If it's very warm, turn fan to High
						self.speed = GPIO.LOW
					GPIO.output(self.speedRelay, self.speed)		# Fan on to variable speed
					GPIO.output(self.fanRelay, GPIO.LOW)

				elif temp <= therm - TEMP_DIFFERENTIAL:
					self.speed = GPIO.HIGH
					GPIO.output(self.speedRelay, GPIO.HIGH)		# Fan Off
					GPIO.output(self.fanRelay, GPIO.HIGH)
			else:
				self.speed = GPIO.HIGH
				GPIO.output(self.speedRelay, GPIO.HIGH)			# Fan Off
				GPIO.output(self.fanRelay, GPIO.HIGH)

		if pump == 'Off':
			GPIO.output(self.pumpRelay, GPIO.HIGH)
		elif pump == 'On':
			GPIO.output(self.pumpRelay, GPIO.LOW)
		elif pump == 'Auto':
			now = datetime.datetime.now().hour
			weekday = datetime.datetime.today().weekday()
			if now >= SCHEDULE[0] and now <= SCHEDULE[1] and weekday >= SCHEDULE[2] and weekday <= SCHEDULE[3]:		# During the schedule period
				GPIO.output(self.pumpRelay, GPIO.LOW)		# Pump on
			else:
				GPIO.output(self.pumpRelay, GPIO.HIGH)		# Pump off

		if self.config['DEFAULT']['LogBool']:
			if self.logCounter >= 1800:		# Log every 30 minutes
				self.logCounter = 0
				self.logTemp(temp, hum, pres)
			else:
				self.logCounter += 1

		self.after(1000, self.thermostat)

	def logTemp(self, t, h, p):
		'''
		Logs current temperature to file
		'''
		file = Path.cwd() / 'tempLog.txt'
		now = datetime.datetime.now()
		with open(file, 'a+') as f:
			f.write(f'{now}, {t}, {h}, {p}')

	def onClosing(self, *args):
		if messagebox.askokcancel('Quit', 'Do you want to quit?'):
			self.fanVar.set('Off')
			self.pumpVar.set('Off')
			GPIO.output(self.pumpRelay, GPIO.HIGH)
			GPIO.output(self.speedRelay, GPIO.HIGH)
			GPIO.output(self.fanRelay, GPIO.HIGH)
			with open('config.ini', 'w') as f:
				self.config.write(f)
			self.destroy()


if __name__ == "__main__":
	app = Program()				# Init the class
	app.mainloop()				# Start the program and keep is running
