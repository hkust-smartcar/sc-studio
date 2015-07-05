'''
sc_studio.string_view

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

class StringView(View):
	def __init__(self, params):
		super(StringView, self).__init__(params)

		self._tk = Tk()
		self._text = Text(self._tk, bg = config.COL_GREY_900,
				fg = config.COL_GREY_100)

		self._tk.title("String view")
		self._text.pack(side = tkinter.LEFT, fill = tkinter.Y)

		self._tk.protocol("WM_DELETE_WINDOW", self.on_press_close)

		self._file = open("string_" + str(int(time.time() * 1000)) + ".txt", "w")

	def run(self):
		super(StringView, self).run()
		self._tk.mainloop()

	def on_new_input(self):
		try:
			hex_str = self.get_input()
			line = self._get_line(hex_str)
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
			return binascii.unhexlify(hex_str)
		except TypeError as e:
			logging.debug(str(e))
			return
