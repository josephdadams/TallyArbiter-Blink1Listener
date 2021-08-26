## Tally Arbiter Blink(1) Listener

# File name: tallyarbiter-blink1listener.py
# Version: 1.1.0
# Author: Joseph Adams
# Email: josephdadams@gmail.com
# Date created: 7/01/2020
# Date last modified: 8/26/2021
# Notes: This file is a part of the Tally Arbiter project. For more information, visit tallyarbiter.com

from signal import signal, SIGINT
from sys import exit
import sys
import time
from blink1.blink1 import Blink1
import socketio
import json

version = '1.1.0'

devices = []
device_states = []
bus_options = []

server = sys.argv[1]

try:
	stored_deviceId_file = open('deviceid.txt')
	stored_deviceId = stored_deviceId_file.read()
	stored_deviceId_file.close()
except IOError:
	stored_deviceId = ''

print('Last Used Device Id: ' + stored_deviceId)

if len(sys.argv) > 2:
	port = sys.argv[2]
else:
	port = '4455'

if len(sys.argv) > 3:
	deviceId = sys.argv[3]
else:
	if (stored_deviceId != ''):
		deviceId = stored_deviceId
	else:
		deviceId = 'null'

#SocketIO Connections
sio = socketio.Client()

@sio.event
def connect():
	print('Connected to Tally Arbiter server:', server, port)
	sio.emit('bus_options')											# get current bus options
	sio.emit('device_listen_blink', {'deviceId': deviceId})			# start listening for the device
	repeatNumber = 2
	while(repeatNumber):
		repeatNumber = repeatNumber - 1
		doBlink(0, 255, 0)
		time.sleep(.3)
		doBlink(0, 0, 0)
		time.sleep(.3)

@sio.event
def connect_error(data):
	print('Unable to connect to Tally Arbiter server:', server, port)
	doBlink(150, 150, 150)
	time.sleep(.3)
	doBlink(0, 0, 0)
	time.sleep(.3)

@sio.event
def disconnect():
	print('Disconnected from Tally Arbiter server:', server, port)
	doBlink(255, 255, 255)
	time.sleep(.3)
	doBlink(0, 0, 0)
	time.sleep(.3)

@sio.event
def reconnect():
	print('Reconnected to Tally Arbiter server:', server, port)
	repeatNumber = 2
	while(repeatNumber):
		repeatNumber = repeatNumber - 1
		doBlink(0, 255, 0)
		time.sleep(.3)
		doBlink(0, 0, 0)
		time.sleep(.3)

@sio.on('devices')
def on_devices(data):
	global devices
	devices = data

@sio.on('device_states')
def on_device_states(data):
	global device_states
	device_states = data
	processTallyData()

@sio.on('bus_options')
def on_bus_options(data):
	global bus_options
	bus_options = data

@sio.on('flash')
def on_flash():
	doBlink(255, 255, 255)
	time.sleep(.5)
	doBlink(0, 0, 0)
	time.sleep(.5)
	doBlink(255, 255, 255)
	time.sleep(.5)
	doBlink(0, 0, 0)
	time.sleep(.5)
	doBlink(255, 255, 255)
	time.sleep(.5)
	processTallyData()

@sio.on('error')
def on_error(errorMessage):
	print(errorMessage)

@sio.on('reassign')
def on_reassign(oldDeviceId, newDeviceId):
	print('Reassigning from DeviceID: ' + oldDeviceId + ' to Device ID: ' + newDeviceId)
	doBlink(0, 0, 0)
	time.sleep(.1)
	doBlink(0, 0, 255)
	time.sleep(.1)
	doBlink(0, 0, 0)
	time.sleep(.1)
	doBlink(0, 0, 255)
	time.sleep(.1)
	doBlink(0, 0, 0)
	sio.emit('listener_reassign', data=(oldDeviceId, newDeviceId))
	global deviceId
	deviceId = newDeviceId
	stored_deviceId_file = open('deviceid.txt', 'w')
	stored_deviceId_file.write(newDeviceId)
	stored_deviceId_file.close()

def getDeviceById(deviceId):
	for device in devices:
		if device['id'] == deviceId:
			return device

def getBusTypeById(busId):
	for bus in bus_options:
		if bus['id'] == busId:
			return bus['type']

def getBusById(busId):
	for bus in bus_options:
		if bus['id'] == busId:
			return bus

def processTallyData():
	busses = []

	for device_state in device_states:
		if len(device_state['sources']) > 0:
			bus = getBusById(device_state['busId'])
			busses.append(bus)
	
	priority = 0
	tallyBus = []

	for bus in busses:
		if bus['priority'] > priority:
			priority = bus['priority']
			tallyBus = bus
	
	#this should leave us with a tallyBus object where the highest priority bus is in this object
	evaluateMode(tallyBus)

def evaluateMode(bus):
	global deviceId
	device = getDeviceById(deviceId)
	if len(bus) > 0:
		deviceName = device['name']
		print('{} is in: {}'.format(deviceName,bus['type']))
		color = hexToRGB(bus['color'])
		doBlink(color[0], color[1], color[2])

def doBlink(r, g, b):
	b1.fade_to_rgb(100, r, g, b)

def hexToRGB(hex):
	hex = hex.lstrip('#')
	return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

try:
	b1 = Blink1()
except:
	print('No blink(1) devices found.')
	exit (0)

while(1):
	try:
		sio.connect('http://' + server + ':' + port)
		sio.wait()
		print('Tally Arbiter Blink(1) Listener Running. Version {}. Press CTRL-C to exit.'.format(version))
		print('Attempting to connect to Tally Arbiter server: ' + server + '(' + port + ')')
	except KeyboardInterrupt:
		print('Exiting Tally Arbiter Listener.')
		doBlink(0, 0, 0)
		exit(0)
	except socketio.exceptions.ConnectionError:
		doBlink(0, 0, 0)
		time.sleep(15)
	except:
		print("Unexpected error:", sys.exc_info()[0])
		print('An error occurred internally.')
		doBlink(0, 0, 0)