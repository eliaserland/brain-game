import time
import logging
import threading
import numpy as np

import dearpygui.dearpygui as dpg
from brainflow.board_shim import BoardIds

import braingame
from datacontainer import DataContainer
from definitions import item_id
from util import FPS, serial_ports
from dpg_util import *
import fonts

toggle_state = False

class GUI:
	def __init__(self) -> None:
		# Create an instance of the main game.
		self.game = braingame.BrainGameInterface()
		self.game_is_running = False

	def create_all_windows(self):
		# Init windows
		self.create_welcome_window()
		self.create_main_window()

		# Global callbacks
		dpg.set_frame_callback(frame=1, callback=self.startup_settings) # Runs on first frame.
		dpg.set_viewport_resize_callback(callback=self.window_resize) # On window resize.
		dpg.set_exit_callback(callback=self.callback_stop_game) # On main window exit.

		# Fullscreen toggle on F11 and mouse double click, fullscreen exit on escape-key.
		with dpg.handler_registry():
			dpg.add_key_press_handler(key=dpg.mvKey_Escape, callback=exit_viewport_fullscreen)
			dpg.add_key_press_handler(key=dpg.mvKey_F11, callback=toggle_viewport_fullscreen)
			dpg.add_mouse_double_click_handler(callback=toggle_viewport_fullscreen)

		# Set welcome screen as primary window
		dpg.set_primary_window(item_id['windows']['welcome_window'], True)


	def create_welcome_window(self):
		"""Create the initial welcome screen."""
		with dpg.window(tag=item_id['windows']['welcome_window'], show=True, no_background=True):
			# Create text items.
			dpg.add_text("BrainGame Curiosum", tag=item_id['text']['title'])
			dpg.add_text("This is a tagline", tag=item_id['text']['tagline'])
			dpg.add_text("PRESS ENTER TO START", tag=item_id['text']['enter_key'])
			dpg.add_text("Copyright by Name1, Name2, Name3, Name4, Name5 & Name6", tag=item_id['text']['copyright'])
		# Set fonts.
		dpg.bind_item_font(item_id['text']['title'], fonts.huge_font)
		dpg.bind_item_font(item_id['text']['tagline'], fonts.large_font)
		dpg.bind_item_font(item_id['text']['enter_key'], fonts.large_font)
		dpg.bind_item_font(item_id['text']['copyright'], fonts.default_font)

		# Enter-key to enter the game.
		with dpg.handler_registry(tag=item_id['registry']['enter_key']):
			dpg.add_key_press_handler(key=dpg.mvKey_Return, callback=self.callback_press_enter_key)

		# Make "Press enter to start game" clickable to enter game.
		with dpg.item_handler_registry(tag=item_id['handlers']['enter_key']):
			dpg.add_item_clicked_handler(callback=self.callback_press_enter_key)
		dpg.bind_item_handler_registry(item_id['text']['enter_key'], item_id['handlers']['enter_key'])


	def callback_press_enter_key(self):
		"""Enter the game from the welcome screen."""
		dpg.configure_item(item_id['windows']['welcome_window'], show=False)
		dpg.set_primary_window(item_id['windows']['main_window'], True)
		dpg.configure_item(item_id['windows']['main_window'], show=True)
		dpg.configure_item(item_id['registry']['enter_key'], show=False)
		dpg.configure_item(item_id['registry']['game_key_binds'], show=True)
		
	
	def callback_exit_game(self):
		"""Return to the welcome screen from within the game."""
		# TODO: Need to safely exit the game.

		dpg.configure_item(item_id['registry']['game_key_binds'], show=False)
		dpg.configure_item(item_id['windows']['main_window'], show=False)
		dpg.set_primary_window(item_id['windows']['welcome_window'], True)
		dpg.configure_item(item_id['windows']['welcome_window'], show=True)
		dpg.configure_item(item_id['registry']['enter_key'], show=True)

	def create_settings_menu(self):
		"""Create the settings menu."""
		def callback_boardid_combo():
			# Retrieve and parse board ID string, and send to boardshim.
			board_name = dpg.get_value(item_id['combos']['board_id'])
			board_id = BoardIds.__getitem__(board_name).value
			self.game.callback_set_board_id(board_id)
		def callback_ok():
			# Let boardshim apply settings and show main window.
			self.game.callback_apply_settings()
			dpg.configure_item(item_id['windows']['settings_window'], show=False)
		def callback_reset():
			# Let boardshim discard any new settings and reset window items.
			dpg.set_value(item_id['combos']['board_id'], value=BoardIds._member_names_[2])
			self.game.callback_discard_settings()
		def callback_cancel():
			# Let boardshim discard any new settings and show main window.
			callback_reset()
			dpg.configure_item(item_id['windows']['settings_window'], show=False)

		# Settings window.
		with dpg.popup(item_id['buttons']['settings'], mousebutton=dpg.mvMouseButton_Left, modal=True, tag=item_id['windows']['settings_window']):
			
			# Board ID selector:
			all_boards = BoardIds._member_names_
			combo1 = dpg.add_combo(all_boards, label="Board ID", default_value=all_boards[2], tag=item_id['combos']['board_id'], callback=callback_boardid_combo)

			# Bottom row of buttons: OK, Reset & Cancel.
			dpg.add_spacer(height=10)
			with dpg.group(horizontal=True):
				btn_width = 100 
				dpg.add_button(label="OK", callback=callback_ok, width=btn_width, tag=item_id['buttons']['ok'])
				dpg.add_button(label="Reset", callback=callback_reset, width=btn_width, tag=item_id['buttons']['reset'])
				dpg.add_button(label="Cancel", callback=callback_cancel, width=btn_width, tag=item_id['buttons']['cancel'])



	def create_main_window(self):
		"""Create the main window. """

		def toggle_start_stop_game():
			global toggle_state
			toggle_state = not toggle_state
			if toggle_state:
				self.callback_start_game()
			else:
				self.callback_stop_game()

		# Game start/stop toggle on enter-key and spacebar.
		with dpg.handler_registry(tag=item_id['registry']['game_key_binds'], show=False):
			dpg.add_key_press_handler(key=dpg.mvKey_Return, callback=toggle_start_stop_game)
			dpg.add_key_press_handler(key=dpg.mvKey_Spacebar, callback=toggle_start_stop_game)
		
		with dpg.window(tag=item_id['windows']['main_window'], show=False):
			with dpg.group(horizontal=True):
				# Left column:
				with dpg.child_window(width=116):
					# Main game buttons
					btn_width = 100 
					dpg.add_button(label="Start", width=btn_width, tag=item_id['buttons']['start'], callback=self.callback_start_game,)
					dpg.add_button(label="Stop", width=btn_width, tag=item_id['buttons']['stop'], callback=self.callback_stop_game)
					dpg.add_button(label="Settings", width=btn_width, tag=item_id['buttons']['settings'])
					dpg.add_button(label="Exit", width=btn_width, tag=item_id['buttons']['exit'], callback=self.callback_exit_game)
					# Settings menutitle_width
					self.create_settings_menu()
				
				# Right plotting window: 
				with dpg.child_window(autosize_x=True):
					# Create all graphs:
					self.create_all_graphs()

	def create_all_graphs(self):
		y_min = -100
		y_max = 100
		width = 550
		height = 375

		with dpg.group(horizontal=True):
			with dpg.plot(label='Player 1 - Time Series', width=width, height=height, anti_aliased=True, tag=item_id['plots']['timeseries1']):
				# optionally create legend
				dpg.add_plot_legend()

				# REQUIRED: create x and y axes
				dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=item_id['axes']['timeseries1_xaxis'])
				dpg.add_plot_axis(dpg.mvYAxis, label="Voltage (uV)", tag=item_id['axes']['timeseries1_yaxis'])

				# series belong to a y axis
				dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=item_id['axes']['timeseries1_yaxis'], tag=item_id['line_series']['timeseries1'])
				dpg.set_axis_limits(item_id['axes']['timeseries1_yaxis'], y_min, y_max)
				dpg.set_axis_limits(item_id['axes']['timeseries1_xaxis'], -5, 0)

			with dpg.plot(label='Player 2 - Time Series', width=width, height=height, anti_aliased=True, tag=item_id['plots']['timeseries2']):
				# optionally create legend
				dpg.add_plot_legend()

				# REQUIRED: create x and y axes
				dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=item_id['axes']['timeseries2_xaxis'])
				dpg.add_plot_axis(dpg.mvYAxis, label="Voltage (uV)", tag=item_id['axes']['timeseries2_yaxis'])

				# series belong to a y axis
				dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=item_id['axes']['timeseries2_yaxis'], tag=item_id['line_series']['timeseries2'])
				dpg.set_axis_limits(item_id['axes']['timeseries2_yaxis'], y_min, y_max)
				dpg.set_axis_limits(item_id['axes']['timeseries2_xaxis'], -5, 0)
		with dpg.group(horizontal=True):
			with dpg.plot(label='Player 1 - Foucs Metric', width=width, height=height, anti_aliased=True, tag=item_id['plots']['metric1']):
				# optionally create legend
				dpg.add_plot_legend()

				# REQUIRED: create x and y axes
				dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=item_id['axes']['metric1_xaxis'])
				dpg.add_plot_axis(dpg.mvYAxis, label="Metric", tag=item_id['axes']['metric1_yaxis'])

				# series belong to a y axis
				dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=item_id['axes']['metric1_yaxis'], tag=item_id['line_series']['metric1'])
				dpg.set_axis_limits(item_id['axes']['metric1_yaxis'], -0.005, 1.005)
				dpg.set_axis_limits(item_id['axes']['metric1_xaxis'], -5, 0)
			
			with dpg.plot(label='Player 2 - Focus Metric', width=width, height=height, anti_aliased=True, tag=item_id['plots']['metric2']):
				# optionally create legend
				dpg.add_plot_legend()

				# REQUIRED: create x and y axes
				dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=item_id['axes']['metric2_xaxis'])
				dpg.add_plot_axis(dpg.mvYAxis, label="Metric", tag=item_id['axes']['metric2_yaxis'])

				# series belong to a y axis
				series4 = dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=item_id['axes']['metric2_yaxis'], tag=item_id['line_series']['metric2'])
				dpg.set_axis_limits(item_id['axes']['metric2_yaxis'], -0.005, 1.005)
				dpg.set_axis_limits(item_id['axes']['metric2_xaxis'], -5, 0)

	
	def window_resize(self):
		"""Callback on window resize."""
		xpos = [0, 0, 1, 1]
		ypos = [0, 1, 0, 1]
		#btn_height = dpg.get_item_height(btn1)
		#h = dpg.get_item_height("Time Series") - btn_height - 45
		h = dpg.get_viewport_client_height() - 45
		#w = dpg.get_item_width("Time Series") - 40
		w = dpg.get_viewport_client_width() - 40
		for i, p in enumerate(item_id['plots'].values()):
			dpg.set_item_height(p, height=h//2)
			dpg.set_item_width(p, width=w//2)
			dpg.set_item_pos(p, [(w//2)*xpos[i], (h//2)*ypos[i],])
		
		self.center_settings_window()
		self.resize_welcome_window()

	def center_settings_window(self):
		"""Center the settings window in the viewport."""
		h = dpg.get_viewport_client_height()
		w = dpg.get_viewport_client_width()	
		settings_height = dpg.get_item_height(item_id['windows']['settings_window'])
		settings_width = dpg.get_item_width(item_id['windows']['settings_window'])
		xpos = w//2 - settings_width//2
		ypos = h//2 - settings_height//2
		#print(h, w, settings_height, settings_width, xpos, ypos)
		dpg.configure_item(item_id['windows']['settings_window'], pos=(xpos, ypos))

	def resize_welcome_window(self):
		h = dpg.get_viewport_client_height()
		w = dpg.get_viewport_client_width()

		# Title
		title_width = dpg.get_item_width(item_id['text']['title'])
		title_xpos = w//2 - 325
		title_ypos = int(0.15*h)
		dpg.set_item_pos(item_id['text']['title'], (title_xpos, title_ypos))

		# Tagline
		tagline_xpos = w//2 - 120
		tagline_ypos = title_ypos + 90
		dpg.set_item_pos(item_id['text']['tagline'], (tagline_xpos, tagline_ypos))

		# Press enter to start
		enter_xpos = w//2 - 190
		enter_ypos = int(np.maximum(tagline_ypos + 100, 0.6*h)) 
		dpg.set_item_pos(item_id['text']['enter_key'], (enter_xpos, enter_ypos))

		# Copyright
		copy_xpos = w//2 - 235
		copy_ypos = h - 50 #int(np.maximum(tagline_ypos + 100, 0.6*h)) 
		dpg.set_item_pos(item_id['text']['copyright'], (copy_xpos, copy_ypos))


	def startup_settings(self):
		"""This function is executed on render of the very first frame."""
		# Make settings window show on startup.
		dpg.configure_item(item_id['windows']['settings_window'], show=False, no_close=True, label="Settings", no_move=True)
		time.sleep(0.01)
		self.center_settings_window()
	
	#----------------------------------------------------------------------

	def callback_start_game(self):
		"""Callback to start a new game."""
		if not self.game_is_running:
			try:
				logging.info("Starting game")
				# Set flag.
				self.game_is_running = True
				# Create a container used for housing return data from game loop.
				self.data = DataContainer()
				# Start the main game loop.
				self.game.start_game(self.data)
				# Set flag & start gui plotting thread
				self.game_is_running = True
				self.thread = threading.Thread(target=self.__gui_loop, daemon=False)
				self.thread.start()
			except BaseException:
				logging.warning('Exception', exc_info=True)
		else:
			logging.info("Game is already running")

	def callback_stop_game(self):
		"""Callback to stop and end a running game."""
		if self.game_is_running:
			logging.info("Stopping game")
			self.game_is_running = False
			self.game.stop_game()
			self.data.destroy()
			self.thread.join()
		else:
			logging.info("No game is running")

	def callback_restart_game(self):
		pass

	def callback_settings_menu(self):
		pass

	def callback_timeseries_settings(self):
		pass

	def callback_focus_settings(self):
		pass

	def callback_language_setting(self):
		pass

	def __gui_loop(self):
		"""Main thread function for updating the GUI plots during a game."""
		fps_timer = FPS()
		while self.game_is_running:
			# Get data from game logic, update graphs.
			return_data = self.data.get()
			self.__update_plots(return_data)
			# Print fps counter
			fps = fps_timer.calc()
			print(f"FPS: {fps:.3f}", end='\r')
	
	def __update_plots(self, data):
			(player1, player2), actions = data
			time1, timeseries1 = player1['time_series']
			time2, timeseries2 = player2['time_series']
			metric_time1, metric1 = player1['focus_metric']
			metric_time2, metric2 = player2['focus_metric']

			#print("Actions: " + ' '.join(actions) + f"  {metric1[-1]:.5f} {metric2[-1]:.5f}", end='\r')
			dpg.set_value(item_id['line_series']['timeseries1'], [list(time1), list(timeseries1)])
			dpg.set_value(item_id['line_series']['timeseries2'], [list(time2), list(timeseries2)])
			dpg.set_value(item_id['line_series']['metric1'], [list(metric_time1), list(metric1)])
			dpg.set_value(item_id['line_series']['metric2'], [list(metric_time2), list(metric2)])





