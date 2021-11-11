import argparse
import time
import logging
import numpy as np
from collections import deque

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowFunctions, DetrendOperations
from brainflow.ml_model import BrainFlowMetrics, BrainFlowClassifiers, BrainFlowModelParams, MLModel

import dearpygui.dearpygui as dpg
from math import sin, cos

from braingame import *

programName = 'BrainGame Curiosum'

def gui_options():
	dpg.show_documentation()
	#dpg.show_style_editor()
	#dpg.show_debug()
	#dpg.show_about()
	dpg.show_metrics()
	#dpg.show_font_manager()
	#dpg.show_item_registry()

def create_gui():
	# Lines to change		
	with dpg.window(tag="Primary Window"):
		dpg.add_text("Hello, world")
		dpg.add_button(label="Save")
		dpg.add_input_text(label="string", default_value="Quick brown fox")
		dpg.add_slider_float(label="float", default_value=0.273, max_value=1)
	
	def button_callback(sender, app_data, user_data):
		print(f"sender is: {sender}")
		print(f"app_data is: {app_data}")
		print(f"user_data is: {user_data}")

	with dpg.window(label="Tutorial"):
		# user data and callback set when button is created
		dpg.add_button(label="Apply", callback=button_callback, user_data="Some Data")

		# user data and callback set any time after button has been created
		btn = dpg.add_button(label="Apply 2", )
		dpg.set_item_callback(btn, button_callback)
		dpg.set_item_user_data(btn, "Some Extra User Data")

	sindatax = []
	sindatay = []
	for i in range(0, 1500):
		sindatax.append(i / 1000)
		sindatay.append(0.5 + 0.5 * sin(50 * i / 1000) * np.random.random())

	def update_series():
		cosdatax = []
		cosdatay = []
		for i in range(0, 1500):
			cosdatax.append(i / 1000)
			cosdatay.append(0.5 + 0.5 * cos(50 * i / 1000)*np.random.random())
		dpg.set_value('series_tag', [cosdatax, cosdatay])
		dpg.set_item_label('series_tag', "0.5 + 0.5 * cos(x)")

	with dpg.window(label="Tutorial", tag="win"):
		dpg.add_button(label="Update Series", callback=update_series)
		# create plot
		with dpg.plot(label="Line Series", height=800, width=1200, anti_aliased=True):
			# optionally create legend
			dpg.add_plot_legend()

			# REQUIRED: create x and y axes
			dpg.add_plot_axis(dpg.mvXAxis, label="x")
			dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")

			# series belong to a y axis
			dpg.add_line_series(sindatax, sindatay, label="0.5 + 0.5 * sin(x)", parent="y_axis", tag="series_tag")


def main():

	# ------------------
	# RUN FIRST THING AT PROGRAM START
	# Parse program arguments and set the appropriate BrainFlow parameters.
	args = parse_arguments()
	params = set_brainflow_input_params(args)
	
	# Determine the active channels.
	active_channels = set_active_channels(args)

	board_id = args.board_id
	streamer_params = args.streamer_params
	# ------------------

	# SHOW STARTUP SPLASH SCREEN (Press any key to start), overlayed by settings dialog.

	# Apply settings to close dialog.

	# When any key is pressed, show main game window.

	game = None
	try:
		# ------------------
		# APPLY SETTINGS
		# Initialize board and prepare session.
		board_shim = BoardShim(args.board_id, params)
		board_shim.prepare_session()

		# Activate differential mode.
		if board_shim.board_id == BoardIds.CYTON_BOARD:
			set_differential_mode(board_shim, active_channels)
		

		# ------------------
		# START GAME
		# Start streaming session.
		board_shim.start_stream(450000, args.streamer_params)
		if board_shim.board_id == BoardIds.SYNTHETIC_BOARD:
			time.sleep(0.1)
		# ------------------

		# Set up game data structures.
		game = GameLogic(board_shim, active_channels)

		# ------------------
		# Prepare GUI (these lines are always needed)
		dpg.create_context()
		dpg.create_viewport(title=programName, width=1000, height=800)

		create_gui()
		gui_options()

		# Run GUI (these lines are always needed)
		dpg.setup_dearpygui()
		dpg.show_viewport()

		dpg.set_primary_window("Primary Window", True)
		# ------------------

		# Main render loop: code here is executed every frame.
		while dpg.is_dearpygui_running():
			game.update()
			dpg.render_dearpygui_frame()
		
	except BaseException as e:
		# Error handling.
		logging.warning('Exception', exc_info=True)
	finally:
		# Clean up GUI and game logic.
		dpg.destroy_context() # TODO: if clause for if game exists
		if game is not None:
			game.destroy() # TODO: if clause for if game exists

		# ------------------
		# End streaming session.
		logging.info('End')
		if board_shim.is_prepared():
			logging.info('Releasing session')
			board_shim.release_session()
		# ------------------

if __name__ == '__main__':
	main()