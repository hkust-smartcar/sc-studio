'''
sc_studio.config

Author: Ming Tsang
Copyright (c) 2014-2015 HKUST SmartCar Team
Refer to LICENSE for details
'''

# Comment out to disable logging
LOGFILE = "scstudio.log"
REMOTE_DEBUG = False
PYSRC = ""

COL_GREY_100 = "#F5F5F5"
COL_GREY_200 = "#EEEEEE"
COL_GREY_900 = "#212121"

MSG_BEGIN = 0xDC
MSG_END = 0xCD
MSG_NOP = 0
MSG_STRING = 1
MSG_CCD_DATA = 2
MSG_CAMERA = 3
MSG_TOKENS = [MSG_STRING, MSG_CCD_DATA, MSG_CAMERA]
