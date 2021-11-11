import argparse
import time
import logging
from typing import Any
import numpy as np
from collections import deque
import threading

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowFunctions, DetrendOperations
from brainflow.ml_model import BrainFlowMetrics, BrainFlowClassifiers, BrainFlowModelParams, MLModel

def parse_arguments():
	"""
	Parse command line arguments. Use brainflow docs to check which parameters 
	are required for any specific board, e.g. for Cyton - set serial port.
	"""
	parser = argparse.ArgumentParser()
	# BoardShim options:
	parser.add_argument('--timeout',     type=int, required=False, default=0, help='timeout for device discovery or connection',)
	parser.add_argument('--ip-port',     type=int, required=False, default=0, help='ip port',)
	parser.add_argument('--ip-protocol', type=int, required=False, default=0, help='ip protocol, check IpProtocolType enum')
	parser.add_argument('--ip-address',      type=str, required=False, default='', help='ip address')
	parser.add_argument('--serial-port',     type=str, required=False, default='', help='serial port')
	parser.add_argument('--mac-address',     type=str, required=False, default='', help='mac address')
	parser.add_argument('--other-info',      type=str, required=False, default='', help='other info')
	parser.add_argument('--serial-number',   type=str, required=False, default='', help='serial number')
	parser.add_argument('--file',            type=str, required=False, default='', help='file')
	# Streamer parameters:
	parser.add_argument('--streamer-params', type=str, required=False, default='', help='streamer params')
	# Board ID:
	parser.add_argument('--board-id',        type=int, required=False, default=BoardIds.SYNTHETIC_BOARD, help='Board id, check docs to get a list of supported boards.')
	# Game options:
	parser.add_argument('--custom_channels', type=list[int], required=False, default=None, help='In game mode: custom channels for each player. Defaults to channels 1 to num_players.')
	args = parser.parse_args()
	return args

def set_brainflow_input_params(args: argparse.Namespace):
	"""
	Set parsed parameters in BrainFlowInputParams structure. 
	"""
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
	return params

def set_active_channels(args: argparse.Namespace):
	"""
	Set which two channels of the BCI board to use. Defaults to 
	channels 1 and 2. 
	"""
	if args.custom_channels is None:
		active_channels = [1, 2] # default
	else:
		active_channels = args.custom_channels
	return active_channels

def set_differential_mode(board_shim: BoardShim, active_channels: list[int]):
	"""
	Set BCI board to 'differential mode', neccessary for multiplayer on a single
	board. For the Cyton board, we set channels 1,2 to "differential mode", 
	channels 3-8 to off. See: https://docs.openbci.com/Cyton/CytonSDK/#channel-setting-commands.
	x (CHANNEL, POWER_DOWN, GAIN_SET, INPUT_TYPE_SET, BIAS_SET, SRB2_SET, SRB1_SET) X
	"""
	#ch_settings = ["x1060100X", "x2060100X", "x3161000X", "x4161000X",
	#               "x5161000X", "x6161000X", "x7161000X", "x8161000X"]
	ch_settings = []
	opt_channel_on  = "060100X" # powered up, default gain, normal input, bias on, srbs off
	opt_channel_off = "161000X" # powered down, default gain, shorted input, bias off, srbs off
	for i in range(1, len(BoardShim.get_eeg_channels(board_shim.board_id))+1):
		base = f'x{i}' # channel no
		if i in active_channels:
			ch_settings.append(base+opt_channel_on)
		else:
			ch_settings.append(base+opt_channel_off)
	# Send configuration to the board.
	board_shim.config_board(''.join(ch_settings))

class Board:
	def __init__(self, board_shim: BoardShim, active_channels: list[int]):
		# Save board parameters.
		self.board_shim = board_shim
		self.board_id = board_shim.get_board_id()
		self.eeg_channels = BoardShim.get_eeg_channels(self.board_id)
		self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
		self.window_size = 5
		self.num_points = self.window_size * self.sampling_rate
		self.timestamp_channel = BoardShim.get_timestamp_channel(self.board_id)
		self.active_channels = active_channels
		# Limit no. of channels if testing with synthetic data
		if self.board_id == BoardIds.SYNTHETIC_BOARD:
			self.eeg_channels = [1, 2, 3, 4, 5, 6, 7, 8]

class AvgBandPower(Board):
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int):
		super().__init__(board_shim, active_channels)
		# Allocate deque for tracking average band power.
		self.avg_band_power = deque([], maxlen=100)
		self.avg_band_power.append(np.zeros(5))
		self.channel = channel

	def get_band_power(self, data: np.ndarray):
		"""
		Calculate average band power from the time series data. 5 Bands: 
		1-4Hz, 4-8Hz, 8-13Hz, 13-30Hz, 30-50Hz.
		"""
		avg, std = DataFilter.get_avg_band_powers(data, [self.channel], self.sampling_rate, True)
		self.avg_band_power.append(avg)
		current_band_power = np.array(self.avg_band_power).mean(0)
		return current_band_power

class MLClassifier:
	model = None
	model_params = None

	@classmethod
	def configure(cls, metric: BrainFlowMetrics=BrainFlowMetrics.RELAXATION, 
	             classifier: BrainFlowClassifiers=BrainFlowClassifiers.REGRESSION):
		if cls.model is not None:
			cls.destroy_model()
		cls.model_params = BrainFlowModelParams(metric, classifier)
		cls.model = MLModel(cls.model_params)
		cls.model.enable_ml_logger()
		cls.model.prepare()
		return cls
	
	@classmethod
	def destroy_model(cls):
		cls.model.release()
		cls.model = None
		cls.model_params = None

class FocusMetric(Board):
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int):
		super().__init__(board_shim, active_channels)
		self.metric = deque([0], maxlen=self.num_points) 
		self.time = deque([time.time()], maxlen=self.num_points)
		classifier = MLClassifier.configure() # TODO: GET INPUT FROM SETTINGS DIALOGUE
		self.model = classifier.model
		self.model_params = classifier.model_params
		self.channel = channel

	def get_metric(self, data: np.ndarray):
		# Get metric estimate. 
		bands = DataFilter.get_avg_band_powers(data, [self.channel], self.sampling_rate, True)
		feature_vector = np.concatenate((bands[0], bands[1]))
		metric = self.model.predict(feature_vector)
		self.metric.append(metric)
		# Get time corresponding to the metric value.
		time = data[self.timestamp_channel, -1]
		self.time.append(time)

		relative_time = np.array(self.time)-time
		return list(relative_time), list(self.metric)

class TimeSeries(Board):
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int):
		super().__init__(board_shim, active_channels)
		self.channel = channel
		self.time = list(reversed(-np.arange(0, self.num_points)/self.sampling_rate))
		self.timeseries = np.zeros(self.num_points)

	def get_time_series(self, data: np.ndarray):
		timeseries = data[self.channel]
		self.timeseries[(self.num_points-len(timeseries)):] = timeseries
		return  self.time, list(self.timeseries)

class Player:
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int):
		self.timeseries = TimeSeries(board_shim, active_channels, channel)
		self.bandp = AvgBandPower(board_shim, active_channels, channel)
		self.focus = FocusMetric(board_shim, active_channels, channel)

	def update(self, data: np.ndarray):
		# Calculate all derived quantities, such as band power, focus metric etc.
		time, timeseries = self.timeseries.get_time_series(data)
		band_power  = self.bandp.get_band_power(data)
		metric_time, metric  = self.focus.get_metric(data)
		# Collect all quantities to be plotted in a dictionary.
		player_info = {
			'time_series': (time, timeseries),
			'band_power': band_power,
			'focus_metric': (metric_time, metric)
		}
		return player_info

class FilterData(Board):
	def __init__(self, board_shim: BoardShim, active_channels: list[int]):
		super().__init__(board_shim, active_channels)

	def filter_data(self, data: np.ndarray):
		""""""
		# Only filter active channels.
		for i, channel in enumerate(self.active_channels):
			pass
			# Constant detrend, i.e. center data at y = 0
			#DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
			# Notch filter, remove 50Hz AC interference.
			#DataFilter.remove_environmental_noise(data[channel], self.sampling_rate, NoiseTypes.FIFTY)
			# Bandpass filter
			#DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
			#				FilterTypes.BUTTERWORTH.value, 0)
			#DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
			#                            FilterTypes.BUTTERWORTH.value, 0)
			#DataFilter.perform_bandstop(data[channel], self.sampling_rate, 50.0, 4.0, 2,
			#                            FilterTypes.BUTTERWORTH.value, 0)
			#DataFilter.perform_bandstop(data[channel], self.sampling_rate, 60.0, 4.0, 2,
			#                            FilterTypes.BUTTERWORTH.value, 0)

class Action:
	def __init__(self) -> None:
		self.p1_actions = ['LEFT', 'RIGHT']
		self.p2_actions = ['FORWARD', 'BACKWARD']

	def perform_actions(self, quantities: list[dict[str, Any]]):
		p1_action = self._decide(quantities[0]) # TODO: Get threshold from settings.
		p2_action = self._decide(quantities[1]) # TODO: Get threshold from settings.

		self._act_player1(p1_action)
		self._act_player2(p1_action)
		
		actions = [self.p1_actions[p1_action], self.p2_actions[p2_action]]
		return actions

	def _decide(self, quantity: dict[str, Any], threshold: int=0.5):
		_, focus = quantity['focus_metric']
		metric = focus[-1] # TODO: Implement smarter selection than this.
		if metric < threshold:
			return 0
		else:
			return 1

	def _act_player1(self, action: int):
		"""Wrapper to call external motor control."""
		if action:
			pass # Higher than threshold. # TODO: implement this
		else:
			pass # Lower than threshold.  # TODO: implement this

	def _act_player2(self, action):
		"""Wrapper to call external motor control."""
		if action:
			pass # Higher than threshold. # TODO: implement this
		else:
			pass # Lower than threshold.  # TODO: implement this

class GameLogic(Board):
	def __init__(self, board_shim: BoardShim, active_channels: list[int]):
		super().__init__(board_shim, active_channels)
		self.p1 = Player(board_shim, active_channels, active_channels[0])
		self.p2 = Player(board_shim, active_channels, active_channels[1])
		self.filter = FilterData(board_shim, active_channels)
		self.act = Action()

	def update(self):
		# Collect data from BCI board.
		data = self.board_shim.get_current_board_data(self.num_points)

		# Filter the raw data, denoise the signal.
		self.filter.filter_data(data)

		# Send data to players, calculate all derived quantities
		q1 = self.p1.update(data)
		q2 = self.p2.update(data)
		quantities = (q1, q2)

		# Decide and send actions to arduino.
		actions = self.act.perform_actions(quantities)

		# Send derived quantities to GUI for plotting.
		return quantities, actions

	def destroy(self):
		MLClassifier().destroy_model()

class BrainGameInterface:
	def __init__(self, return_data):
		self.return_data = return_data
		# Set logging level.
		BoardShim.enable_dev_board_logger()
		logging.basicConfig(level=logging.DEBUG)
		# Parse program arguments
		args = parse_arguments()
		# Set appropriate BoardShim parameters.
		params = set_brainflow_input_params(args)
		# Set active channels.
		active_channels = set_active_channels(args)
		# Save settings.
		self.params = params
		self.active_channels = active_channels
		self.board_id = args.board_id
		self.streamer_params = args.streamer_params
		# Variables to keep temporary settings in settings dialogue.
		self.board_id_tmp = self.board_id
		self.active_channels_tmp = self.active_channels
		self.serial_port_tmp = self.params.serial_port
		# Preallocation for BoardShim, GameLogic and game flag.
		self.board_shim = None
		self.game = None
		self.game_is_running = False	

	def callback_apply_settings(self):
		"""Apply current settings to the board."""
		# If BoardShim has been initialized before:
		if self.board_shim is not None:
			# Break early if there's no new settings to apply.
			if not self.__has_settings_changed():
				logging.info("No new settings to apply")
				return
			# Stop the session if board is already running.
			if self.board_shim.is_prepared():
				logging.info('Releasing board shim')
				self.board_shim.release_session()
			# Apply new settings.
			self.board_id = self.board_id_tmp
			self.active_channels = self.active_channels_tmp
			self.params.serial_port = self.serial_port_tmp
		
		try:
			# Initialize BoardShim and prepare session.
			board_shim = BoardShim(self.board_id, self.params)
			board_shim.prepare_session()
			logging.info('Board shim prepared')

			# Activate differential mode.
			if board_shim.board_id == BoardIds.CYTON_BOARD:
				set_differential_mode(board_shim, self.active_channels)
				logging.info("Differential mode set")

			# Save BoardShim
			self.board_shim = board_shim
			self.new_settings = True
			logging.info("Board shim initialized")

		except BaseException:
			# Error handling.
			logging.warning('Exception', exc_info=True)

	def callback_discard_settings(self):
		"""Discard current settings."""
		self.board_id_tmp = self.board_id
		self.active_channels_tmp = self.active_channels
		self.serial_port_tmp = self.params.serial_port
		logging.info("Settings discarded")

	def __has_settings_changed(self):
		"""Return true if current settings are different to old settings."""
		if (self.board_id == self.board_id_tmp
		    and self.active_channels == self.active_channels_tmp
		    and self.params.serial_port == self.serial_port_tmp):
			return False
		else:
			return True

	def callback_set_serial_port(self, serial_port: str):
		self.serial_port_tmp = serial_port
		logging.info("Serial port set")

	def callback_set_board_id(self, board_id: int):
		self.board_id_tmp = board_id
		logging.info("Board ID set")

	def callback_set_active_channels(self, active_channels: list[int]):
		self.active_channels_tmp = active_channels
		logging.info("Active channels set")

	def callback_start_game(self):
		"""Start the main game."""
		if self.game_is_running:
			print("Game is already started")
			return
		# Verify that a session is prepared.
		if self.board_shim is None or not self.board_shim.is_prepared():
			logging.info("Applying settings")
			self.callback_apply_settings()
			
		try: 
			# Start streaming session.
			self.board_shim.start_stream(450000, self.streamer_params)
			
			# Add delay for synthetic board, too fast otherwise.
			if self.board_shim.board_id == BoardIds.SYNTHETIC_BOARD:
				time.sleep(0.5)

			# On init setup or when settings are new, create the game logic.
			if self.game is None or self.new_settings:
				self.game = GameLogic(self.board_shim, self.active_channels)
				self.new_settings = False
				logging.info("Game logic created")
			
			# Start threading
			self.game_is_running = True
			self.game_thread = threading.Thread(target=self.__game_update_loop, daemon=False)
			self.game_thread.start()
			logging.info("Game started")

		except BaseException: 
			# Error handling.
			logging.warning('Exception', exc_info=True)

	def __game_update_loop(self):
		"""Main thread function for game logic loop."""

		self.init_fps()
		while self.game_is_running:
			# Update game logic one step, collect game info.
			quantities, actions = self.game.update()
			# Send game info to GUI for plotting.
			self.return_data.put([quantities, actions])
			#print(f"{np.random.random()}", end="\r")
			self.calc_fps()
			#print(f"FPS: {self.fps:.3f}", end='\r')


	def init_fps(self):
		self.fps = -1
		self.lastTime = time.time()
	
	def calc_fps(self):
		"""Calculate frames per second."""
		now = time.time()
		dt = now - self.lastTime
		self.lastTime = now
		if self.fps == -1:
			self.fps = 1.0/dt
		else: 
			s = np.clip(dt*3., 0, 1)
			self.fps = self.fps * (1-s) + (1.0/dt) * s



	def callback_stop_game(self):
		"""Stop the main game."""
		# Halt any running game session.
		if self.game_is_running:
			# Stop game loop.
			self.game_is_running = False
			# Join Thread.
			self.game_thread.join()
			logging.info("Game stopped")

			# Clean up game logic
			self.game.destroy()
			self.game = None
			logging.info("Game logic destroyed")
		else:
			logging.info("No game is running")


		## Halt any running game session.
		#if self.game_is_running:
		#	# Stop game loop.
		#	self.game_is_running = False
		#	# Join Thread.
		#	self.thread.join()
		#	logging.info("Game stopped")
	
		# Clean up game logic
		#if self.game is not None:
		#	self.game.destroy()
		#	self.game = None
		#	logging.info("Game logic destroyed")

		# Clean up board shim.
		if self.board_shim is not None and self.board_shim.is_prepared():
			self.board_shim.release_session()
			self.board_shim = None
			logging.info('Board shim released')
		
