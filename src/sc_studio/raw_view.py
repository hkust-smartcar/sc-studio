'''
sc_studio.raw_view

Author: Ming Tsang
Copyright (c) 2014-2015 HKUST SmartCar Team
Refer to LICENSE for details
'''

import sys
import time
import tkinter
from tkinter import Tk, Scrollbar, Text
from sc_studio import config
from sc_studio.view import View

class RawView(View):
	def __init__(self, params):
		super(RawView, self).__init__(params)

		self._tk = Tk()
		self._scroll = Scrollbar(self._tk)
		self._text = Text(self._tk, bg = config.COL_GREY_900,
				fg = config.COL_GREY_100)

		self._tk.title("Fallback view")
		self._scroll.pack(side = tkinter.RIGHT, fill = tkinter.Y)
		self._scroll.config(command = self._text.yview)
		self._text.config(yscrollcommand = self._scroll.set)
		self._text.pack(side = tkinter.LEFT, fill = tkinter.Y)

	def run(self):
		super(RawView, self).run()
		self._append_text()
		self._tk.mainloop()

	def _append_text(self):
		self._tk.after(100, self._append_text)
		i = 0
		text = ""
		while self._input_queue and i < 10:
			++i
			text += super(RawView, self).get_input()
		if not text:
			return

		is_bottom = (self._scroll.get()[1] == 1.0)
		self._text.insert(tkinter.END, text)
		if is_bottom:
			self._text.yview(tkinter.END)
			
	def _io_thread_main(self):
		while self._is_thread_run:
			text = sys.stdin.read(50)
			self._input_queue_mutex.acquire()
			try:
				self._input_queue.append(text)
			finally:
				self._input_queue_mutex.release()
			self.on_new_input()
