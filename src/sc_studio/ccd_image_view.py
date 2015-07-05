'''
sc_studio.ccd_image_view

Author: Ming Tsang
Copyright (c) 2014-2015 HKUST SmartCar Team
Refer to LICENSE for details
'''

import binascii
import logging
import time
import tkinter
from tkinter import Tk, Text
from sc_studio import config
from sc_studio.view import View

class CcdImageView(View):
	def __init__(self, params):
		super(CcdImageView, self).__init__(params)

		self._ccd_id = int(params["ccd_id"]) if "ccd_id" in params else 0
		self._threshold = params["threshold"] if "threshold" in params else 128

		self._tk = Tk()
		self._text = Text(self._tk, width = 128, bg = config.COL_GREY_900,
				fg = config.COL_GREY_100, font = ("Courier", 5))

		self._tk.title("CCD image view [" + str(self._ccd_id) + ']')
		self._text.pack(side = tkinter.LEFT, fill = tkinter.Y)

		self._tk.protocol("WM_DELETE_WINDOW", self.on_press_close)

		self._file = open("ccd_image_" + str(self._ccd_id) + '_' \
				+ str(int(time.time() * 1000)) + ".txt", "w")

	def run(self):
		super(CcdImageView, self).run()
		self._tk.mainloop()

	def on_new_input(self):
		try:
			hex_str = self.get_input()
			if int(hex_str[0:2], 16) != self._ccd_id:
				return
			line = self._get_line(hex_str[2:])
		except Exception as e:
			logging.debug(str(e))
			return

		string = line.decode("UTF-8")
		self._text.insert(tkinter.END, string)
		self._text.insert(tkinter.END, '\n')
		while self._text.yview()[1] != 1.0:
			self._text.delete(1.0, 2.0)

		self._file.write(time.strftime("[%x %X] "))
		self._file.write(string)
		self._file.write('\n')

	def on_dismiss(self):
		self._tk.after_idle(self.on_press_close)

	def on_press_close(self):
		self._tk.destroy()
		self.join_io_thread()

	def _get_line(self, hex_str):
		try:
			hex_data = binascii.unhexlify(hex_str)
		except TypeError as e:
			logging.debug(str(e))
			return

		line = bytearray(128)
		for i in range(128):
			line[i] = ord('#') if hex_data[i] > self._threshold else ord(' ')
		return line
