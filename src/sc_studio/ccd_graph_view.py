'''
sc_studio.ccd_graph_view

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

class CcdGraphView(View):
	def __init__(self, params):
		super(CcdGraphView, self).__init__(params)

		self._ccd_id = int(params["ccd_id"]) if "ccd_id" in params else 0

		self._tk = Tk()
		self._text = Text(self._tk, height = CcdGraphView._HEIGHT + 1,
				width = 128, bg = config.COL_GREY_900, fg = config.COL_GREY_100,
				font = ("Courier", 8))

		self._tk.title("CCD graph view [" + str(self._ccd_id) + ']')
		self._tk.resizable(width = False, height = False)
		self._text.pack(side = tkinter.LEFT, fill = tkinter.Y)

		self._tk.protocol("WM_DELETE_WINDOW", self.on_press_close)

		self._file = open("ccd_graph_" + str(self._ccd_id) + '_' \
				+ str(int(time.time() * 1000)), "w")

	def run(self):
		super(CcdGraphView, self).run()
		self._tk.mainloop()

	def on_new_input(self):
		try:
			hex_str = self.get_input()
			if int(hex_str[0:2], 16) != self._ccd_id:
				return
			display = self._get_display_list(hex_str[2:])
		except Exception as e:
			logging.debug(str(e))
			return

		self._file.write(time.strftime("[%x %X]\n"))
		self._text.delete(1.0, tkinter.END)
		for line in display:
			string = line.decode("UTF-8")
			self._text.insert(tkinter.END, string)
			self._file.write(string)
			self._file.write('\n')

	def on_dismiss(self):
		self._tk.after_idle(self.on_press_close)

	def on_press_close(self):
		self._tk.destroy()
		self.join_io_thread()

	def _get_display_list(self, hex_str):
		display = [bytearray(b' ' * 128) for i in range(CcdGraphView._HEIGHT)]
		try:
			hex_data = binascii.unhexlify(hex_str)
		except TypeError as e:
			logging.debug(str(e))
			return

		for i in range(128):
			row = int(CcdGraphView._HEIGHT - 1 - hex_data[i] \
					/ CcdGraphView._GROUP_WIDTH);
			display[row][i] = ord('#');
		return display

	_HEIGHT = 26
	_GROUP_WIDTH = 10
