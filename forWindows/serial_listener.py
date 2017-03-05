import serial
import time
from PIL import Image
from PIL import ImageEnhance
import os
import requests

counter = 2

def button_pressed():
	global counter

	path = 'c:\\Users\\yuelun\\Pictures\\bmp1.bmp'
	save_path = 'c:\\Users\\yuelun\\Pictures\\jpg' + str(counter) + '.jpg'
	im = Image.open(path)
	enhancer = ImageEnhance.Color(im)
	im2 = enhancer.enhance(1.5)
	im2.save(save_path, 'JPEG')
	#.save(save_path, 'JPEG')

	url = 'https://twilio-160408.appspot.com/collect'
	# url = 'http://127.0.0.1:8080/collect'
	files = {'file':open(save_path, 'rb')}
	r = requests.post(url, files=files)
	print(r.status_code)
	counter+=1


def serial_listener():
	lastTrigger = 0

	ser = serial.Serial('COM5', 9600)

	while(1):
		if ser.read() == '1':
			if time.time()-lastTrigger > 3:
				button_pressed()
				lastTrigger = time.time()



if __name__ == '__main__':
	serial_listener()
