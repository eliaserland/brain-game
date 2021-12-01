import argparse
import time
import logging
import random
import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph.ptime as ptime

import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowFunctions, DetrendOperations

# My stuff
import matplotlib.pyplot as plt

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

programName = 'BrainGame Curiosum'
time_init = time.time()

from braingame import set_differential_mode

fps = None
lastTime = ptime.time()

class Graph:
	def __init__(self, board_shim):
		self.board_id = board_shim.get_board_id()
		self.board_shim = board_shim
		self.exg_channels = BoardShim.get_exg_channels(self.board_id)
		self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
		self.update_speed_ms = 10
		self.window_size = 5 
		self.num_points = self.window_size * self.sampling_rate
		self.time_stamp_channel = BoardShim.get_timestamp_channel(self.board_id)
		self.data = np.zeros((BoardShim.get_num_rows(self.board_id), self.num_points))
		self.time = list(reversed(-np.arange(0, self.num_points)/self.sampling_rate))
		

		print("NUM_POINTS = " + str(self.num_points))

		# ONLY TEMP
		self.exg_channels = [1, 2]
		

		self.app = QtGui.QApplication([])
		self.win = pg.GraphicsWindow(title=programName,size=(1200, 1000))
		# Enable antialiasing for prettier plots
		#pg.setConfigOptions(antialias=True)


		self._init_timeseries()

		timer = QtCore.QTimer()
		timer.timeout.connect(self.update)
		timer.start(self.update_speed_ms)
		QtGui.QApplication.instance().exec_()


	def _init_timeseries(self):
		ylim = 20
		self.plots = list()
		self.curves = list()
		for j in range(2):
			for i in range(len(self.exg_channels)):
				p = self.win.addPlot(row=i,col=j)
				p.showAxis('left', True)
				p.setMenuEnabled('left', False)
				p.showAxis('bottom', True)
				p.setMenuEnabled('bottom', True)
				p.setYRange(-ylim, ylim, padding=5)

				p.setLabel('left', "Pot", units='uV')	
				p.setLabel('bottom', "Time", units='s')
				if i == 0:
					p.setTitle('TimeSeries Plot')
				self.plots.append(p)
				curve = p.plot(pen=pg.mkPen('k', width=2))
				self.curves.append(curve)

	def update(self):
		global fps, lastTime
		# Get data from board
		board_data = self.board_shim.get_current_board_data(self.num_points)

		series_len = board_data.shape[1]
		self.data[:, (self.num_points-series_len):] = board_data

		avg_bands = [0, 0, 0, 0, 0]

		for count, channel in enumerate(self.exg_channels):
			# plot timeseries
			#Center data
			DataFilter.detrend(self.data[channel], DetrendOperations.CONSTANT.value)
			DataFilter.detrend(self.data[channel], DetrendOperations.LINEAR.value)
			#Notch filter to remove AC power at 50 Hz 
			DataFilter.remove_environmental_noise(self.data[channel], self.sampling_rate, NoiseTypes.FIFTY)
			
			#bandpass (freq: 2-32, order: 4 (pretty high to fully remove 100 Hz)) 
			DataFilter.perform_bandpass(self.data[channel], self.sampling_rate, 50, 50, 2, FilterTypes.BUTTERWORTH.value, 0)

			#DataFilter.perform_wavelet_denoising(self.data[channel], 'coif3', 3)
			#Lowpass-filter (cutofffreq: 35, order 4)
			#DataFilter.perform_lowpass(self.data[channel], self.sampling_rate, 35.0, 4, FilterTypes.BUTTERWORTH.value, 0)
			DataFilter.perform_rolling_filter(self.data[channel], 3, AggOperations.MEDIAN.value)
			#DataFilter.perform_rolling_filter(self.data[channel],5 , AggOperations.MEAN.value)
			#Maybe could use bandstop
			DataFilter.perform_bandstop(self.data[channel], self.sampling_rate, 100, 2.0, 2,
										FilterTypes.BUTTERWORTH.value, 0)
			#DataFilter.perform_bandstop(self.data[channel], self.sampling_rate, 4, 4, 2,
			#							FilterTypes.BUTTERWORTH.value, 0)
			
		for i in range(2):
			for count, channel in enumerate(self.exg_channels):
				self.curves[count+i*2].setData(self.time, self.data[channel])
				
		#self.app.processEvents()

		now = ptime.time()
		dt = now - lastTime
		lastTime = now
		if fps is None:
			fps = 1.0/dt
		else:
			s = np.clip(dt*3., 0, 1)
			fps = fps * (1-s) + (1.0/dt) * s
		print('%0.2f fps' % fps)
		#self.app.processEvents()  ## force complete redraw for every plot

def main():
	# Set logging level.
	BoardShim.enable_dev_board_logger()
	logging.basicConfig(level=logging.DEBUG)

	# Parse command line arguments. Use docs to check which parameters are 
	# required for specific board, e.g. for Cyton - set serial port.
	parser = argparse.ArgumentParser()
	parser.add_argument('--timeout',     type=int, required=False, default=0, help='timeout for device discovery or connection',)
	parser.add_argument('--ip-port',     type=int, required=False, default=0, help='ip port',)
	parser.add_argument('--ip-protocol', type=int, required=False, default=0, help='ip protocol, check IpProtocolType enum')
	parser.add_argument('--ip-address',      type=str, required=False, default='', help='ip address')
	parser.add_argument('--serial-port',     type=str, required=False, default='', help='serial port')
	parser.add_argument('--mac-address',     type=str, required=False, default='', help='mac address')
	parser.add_argument('--other-info',      type=str, required=False, default='', help='other info')
	parser.add_argument('--streamer-params', type=str, required=False, default='', help='streamer params')
	parser.add_argument('--serial-number',   type=str, required=False, default='', help='serial number')
	parser.add_argument('--file',            type=str, required=False, default='', help='file')
	parser.add_argument('--board-id',        type=int, required=False, default=BoardIds.SYNTHETIC_BOARD, help='board id, check docs to get a list of supported boards')
	args = parser.parse_args()

	# Set parsed parameters in BrainFlowInputParams structure.
	params = BrainFlowInputParams()
	params.ip_port = args.ip_port
	params.serial_port = args.serial_port
	params.mac_address = args.mac_address
	params.other_info = args.other_info
	params.serial_number = args.serial_number
	params.ip_address = args.ip_address
	params.ip_protocol = args.ip_protocol
	params.timeout = args.timeout
	params.file = args.file

	try:
		# Start session.
		board_shim = BoardShim(args.board_id, params)
		board_shim.prepare_session()
        
		set_differential_mode(board_shim, [1,2])
        
		board_shim.start_stream(450000, args.streamer_params)
		
		# Start plotting.
		g = Graph(board_shim)
		
	except BaseException as e:
		# Error handling.
		logging.warning('Exception', exc_info=True)
	
	finally:
		# End session.
		logging.info('End')
		if board_shim.is_prepared():
			logging.info('Releasing session')
			board_shim.release_session()


if __name__ == '__main__':
	main()
