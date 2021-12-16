import argparse
import queue
import time
import logging
from typing import Any
import numpy as np
from collections import deque
import threading
import multiprocessing

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowFunctions, DetrendOperations
from brainflow.ml_model import BrainFlowMetrics, BrainFlowClassifiers, BrainFlowModelParams, MLModel

WINDOW_SIZE = 5 # Seconds

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
	"""Base class containing BoardShim details and settings."""
	def __init__(self, board_shim: BoardShim, active_channels: list[int]):
		# Save board parameters.
		self.board_shim = board_shim
		self.board_id = board_shim.get_board_id()
		self.eeg_channels = BoardShim.get_eeg_channels(self.board_id)
		self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
		self.window_size = WINDOW_SIZE
		self.num_points = self.window_size * self.sampling_rate
		self.num_channels = self.board_shim.get_num_rows(self.board_id)
		self.timestamp_channel = BoardShim.get_timestamp_channel(self.board_id)
		self.active_channels = active_channels
		# Limit no. of channels if testing with synthetic data
		if self.board_id == BoardIds.SYNTHETIC_BOARD:
			self.eeg_channels = [1, 2, 3, 4, 5, 6, 7, 8]

class AvgBandPower(Board):
	"""Class for calculating average band power from time series data."""
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
	"""Simpleton class containing the BrainFlow metric classifier."""
	model = None
	model_params = None

	@classmethod
	def configure(cls, metric: BrainFlowMetrics=BrainFlowMetrics.RELAXATION, 
	             classifier: BrainFlowClassifiers=BrainFlowClassifiers.REGRESSION):
		"""Create and configure the classifier."""
		if cls.model is not None:
			cls.destroy_model()
		cls.model_params = BrainFlowModelParams(metric, classifier)
		cls.model = MLModel(cls.model_params)
		cls.model.enable_ml_logger()
		cls.model.prepare()
		return cls
	
	@classmethod
	def destroy_model(cls):
		"""Safely destroy the classifer."""
		cls.model.release()
		cls.model = None
		cls.model_params = None

class FocusMetric(Board):
	"""Class for calculating the BrainFlow focus metric from time series data."""
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int, previous_metric: list, previous_time: list):
		super().__init__(board_shim, active_channels)
		if previous_metric is None:
			self.metric = deque([0], maxlen=self.num_points) 
			self.time = deque([time.time()], maxlen=self.num_points)
		else:
			self.metric = deque([], maxlen=self.num_points)
			for m in previous_metric:
				self.metric.append(m)
			self.time = deque([], maxlen=self.num_points)
			now = time.time()
			for t in previous_time:
				self.time.append(t+now)

		classifier = MLClassifier.configure() # TODO: GET INPUT FROM SETTINGS DIALOGUE
		self.model = classifier.model
		self.model_params = classifier.model_params
		self.channel = channel

	def get_metric(self, data: np.ndarray):
		"""From time series data, get current focus metric estimate."""
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
	"""Class for extracting the time series data for a specific player."""
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int):
		super().__init__(board_shim, active_channels)
		self.channel = channel # The channel associated with the player.
		self.time = list(reversed(-np.arange(0, self.num_points)/self.sampling_rate))
		self.timeseries = np.zeros(self.num_points)

	def get_time_series(self, data: np.ndarray):
		"""Get the timeseries for the given player"""
		timeseries = data[self.channel]
		#self.timeseries[(self.num_points-len(timeseries)):] = timeseries
		return  self.time, list(timeseries)

class Player:
	"""Class collecting all player specific logic."""
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int, old_playerinfo):
		if old_playerinfo is None:
			previous_time, previous_metric = (None, None)
		else:
			previous_time, previous_metric = old_playerinfo['focus_metric']
		self.timeseries = TimeSeries(board_shim, active_channels, channel)
		self.bandp = AvgBandPower(board_shim, active_channels, channel)
		self.focus = FocusMetric(board_shim, active_channels, channel, previous_metric, previous_time)

	def update(self, data: np.ndarray):
		"""Update derived quantities for the current timestep."""
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
	"""Class responsible for filtering of the raw time series data."""
	def __init__(self, board_shim: BoardShim, active_channels: list[int]):
		super().__init__(board_shim, active_channels)

	def filter_data(self, data: np.ndarray):
		"""Apply filtering to the current timestep."""
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

	def get_actions(self, quantities: list[dict[str, Any]]):
		p1_action = self._decide(quantities[0]) # TODO: Get threshold from settings.
		p2_action = self._decide(quantities[1]) # TODO: Get threshold from settings.

		#self._act_player1(p1_action)
		#self._act_player2(p1_action)
		
		actions = [self.p1_actions[p1_action], self.p2_actions[p2_action]]
		return actions

	def _decide(self, quantity: dict[str, Any], threshold: int=0.5):
		_, metric_series = quantity['focus_metric']
		metric_val = metric_series[-1] # TODO: Implement smarter selection than this.
		if metric_val < threshold:
			return 0
		else:
			return 1

	#def _act_player1(self, action: int):
	#	"""Wrapper to call external motor control."""
	#	if action:
	#		pass # Higher than threshold. # TODO: implement this
	#	else:
	#		pass # Lower than threshold.  # TODO: implement this

	#def _act_player2(self, action):
	#	"""Wrapper to call external motor control."""
	#	if action:
	#		pass # Higher than threshold. # TODO: implement this
	#	else:
	#		pass # Lower than threshold.  # TODO: implement this


#class MotorLogic:
#	def __init__(self) -> None:
#		pass
#		# lab = LabyrintStyrning()
#
#	def vote(self, quantities: list[dict[str, Any]]):
#		pass
#
#	def start_motor_control(self):
#		self.motors_are_running = True
#		self.motor_thread = threading.Thread(target=self.__motor_update_loop, daemon=False)
#		self.motor_thread.start()
#
#	def stop_motor_control(self):
#		self.motors_are_running = False
#		self.motor_thread.join()
	
#	def __motor_update_loop(self):
#		"""Thread function for motor control logic."""
#		while self.motors_are_running:
			# Wait for queue to be not empty

			# Take item from queue.

			# Send command to motors.
#			pass

def motor_logic(queue: multiprocessing.Queue) -> None:
	"""Main function to handle interface with servos."""
	# lab = LabyrintStyrning()
	while True:
		# Pick item from the queue.
		action = queue.get()
		# Handle certain special cases.
		if action == "end": # to be called at program exit
			break
		if action == "reset": # to be called at braingame.stop_game
			# TODO: Return to starting configuration.
			continue
		# Act according to action.
		#lab.turn_right(1)
		#lab.turn_left(1)
		print(action)
	
	# Safely shut down program.
	#lab.__del__()

"""
def motor_loop(queue: multiprocessing.Queue):
	#lab = LabyrintStyrning()
	while True:
		action = queue.get()
		if action == "stop":
			queue.task_done()
			break
		# Act according to action
		#lab.turn_right(1)
		#lab.turn_left(1)
		queue.task_done()
"""

class GameLogic(Board):
	"""Class containing and collecting the main game logic."""
	def __init__(self, board_shim: BoardShim, active_channels: list[int], init_data: np.ndarray, old_quantities=None):
		super().__init__(board_shim, active_channels)
		if old_quantities is None:
			(q1, q2) = None, None
		else:
			(q1, q2) = old_quantities
		self.p1 = Player(board_shim, active_channels, active_channels[0], q1)
		self.p2 = Player(board_shim, active_channels, active_channels[1], q2)
		self.filter = FilterData(board_shim, active_channels)
		self.act = Action()
		if init_data is not None:
			self.init_data = init_data
		else: 
			self.init_data = np.zeros((self.num_channels, self.num_points))
	
	def update(self):
		"""Update game logic. Equivalent to advancing game one step forwards in time."""
		# Collect data from BCI board.
		data = self.board_shim.get_current_board_data(self.num_points)

		# Merge into init/old data array.
		self.data = self.__merge_data(data)

		# Filter the raw data, denoise the signal.
		self.filter.filter_data(self.data)

		# Send data to players, calculate all derived quantities
		q1 = self.p1.update(self.data)
		q2 = self.p2.update(self.data)
		quantities = (q1, q2)

		# Decide and send actions to arduino.
		actions = self.act.get_actions(quantities)

		# Send derived quantities to GUI for plotting.
		return quantities, actions, self.data

	def __merge_data(self, data_in: np.ndarray):
		"""
		If data array is smaller than maximum allowed size, merge the new 
		data into the array of initial/old data.
		"""
		if data_in.shape[1] < self.num_points:
			data_out = np.zeros_like(self.init_data)
			data_out[:, :(self.num_points- data_in.shape[1])] = self.init_data[:, data_in.shape[1]:]
			data_out[:, (self.num_points- data_in.shape[1]):] = data_in
		else:
			data_out = data_in
		return data_out

	def destroy(self):
		"""Safely destroy the main game logic."""
		MLClassifier().destroy_model()


class BrainGameInterface:
	"""Main outwards-facing class responsible for the 'game'-side of the BrainGame."""
	def __init__(self):
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
		self.gamelogic = None
		self.game_is_running = False
		self.previous_data = None

	def callback_apply_settings(self):
		"""Apply current settings to the board."""
		
		# Break early if there's no new settings to apply.
		if self.board_shim is not None and not self.__has_settings_changed():
			logging.info("Apply settings: No new settings to apply")
			return True
		# Stop the session.
		self.stop_game()
		# Apply new settings.
		self.board_id = self.board_id_tmp
		self.active_channels = self.active_channels_tmp
		self.params.serial_port = self.serial_port_tmp
		
		try:
			# Initialize BoardShim and prepare session.
			print(self.board_id, self.board_id_tmp)
			self.board_shim = BoardShim(self.board_id, self.params)
			self.board_shim.prepare_session()
			logging.info('Apply settings: Board shim prepared')

			# Activate differential mode.
			if self.board_shim.board_id == BoardIds.CYTON_BOARD:
				set_differential_mode(self.board_shim, self.active_channels)
				logging.info("Applying settings: Differential mode set")

			logging.info("Apply settings: Board shim initialized")
			
			# TODO: Initialize Arduino.
			
			self.queue = multiprocessing.Queue()
			self.motor_process = multiprocessing.Process(target=motor_logic, args=(self.queue,))
			self.motor_process.start()

			# TODO: CORRECT ERROR CHECKING AND HANDLING OF EXCEPTIONS
			
			return True

		except BaseException:
			# Error handling.
			logging.warning('Exception', exc_info=True)
			self.stop_game()
			return False

	def callback_discard_settings(self):
		"""Discard current settings."""
		self.board_id_tmp = self.board_id
		self.active_channels_tmp = self.active_channels
		self.serial_port_tmp = self.params.serial_port
		logging.info("Settings discarded")

	def __has_settings_changed(self):
		"""Return true if current settings are different from old settings."""
		if (self.board_id == self.board_id_tmp
		    and self.active_channels == self.active_channels_tmp
		    and self.params.serial_port == self.serial_port_tmp):
			return False
		else:
			return True

	def callback_set_serial_port(self, serial_port: str):
		self.serial_port_tmp = serial_port
		logging.info(f"Serial port set: serial_port={serial_port}")

	def callback_set_board_id(self, board_id: int):
		self.board_id_tmp = board_id
		logging.info(f"Board ID set: board_id={board_id}")
	
	def callback_set_active_channels(self, active_channels: list[int]):
		self.active_channels_tmp = active_channels
		logging.info(f"Active channels set: active_channels={active_channels}")

	def start_game(self, fresh_start=True):
		"""Start the main game."""
		if self.game_is_running:
			print("Start game: Game is already started")
			return
		# Verify that a session is prepared.
		if self.board_shim is None or not self.board_shim.is_prepared():
			logging.info("Start game: Need apply settings first")
			self.callback_apply_settings()
		try: 
			# Start streaming session.
			self.board_shim.start_stream(450000, self.streamer_params)
			
			# Create the game logic.
			if self.previous_data is None or fresh_start:
				init_data = None
				old_quantities = None
			else:
				init_data = self.previous_data
				old_quantities = self.previous_quantities
			self.gamelogic = GameLogic(self.board_shim, self.active_channels, init_data, old_quantities)
			logging.info("Start game: Game logic created")
		
			# Start threading
			self.game_is_running = True
			logging.info("Start game: Game started")

			#self.game_thread = threading.Thread(target=self.__game_update_loop, daemon=False)
			#self.game_thread.start()
			
			# TODO: Start motor control loop.
			#self.motor_control = Action()

		except BaseException: 
			# Error handling.
			logging.warning('Exception', exc_info=True)
			self.stop_game()
			raise Exception("Could not start game logic loop")
	
	def update_game(self):
		"""Update gamelogic one step."""
		# Update game logic one step, collect game info.
		quantities, actions, data = self.gamelogic.update()
		# Send actions to the motor logic
		self.queue.put(actions) # TODO: SEND ACTIONS
		# Save quantities to enable game restarts from old data.
		self.previous_data = data
		self.previous_quantities = quantities
		self.previous_actions = actions
		return quantities, actions, data 

	#def __game_update_loop(self):
	#	"""Main thread function for game logic loop."""
	#	while self.game_is_running:
	#		# Update game logic one step, collect game info.
	#		quantities, actions, data = self.gamelogic.update()
	#		# Send game info to GUI for plotting.
	#		self.return_data.put((quantities, actions))
	#	
	#	# At end, save last game state for next session.
	#	self.previous_data = data
	#	self.previous_quantities = quantities
	#	self.previous_actions = actions

	def stop_game(self):
		"""Stop the main game."""
		# Halt any running game session.
		if self.game_is_running:
			# Stop game loop.
			self.game_is_running = False
			# Join Thread.
			logging.info("Stop game: Game logic stopped")
			# Clean up game logic
			self.gamelogic.destroy()
			self.gamelogic = None
			logging.info("Stop game: Game logic destroyed")

			# TODO: Stop motor control loop.

		else:
			logging.info("Stop game: No game is running")
			
		# Clean up board shim.
		if self.board_shim is not None:
			if self.board_shim.is_prepared():
				self.board_shim.release_session()
				logging.info('Stop game: Board shim released')
			self.board_shim = None
			
	def quit_game(self):
		self.queue.put("end")
		self.queue.close()
		self.motor_process.join()
