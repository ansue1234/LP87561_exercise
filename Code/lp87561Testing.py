# -*- coding: utf-8 -*-

# Author: Andrew Sue
# Date: 6/25/2020

"""
	Based on "My Raspberry Pi talks to my Oscilloscope" by scruss
	https://scruss.com/blog/2013/12/15/my-raspberry-pi-talks-to-my-oscilloscope/
""" 
 
import smbus
import usbtmc
import matplotlib.pyplot as plot
import numpy as np
import time
import RPi.GPIO as GPIO



# setup usbtmc to monitor wave, Rigol DS1102E specifically
scope = usbtmc.Instrument(0x1ab1, 0x0588) 

# Setup channel, address and register to write to
channel = 1
address = 0x62
reg_write = {"enable" : 0x02, "Vout" : 0x0A, "slew rate" : 0x03, "delay" : 0x12}

################# Regulator Setup #####################

# Initialize I2C (SMBus)
bus = smbus.SMBus(channel)

# Enable and setup Buck
bus.write_i2c_block_data(address, reg_write["enable"], [0xC4]) # Enable BUCK0 with EN1 control and enabled discharge resistor
bus.write_i2c_block_data(address, reg_write["slew rate"], [0x07]) # 0.47mV/us
bus.write_i2c_block_data(address, reg_write["delay"], [0x0F]) # 15ms
bus.write_i2c_block_data(address, reg_write["Vout"], [0x17]) # 0.73V

try: 
	scope.ask(":TIM:SCAL 0.5")
except:
	pass

################# GPIO on rpi ##########################

# Setting up GPIO Pin
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)
# trigger EN Pin
GPIO.output(11, GPIO.HIGH)
time.sleep(0.75)
GPIO.output(11, GPIO.LOW)



################# Scope control #######################

# stop and get raw data
scope.write(":WAV:POIN:MODE RAW")
raw1 = scope.ask(":WAV:DATA? CHAN1")[10:]
raw2 = scope.ask(":WAV:DATA? CHAN2")[10:]
raw_data_1 = bytes(raw1, 'utf-8')
raw_data_2 = bytes(raw2, 'utf-8')
size = max(len(raw1), len(raw2))


	
# get scale
x_scale = float(scope.ask(":TIM:SCAL?"))
y_scale = float(scope.ask(":CHAN1:SCAL?"))
x_offset = float(scope.ask(":TIM:OFFS?"))
y_offset = float(scope.ask(":CHAN1:OFFS?"))
sample_rt = float(scope.ask(":ACQ:SAMP?"))

################# Graphing data #######################

# form data points
def pts(raw_data):
	data = np.frombuffer(raw_data, 'B')
	data = data * -1 + 255
	data = (data -130.0 - y_offset/y_scale * 25) /25 * y_scale
	return data
	
chan1_data = pts(raw_data_1)
chan2_data = pts(raw_data_2)
time = np.linspace(x_offset - 6 * x_scale, x_offset + 6 * x_scale, num = max(len(chan1_data), len(chan2_data)))

if (time[-1] < 1e-3):
	time = time *1e6
	tUnit = "uS"
elif (time[-1] < 1):
	time = time * 1e3
	tUnit = "mS"
else:
	tUnit = "S"

# plotting data
plot.plot(time, chan1_data, label = "CHAN1-BUCK0")
plot.plot(time, chan2_data, label = "CHAN2-EN1")
plot.legend()
plot.title("scope output")
plot.ylabel("V")
plot.xlabel(tUnit)
plot.xlim(time[0], time[-1])
plot.grid(True)
plot.show()








