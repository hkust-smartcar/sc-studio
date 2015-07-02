'''
sc_studio.camera_view

Author: Ming Tsang
Copyright (c) 2014-2015 HKUST SmartCar Team
Refer to LICENSE for details
'''

import binascii
import logging
import os
from PIL import Image, ImageOps, ImageTk
import time
import tkinter
from tkinter import Tk, Canvas
from sc_studio.view import View

class CameraView(View):
	def __init__(self, params):
		super(CameraView, self).__init__(params)

		self._multiplier = int(params["multiplier"]) if "multiplier" in params \
				else 1
		self._multiplier = max(self._multiplier, 1)

		self._tk = Tk()
		self._canvas = Canvas(self._tk, width = 80 * self._multiplier,
				height = 60 * self._multiplier)

		self._tk.title("Camera view")
		self._tk.resizable(width = False, height = False)
		self._canvas.pack(side = tkinter.LEFT, fill = tkinter.BOTH,
				expand = True)

		self._tk.protocol("WM_DELETE_WINDOW", self.on_press_close)

		self._base_dir = "camera_" + str(int(time.time() * 1000))
		os.makedirs(self._base_dir)

	def run(self):
		super(CameraView, self).run()
		self._tk.mainloop()

	def on_new_input(self):
		try:
			hex_str = self.get_input()
			img = self._get_image(hex_str)
		except Exception as e:
			logging.debug(str(e))
			return
		if img is None:
			return

		bmp = ImageTk.BitmapImage(image = img, foreground = "white",
				background = "black")
		self._canvas.create_image(0, 0, image = bmp, anchor = tkinter.NW)
		self._tk_image = bmp

		img.save(self._base_dir + '/' + str(int(time.time() * 1000)) + ".png")

	def on_dismiss(self):
		self._tk.after_idle(self.on_press_close)

	def on_press_close(self):
		self._tk.destroy()
		self.join_io_thread()

	def _get_image(self, hex_str) -> Image:
		try:
			hex_data = binascii.unhexlify(hex_str)
			# Invert data from MCU
			hex_data = bytes([~h & 0xFF for h in hex_data])
		except TypeError as e:
			logging.debug(str(e))
			return

		img = Image.frombytes(mode = '1', size = (80, 60), data = hex_data)
		img = img.resize((80 * self._multiplier, 60 * self._multiplier))
		return img
