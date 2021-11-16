import argparse
import time
import logging
import numpy as np
import platform
import pyfirmata
from scipy.signal import find_peaks
from collections import deque
from KeytestStyrning import *
#import pyqtgraph as pg
#from pyqtgraph.Qt import QtGui, QtCore
#import pyqtgraph.ptime as ptime

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowFunctions, DetrendOperations
from brainflow.ml_model import BrainFlowMetrics, BrainFlowClassifiers, BrainFlowModelParams, MLModel

import matplotlib
if platform.system() == 'Darwin': # Set backend for MacOS.
	matplotlib.use('TKAgg')
from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec
logging.getLogger('matplotlib').disabled = True

programName = 'BrainGame Curiosum'
fps = -1
lastTime = time.time()
Labyrint = LabyrintStyrning()
class BlitManager:
	def __init__(self, canvas, animated_artists=()):
		"""
		Parameters
		----------
		canvas : FigureCanvasAgg
		The canvas to work with, this only works for sub-classes of the Agg
		canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
		`~FigureCanvasAgg.restore_region` methods.
		animated_artists : Iterable[Artist]
		List of the artists to manage
		"""
		self.canvas = canvas
		self._bg = None
		self._artists = []

		for a in animated_artists:
			self.add_artist(a)
		# grab the background on every draw
		self.cid = canvas.mpl_connect("draw_event", self.on_draw)

	def on_draw(self, event):
		"""Callback to register with 'draw_event'."""
		cv = self.canvas
		if event is not None:
			if event.canvas != cv:
				raise RuntimeError
		self._bg = cv.copy_from_bbox(cv.figure.bbox)
		self._draw_animated()

	def add_artist(self, art):
		"""
		Add an artist to be managed.
		Parameters
		----------
		art : Artist
		The artist to be added.  Will be set to 'animated' (just
		to be safe).  *art* must be in the figure associated with
		the canvas this class is managing.
		"""
		if art.figure != self.canvas.figure:
			raise RuntimeError
		art.set_animated(True)
		self._artists.append(art)

	def _draw_animated(self):
		"""Draw all of the animated artists."""
		fig = self.canvas.figure
		for a in self._artists:
			fig.draw_artist(a)

	def update(self):
		"""Update the screen with animated artists."""
		cv = self.canvas
		fig = cv.figure
		# paranoia in case we missed the draw event
		if self._bg is None:
			self.on_draw(None)
		else:
			# restore the background
			cv.restore_region(self._bg)
			# draw all of the animated artists
			self._draw_animated()
			# update the GUI state
			cv.blit(fig.bbox)
		# let the GUI event loop process anything it has to do
		cv.flush_events()

class Graph:
	def __init__(self, board_shim, settings):
		"""Initialize."""
		# Save board parameters.
		self.board_id = board_shim.get_board_id()
		self.board_shim = board_shim
		self.eeg_channels = BoardShim.get_eeg_channels(self.board_id)
		self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
		self.window_size = 5
		self.num_points = self.window_size * self.sampling_rate
		self.timestamp_channel = BoardShim.get_timestamp_channel(self.board_id)

		# Allocate arrays for data and time.
		self.data = np.zeros((BoardShim.get_num_rows(self.board_id), self.num_points))
		self.time = list(reversed(-np.arange(0, self.num_points)/self.sampling_rate))

		# Game settings.
		self.no_gui = settings['no_gui']
		self.game_mode = settings['game_mode']
		self.num_players = settings['num_players']
		self.active_channels = settings['active_channels']
		if self.active_channels is None:
			self.active_channels = self.eeg_channels

		# Allocate deque for tracking average band power.
		self.avg_band_power = deque([], maxlen=100)
		avg = list()
		for i in range(self.num_players):
			avg.append(np.zeros(5))
		self.avg_band_power.append(avg)
		self.count = 0
		self.lastcount = 0
		self.old_peaks = [[],[]]
		self.position_1 = 0
		self.position_2 = 0
		# Allocate deques for each player metric.
		self.metrics = list()
		self.metric_times = list()
		for i in range(self.num_players):
			m = deque([0], maxlen=self.num_points)
			t = deque([time.time()], maxlen=self.num_points)
			self.metrics.append(m)
			self.metric_times.append(t)

		# Limit no. of channels if testing with synthetic data
		if self.board_id == BoardIds.SYNTHETIC_BOARD:
			self.eeg_channels = [1, 2, 3, 4, 5, 6, 7, 8]

		# Initialize plots
		if not self.no_gui:
			self._init_plot()
		else:
			time.sleep(1) # ONLY TEMPORARY

		# Initialize ML models
		self._init_ml_model()

		print("----INITIALIZATION COMPLETED----")

		# Update plots, until program end.
		self.running = True
		now = time.time()
		while self.running:
			# Gather data and update everything.
			self.update()

			# Limit update frequency if needed.
			lastTime = now
			now = time.time()
			dt = now-lastTime
			if dt <= 1/self.sampling_rate:
				time.sleep(1/self.sampling_rate - dt)

	def _init_plot(self):
		"""Initialize the time series and associated plots."""
		# Window limits of time series plot.
		ylim = 200 * 1.1
		fsize = 8   # Fontsize
		lsize = 0.8 # Line width

		# Set color cycle.
		colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

		# Create a figure.
		fig = plt.figure(constrained_layout=True, num=programName)

		self.ln_timeseries = list()
		self.ln_ftt = list()
		self.ln_band = list()
		self.ln_focus = list()
		self.barplots = list()

		# Set up figure according to the game mode.
		if self.game_mode == 'analysis':
			num_channels = len(self.eeg_channels)
			# Set gridspec for custom subplot layout.
			gs = GridSpec(num_channels, 2, figure=fig)

			# Create axes for the figure.
			# Left column
			axes = []
			for i in range(num_channels):
				ax = fig.add_subplot(gs[i, 0])
				axes.append(ax)
			# Right column
			ax = fig.add_subplot(gs[:int(num_channels/4), 1])
			axes.append(ax)
			ax = fig.add_subplot(gs[int(num_channels/4):int(num_channels/2), 1])
			axes.append(ax)
			ax = fig.add_subplot(gs[int(num_channels/2):int(num_channels*3/4), 1])
			axes.append(ax)
			ax = fig.add_subplot(gs[int(num_channels*3/4):, 1])
			axes.append(ax)

			# Add all lines
			for i, ax in enumerate(axes):
				if i < num_channels: # Time series graphs.
					(ln_tmp,) = ax.plot(self.time, self.data[self.eeg_channels[i]],
					                    animated=True, linewidth=lsize, color=colors[i%10])
					self.ln_timeseries.append(ln_tmp)
					ax.set_ylim(-ylim, ylim)
					ax.set_xlim(np.min(self.time)*1.001, np.max(self.time))
					ax.set_ylabel("Pot (uV)", fontsize=fsize)
					if i == len(self.eeg_channels)-1:
						ax.set_xlabel("Time (s)", fontsize=fsize)
				elif i == num_channels: # FFT-graph.
					(ln_tmp,) = ax.plot(self.time, self.data[self.eeg_channels[0]],
					                    animated=True, linewidth=lsize, color=colors[i%10])
					self.ln_ftt.append(ln_tmp) # only temp
					#(ln_tmp,) = ax.plot([0], self.metric, animated=True, linewidth=0.8, color=colors[i%10]) # TODO: CHANGE THIS HERE
				elif i == num_channels+1: # Avg band power.
					barcontainer = ax.bar(list(range(5)), np.ones(5), animated=True)
					for i, b in enumerate(barcontainer):
						b.set_color(colors[i])
						self.ln_band.append(b)

					self.barplots.append(barcontainer)
					ax.set_yscale('log')
					ax.set_ylim(1, 100)
					ax.set_xticks(list(range(5)))
					ax.set_xticklabels(['Delta\n1-4Hz', 'Theta\n4-8Hz', 'Alpha\n8-13Hz', 'Beta\n13-30Hz', 'Gamma\n30-50Hz'])
				elif i == num_channels+2: # Focus metric.
					(ln_tmp,) = ax.plot([0], self.metrics[0], animated=True, linewidth=lsize, color=colors[i%10])
					self.ln_focus.append(ln_tmp)
					ax.set_ylim(-0.01, 1.01)
					ax.set_xlim(-10, 0)
					ax.set_ylabel('Metric value', fontsize=fsize)
					ax.set_xlabel("Time (s)", fontsize=fsize)
				else: # Other
					pass
				ax.tick_params(axis='x', labelsize=fsize)
				ax.tick_params(axis='y', labelsize=fsize)

		elif self.game_mode == 'game':
			num_rows = 4
			num_cols = self.num_players
			gs = GridSpec(num_rows, num_cols, figure=fig)
			axes = []
			for i in range(num_rows):
				for j in range(num_cols):
					ax = fig.add_subplot(gs[i, j])
					axes.append(ax)

			# Add all lines
			player_names = ['Player 1', 'Player 2', 'Player 3', 'Player 4']
			for i, ax in enumerate(axes):
				if i < num_cols: # Time series graph.
					(ln_tmp,) = ax.plot(self.time, self.data[self.active_channels[i]], animated=True, linewidth=lsize, color=colors[i//self.num_players])
					self.ln_timeseries.append(ln_tmp)
					ax.set_ylim(-ylim, ylim)
					ax.set_xlim(np.min(self.time)*1.001, np.max(self.time))
					ax.set_ylabel("Pot (uV)", fontsize=fsize)
					ax.set_xlabel("Time (s)", fontsize=fsize)
					ax.set_title(player_names[i])
				elif i < 2*num_cols: # FFT-graph
					(ln_tmp,) = ax.plot(self.time, self.data[self.active_channels[0]], animated=True, linewidth=lsize, color=colors[i//self.num_players])
					self.ln_ftt.append(ln_tmp) # only temp
				elif i < 3*num_cols: # Avg band power.
					barcontainer = ax.bar(list(range(5)), np.ones(5), animated=True)
					for i, b in enumerate(barcontainer):
						b.set_color(colors[i])
						self.ln_band.append(b)
					self.barplots.append(barcontainer)
					ax.set_yscale('log')
					ax.set_ylim(10**-5, 10*2)
					ax.set_ylabel('Power (uV)^2/Hz', fontsize=fsize)
					ax.set_xticks(list(range(5)))
					ax.set_xticklabels(['Delta\n1-4Hz', 'Theta\n4-8Hz', 'Alpha\n8-13Hz', 'Beta\n13-30Hz', 'Gamma\n30-50Hz'])
				else: # Focus metric.
					(ln_tmp,) = ax.plot([0], self.metrics[i%num_cols], animated=True, linewidth=lsize, color=colors[i//self.num_players])
					self.ln_focus.append(ln_tmp)
					ax.set_ylim(-0.01, 1.01)
					ax.set_xlim(-10, 0)
					ax.set_ylabel('Metric value', fontsize=fsize)
					ax.set_xlabel("Time (s)", fontsize=fsize)

				ax.tick_params(axis='x', labelsize=fsize)
				ax.tick_params(axis='y', labelsize=fsize)

			self.num_rows = num_rows
			self.num_cols = num_cols
		else:
			raise ValueError(f"Invalid option {self.game_mode}")

		# Save axis.
		self.axes = axes

		# Add an FPS counter
		self.fr_number = plt.suptitle("0")

		# Create the blitting manager, save all artists
		artists = self.ln_timeseries+self.ln_ftt+self.ln_band+self.ln_focus+[self.fr_number]
		self.bm = BlitManager(fig.canvas, artists)

		# Make sure the window is on the screen and drawn
		plt.show(block=False)
		plt.pause(0.1)

		# Set trigger when when window is closed.
		fig.canvas.mpl_connect('close_event', self._on_close)
		#fig.canvas.manager.set_window_title(programName)

	def _on_close(self, event):
		"""Tasks to perform on app closing event."""
		self.running = False

	def _init_ml_model(self):
		"""Initialize a brainflow machine learning model."""
		# Set model parameters.
		model_params = BrainFlowModelParams(BrainFlowMetrics.RELAXATION, BrainFlowClassifiers.REGRESSION)
		# Create the model.
		model = MLModel(model_params)
		# Set log level and prepare the classifier.
		model.enable_ml_logger()
		model.prepare()
		# Save the classifer with its parameters.
		self.model = model
		self.model_params = model_params

	def remove_ml_model(self):
		self.model.release()

	def update(self):
		# Get data from board
		data = self.board_shim.get_current_board_data(self.num_points)

		# Data filtering.
		self.filter_data(data)

		# Data processing:
		# PERFORM FAST FOURIER TRANSFOR ON DATA
		#for i, channel in enumerate(self.eeg_channels):
		#	# Fast Fourier Transform:
		#	# FFT-alg can only accept an array with lenght equal to a power of 2.
		#	length = data.shape[1]
		#	n = smallest_power(length)
		#	freq = DataFilter.perform_fft(data[channel, length-n:], WindowFunctions.HANNING)
#		print(freq.shape)

		#self.get_fft(data)

		# Calculate average band power.
		self.get_band_power(data)

		# Get metric prediction from the ML model
		self.get_metric(data)

		# Merge into self.data
		series_len = data.shape[1]
		self.data[:, (self.num_points-series_len):] = data

		# Update graphs:
		if not self.no_gui:
			# Update the artists
			self.update_artists()

			# Tell the blitting manager to do its thing
			self.bm.update()

		# Calculate frames per second
		self.calc_fps()

		# Print info to terminal
		self.print_info()

	def update_artists(self):
		"""Update all artists in the graph."""
		global fps
		# Time series plots
		for i, ln in enumerate(self.ln_timeseries):
			ln.set_ydata(self.data[self.active_channels[i]])
		# FFT
		for i, ln in enumerate(self.ln_ftt):
			pass

		# Average band power
		for i, barcontainer in enumerate(self.barplots):
			for j, b in enumerate(barcontainer):
				b.set_height(self.current_band_power[i, j])
		# Focus metric
		for i, ln in enumerate(self.ln_focus):
			relative_time = np.array(self.metric_times[i])-self.metric_times[i][-1]
			ln.set_ydata(self.metrics[i])
			ln.set_xdata(relative_time)
		# FPS counter
		self.fr_number.set_text(f"{fps:0.2f} fps")

	def filter_data(self, data):
		# Only filter active channels.
		for i, channel in enumerate(self.active_channels):
			# Constant detrend, i.e. center data at y = 0
			DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
			# Notch filter, remove 50Hz AC interference.
			DataFilter.remove_environmental_noise(data[channel], self.sampling_rate, NoiseTypes.FIFTY)
			# Bandpass filter
			DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
			                            FilterTypes.BUTTERWORTH.value, 0)
			#DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
			#                            FilterTypes.BUTTERWORTH.value, 0)
			#DataFilter.perform_bandstop(data[channel], self.sampling_rate, 50.0, 4.0, 2,
			#                            FilterTypes.BUTTERWORTH.value, 0)
			#DataFilter.perform_bandstop(data[channel], self.sampling_rate, 60.0, 4.0, 2,
			#                            FilterTypes.BUTTERWORTH.value, 0)

	def get_band_power(self, data):
		"""
		Calculate average band power from the time series data. 5 Bands:
		1-4Hz, 4-8Hz, 8-13Hz, 13-30Hz, 30-50Hz.
		"""
		avg_bp = list()
		if self.game_mode == 'game':
			for i in range(self.num_players):
				channel = self.active_channels[i]
				avg, std = DataFilter.get_avg_band_powers(data, [channel], self.sampling_rate, True)
				avg_bp.append(avg)
		elif self.game_mode == 'analysis':
			avg, std = DataFilter.get_avg_band_powers(data, self.active_channels, self.sampling_rate, True)
			avg_bp.append(avg)
		else:
			raise ValueError(f"Invalid option {self.game_mode}")
		self.avg_band_power.append(avg_bp)
		self.current_band_power = np.array(self.avg_band_power).mean(0)

	def get_metric(self, data):
		self.current_metrics = list()
		if self.game_mode == 'game':
			for i, channel in enumerate(self.active_channels):
				# Get metric estimate.
				bands = DataFilter.get_avg_band_powers(data, [channel], self.sampling_rate, True)
				feature_vector = np.concatenate((bands[0], bands[1]))
				metric = self.model.predict(feature_vector)
				self.metrics[i].append(metric)
				# Get time corresponding to the metric value.
				metric_time = data[self.timestamp_channel, -1]
				self.metric_times[i].append(metric_time)

				self.current_metrics.append(metric)
		elif self.game_mode == 'analysis':
			# Get metric prediction from the ML model
			bands = DataFilter.get_avg_band_powers(data, self.eeg_channels, self.sampling_rate, True)
			feature_vector = np.concatenate((bands[0], bands[1]))
			metric = self.model.predict(feature_vector)
			self.metrics[0].append(metric)

			# Get time and append to the appropriate list
			metric_time = data[self.timestamp_channel, -1]
			self.metric_times[0].append(metric_time)

			self.current_metrics.append(metric)
		else:
			raise ValueError(f"Invalid option {self.game_mode}")

	def calc_fps(self):
		"""Calculate frames per second."""
		global fps, lastTime
		now = time.time()
		dt = now - lastTime
		lastTime = now
		if fps == -1:
			fps = 1.0/dt
		else:
			s = np.clip(dt*3., 0, 1)
			fps = fps * (1-s) + (1.0/dt) * s

	def print_info(self):
		"""Print information to the terminal."""
		global fps
		names = ['one', 'two', 'three', 'four']
		#print(f" {fps:6.2f} fps, metric ({self.model_params.metric.name.lower()}):", end='')
		#for i in range(self.num_players):
		#	print(f' player_{names[i]} = {self.current_metrics[i]:.3f}', end='')
		#print('', end='\r')
		#n = self.num_points

		# for every player
		for i in range(self.num_players):
			x = self.metrics[i]
			peaks, _ = find_peaks(x, height=0.950, width = 70)

			# For every peak
			for peak in peaks:
				if self.old_peaks[i]:
					t = self.metric_times[i][peak]
					comparison = np.abs(t - np.array(self.old_peaks[i]))
					min_dt = np.min(comparison)

					if min_dt < 15/self.sampling_rate:

						#SAMPLING_RATE = 250
						#DO NOTHING GO TO NEXT PEAK
						#print("NO APPEND")
						pass
						# Samma peak som tidigare
					else:
					# Ny peak
						if i == 0:
							self.old_peaks[i].append(t)
							print('YES APPEND')
							if self.position_1 == 0:
								Labyrint.turn_left(1)
								self.position_1 = 1
							elif self.position_1 == 1:
								Labyrint.turn_right(1)
								self.position_1 = 0
						else: # SECOND PLAYER
							self.old_peaks.append(t)
							print('YES APPEND')
							if self.position_2 == 0:
								Labyrint.turn_left(2)
								self.position_2 = 1
							elif self.position_2 == 1:
								Labyrint.turn_right(2)
								self.position_2 = 0


				else:
					if i == 0:
						self.old_peaks[i].append(self.metric_times[i][peak])
						#print("OLD PEAKS OG = ",self.old_peaks)
						print("OG APPEND PLAYER ONE")
						Labyrint.turn_right(1)
						self.position_1 = 0
					else:
						self.old_peaks[i].append(self.metric_times[i][peak])
						#print("OLD PEAKS OG = ",self.old_peaks)
						print("OG APPEND PLAYER TWO")
						Labyrint.turn_right(2)
						self.position_2 = 0

def smallest_power(x):
	"""Return the smallest power of 2, smaller than or equal to x."""
	return 0 if x == 0 or x == 1 else  1<<(x.bit_length()-1)

def main():
	# Set logging level.
	BoardShim.enable_dev_board_logger()
	#logging.basicConfig(level=logging.DEBUG)

	# Parse command line arguments. Use docs to check which parameters are
	# required for specific board, e.g. for Cyton - set serial port.
	parser = argparse.ArgumentParser()
	# Board options:
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
	parser.add_argument('--board-id',        type=int, required=False, default=BoardIds.SYNTHETIC_BOARD, help='Board id, check docs to get a list of supported boards.')
	# Game options:
	parser.add_argument('--no-gui', type=bool, required=False, default=False, help='Run program without GUI.')
	parser.add_argument('--game-mode', type=str, required=False, default='game', choices=['game', 'analysis'], help="Mode: Game (single-/multiplayer) or evaulation/analysis (only singleplayer).")
	parser.add_argument('--num-players', type=int, required=False, default=2, choices=[1, 2, 3, 4], help="In game mode: Number of players.")
	parser.add_argument('--custom_channels', type=list[int], required=False, default=None, help='In game mode: custom channels for each player. Defaults to channels 1 to num_players.')
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

	# Set active channels
	if args.custom_channels is not None:
		active_channels = args.custom_channels
	elif args.game_mode == 'game':
		active_channels = list(range(1, args.num_players+1))
	else:
		active_channels = None

	# Game settings.
	settings = {
		'no_gui': args.no_gui,
		'game_mode': args.game_mode,
		'num_players': args.num_players if args.game_mode == 'game' else 1,
		'active_channels': active_channels
	}

	g = None
	try:
		# Initialize board and prepare session.
		board_shim = BoardShim(args.board_id, params)
		board_shim.prepare_session()

		# Set board to "differential mode." See: https://docs.openbci.com/Cyton/CytonSDK/#channel-setting-commands
		# x (CHANNEL, POWER_DOWN, GAIN_SET, INPUT_TYPE_SET, BIAS_SET, SRB2_SET, SRB1_SET) X
		# channel 1,2 "differential mode", channel 3-8 off.
		#ch_settings = ["x1060100X", "x2060100X", "x3161000X", "x4161000X",
		#               "x5161000X", "x6161000X", "x7161000X", "x8161000X"]
		if board_shim.board_id == BoardIds.CYTON_BOARD:
			if settings['game_mode'] == 'game':
				# Set active channels to "differential mode", turn off others.
				ch_settings = []
				opt_channel_on  = "060100X"
				opt_channel_off = "161000X"
				for i in range(1,len(BoardShim.get_eeg_channels(board_shim.board_id))+1):
					s = f'x{i}'
					if i in settings['active_channels']:
						ch_settings.append(s+opt_channel_on)
					else:
						ch_settings.append(s+opt_channel_off)
				board_shim.config_board(''.join(ch_settings))

		# Start session.
		board_shim.start_stream(450000, args.streamer_params)

		# Start plotting.
		g = Graph(board_shim, settings)

	except BaseException as e:
		# Error handling.
		logging.warning('Exception', exc_info=True)
		if g is not None:
			g.remove_ml_model()

	finally:
		# End session.
		if g is not None:
			g.remove_ml_model()
		logging.info('End')
		if board_shim.is_prepared():
			logging.info('Releasing session')
			board_shim.release_session()


if __name__ == '__main__':
	main()
