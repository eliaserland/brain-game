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
		"""Creates and initializes all windows for the graphical user interface."""
		# Create an instance of the main game.
		self.game = braingame.BrainGameInterface()
		self.game_is_running = False
		self.settings_are_applied = False
		self.have_shown_help_dialogue = False
		
		# Create and initialize all GUI windows.
		self.__create_welcome_window()
		self.__create_main_window()
		self.__create_loading_screen()
		self.__create_settings_menu()
		self.__create_help_dialogue()

		# Set global callbacks.
		dpg.set_frame_callback(frame=1, callback=self.__startup_settings) # Executes on first frame.
		dpg.set_viewport_resize_callback(callback=self.window_resize) # Executes on window resize.
		dpg.set_exit_callback(callback=self.callback_stop_game) # Executes on program window exit.

		# Global key binds: Fullscreen mode: toggle on F11, toggle on mouse double click, exit on escape-key.
		with dpg.handler_registry():
			dpg.add_key_press_handler(key=dpg.mvKey_Escape, callback=exit_viewport_fullscreen)
			dpg.add_key_press_handler(key=dpg.mvKey_F11, callback=toggle_viewport_fullscreen)
			dpg.add_mouse_double_click_handler(callback=toggle_viewport_fullscreen)

		# Set welcome screen as primary window initially
		dpg.set_primary_window(item_id['windows']['welcome_window'], True)

	def __startup_settings(self):
		"""This function is executed on render of the very first frame."""
		self.window_resize()

	def __create_welcome_window(self):
		"""Create the initial welcome screen."""
		# Create the window.
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

		# Set key bind: Enter-key to enter the game. Default state: activated.
		with dpg.handler_registry(tag=item_id['registry']['enter_key']):
			dpg.add_key_press_handler(key=dpg.mvKey_Return, callback=self.callback_enter_game)

	def __create_main_window(self):
		"""Create the main window. """
		# Define helper function.
		def toggle_start_stop_game():
			"""Wrapper function for game start/stop toggle functionality."""
			global toggle_state
			toggle_state = not toggle_state
			if toggle_state:
				self.callback_start_game()
			else:
				self.callback_stop_game()

		# Key bind: Game start/stop toggle on enter-key and spacebar. Default state: deactivated.
		with dpg.handler_registry(tag=item_id['registry']['game_key_binds'], show=False):
			dpg.add_key_press_handler(key=dpg.mvKey_Return, callback=toggle_start_stop_game)
			dpg.add_key_press_handler(key=dpg.mvKey_Spacebar, callback=toggle_start_stop_game)

		# Create the window. Initially hidden.
		with dpg.window(tag=item_id['windows']['main_window'], show=False):
			with dpg.group(horizontal=True): # Horizontal grouping.
				# Left column: add game buttons and text items
				with dpg.child_window(width=116):
					# Main game buttons
					btn_width = 100 
					dpg.add_button(label="Start", width=btn_width, tag=item_id['buttons']['start'], callback=self.callback_start_game,)
					dpg.add_button(label="Stop", width=btn_width, tag=item_id['buttons']['stop'], callback=self.callback_stop_game)
					dpg.add_button(label="Help", width=btn_width, tag=item_id['buttons']['help_open'], callback=self.callback_show_help_dialogue)
					dpg.add_button(label="Settings", width=btn_width, tag=item_id['buttons']['settings'], callback=self.callback_show_settings_menu)
					dpg.add_button(label="Exit", width=btn_width, tag=item_id['buttons']['exit'], callback=self.callback_exit_game)
					
				# Right column: add plotting window with respective graphs.
				with dpg.child_window(autosize_x=True):
					# Create all graphs for plotting:
					self.__create_all_graphs()
	
	def __create_all_graphs(self):
		"""Create and initialize all plotting graphs of the main game window."""
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

	def __create_loading_screen(self):
		"""Create the loading screen."""
		# Create the window. Initially hidden.
		with dpg.window(tag=item_id['windows']['loading_screen'], height=100, width=450, show=False, no_resize=True, 
		                no_close=False, no_move=True, no_title_bar=True, modal=True):
			dpg.add_loading_indicator(tag=item_id['indicator']['settings_loading'], pos=(20, 19), style=0)
			dpg.add_text("Applying settings...", pos=(95, 35), tag=item_id['text']['loading'])

	def __create_help_dialogue(self):
		"""Create the help dialogue."""
		# Create the window. Initially hidden.
		with dpg.window(label="Help", tag=item_id['windows']['help_dialogue'], height=600, width=800, show=False, 
		                no_resize=True, no_move=True, modal=True, no_title_bar=False, on_close=self.callback_close_help_dialogue):
			dpg.add_text("This is a help text", pos=(95, 35), tag=item_id['text']['help'])
			dpg.add_button(label="Close", tag=item_id['buttons']['help_close'], callback=self.callback_close_help_dialogue)

	def __create_settings_menu(self):
		"""Create the settings menu."""
		# Contains the last settings which was successfully applied.
		self.last_working_settings = None

		# Create the settings window.
		with dpg.window(tag=item_id['windows']['settings_window'], label="Settings", height=150, width=450, 
		                modal=True, show=False, no_close=True, no_move=True, no_resize=True, no_collapse=True):
			# Create drop-down menu for Board-ID selector:
			all_boards = BoardIds._member_names_
			combo1 = dpg.add_combo(all_boards, label="Board ID", default_value=all_boards[2], tag=item_id['combos']['board_id'])

			# Create bottom row of buttons: OK, Reset & Cancel.
			dpg.add_spacer(height=10)
			with dpg.group(horizontal=True): 
				btn_width = 100 
				dpg.add_button(label="OK", callback=self.callback_settings_ok, width=btn_width, tag=item_id['buttons']['ok'])
				dpg.add_button(label="Reset", callback=self.callback_settings_reset, width=btn_width, tag=item_id['buttons']['reset'])
				dpg.add_button(label="Cancel", callback=self.callback_settings_cancel, width=btn_width, tag=item_id['buttons']['cancel'], enabled=False) # Initially disabled.

				# Gray out the cancel button initially. Used to indicate that settings must be loaded successfully at least once at program startup.
				self.default_theme = dpg.get_item_theme(item_id['buttons']['cancel'])
				with dpg.theme(tag=item_id['theme']['disabled']):
					with dpg.theme_component(dpg.mvButton, enabled_state=False): 
						dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (51, 51, 55))
						dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (51, 51, 55))
						dpg.add_theme_color(dpg.mvThemeCol_Text, (151, 151, 151))
				dpg.bind_item_theme(item_id['buttons']['cancel'], item_id['theme']['disabled'])

	def callback_enter_game(self):
		"""
		Callback function used to transition from the welcome screen to the main 
		game screen when the player presses the enter key at the welcome screen.
		"""
		# Change the active key-binds: Deactivate welcome screen binds, activate game screen binds.
		dpg.configure_item(item_id['registry']['enter_key'], show=False)
		dpg.configure_item(item_id['registry']['game_key_binds'], show=True)
		
		# Hide the welcome screen, show the main game screen.
		dpg.configure_item(item_id['windows']['welcome_window'], show=False)
		dpg.configure_item(item_id['windows']['main_window'], show=True)
			
		# Set the main game window as the primary window.
		dpg.set_primary_window(item_id['windows']['main_window'], True)
		
		# Show settings window if no settings are applied.
		if not self.settings_are_applied:
			self.callback_show_settings_menu()
		else: 
			self.callback_show_help_dialogue()
		
		# Force resize all items to ensure correct scaling/positions.
		self.window_resize()

	def callback_exit_game(self):
		"""
		Callback function used to transition from the main game screen to 
		the welcome screen. Tries to safely stop a running game if active.
		"""
		# Stop any currently running game.
		self.callback_stop_game()

		# Switch key-binds.
		dpg.configure_item(item_id['registry']['game_key_binds'], show=False)
		dpg.configure_item(item_id['registry']['enter_key'], show=True)
		
		# Hide main game window, show the welcome screen.
		dpg.configure_item(item_id['windows']['main_window'], show=False)
		dpg.configure_item(item_id['windows']['welcome_window'], show=True)

		# Set the welcome screen as the primary window.
		dpg.set_primary_window(item_id['windows']['welcome_window'], True)
		
		# Force resize all items to ensure correct scaling/positions.
		self.window_resize()

		# Reset help dialogue status.
		self.have_shown_help_dialogue = False

	def propagate_settings(self) -> list:
		"""Propagate settings selected in the GUI to the underlying game logic. """
		# Retrieve board ID string, parse it to an integer and send it to the boardshim.
		board_name = dpg.get_value(item_id['combos']['board_id'])
		board_id = BoardIds[board_name].value
		self.game.callback_set_board_id(board_id)

		# Collect all settings sent to the board.
		settings = [board_id]
		return settings

	def callback_settings_reset(self):
		"""
		Callback function to reset the GUI settings menu. If no settings 
		have previously been applied successfully, reset to defaults. Else
		reset to the settings which proved to be working before and 
		successfully were applied.
		"""
		if self.last_working_settings is None:
			settings = [0] # Defaults: [Synthetic board, ...]
		else:
			settings = self.last_working_settings
		
		# Set Board-ID in GUI drop down menu.
		board_id = settings[0]
		dpg.set_value(item_id['combos']['board_id'], value=BoardIds(board_id).name)
		
	def callback_settings_cancel(self):
		"""Callback function to discard new settings and close the settings window."""
		# Reset settings.
		self.callback_settings_reset()
		# Hide the settings window.
		dpg.configure_item(item_id['windows']['settings_window'], show=False)
		# Reactivate key-binds for main game screen.
		dpg.configure_item(item_id['registry']['game_key_binds'], show=True)

	def callback_show_settings_menu(self):
		"""Callback function to enter the settings menu."""
		self.callback_stop_game() # Stop any game currently running.
		dpg.split_frame() # Guarantee next lines will be rendered in a new frame.
		dpg.configure_item(item_id['windows']['settings_window'], show=True) # Show the window.
		dpg.configure_item(item_id['registry']['game_key_binds'], show=False) # Deactivate game key-binds.

	def callback_show_help_dialogue(self):
		"""Callback function to enter the help dialogue."""
		self.callback_stop_game() # Stop any game currently running.
		dpg.split_frame() # Guarantee next lines will be rendered in a new frame.
		dpg.configure_item(item_id['windows']['help_dialogue'], show=True) # Show the window.
		dpg.configure_item(item_id['registry']['game_key_binds'], show=False) # Deactivate game key-binds.

	def callback_close_help_dialogue(self):
		"""Callback function to close the help dialogue."""
		dpg.configure_item(item_id['windows']['help_dialogue'], show=False) # Hide the window.
		dpg.configure_item(item_id['registry']['game_key_binds'], show=True) # Reactivate game key-binds.

	def callback_settings_ok(self):
		"""
		Callback function for the "OK" button in the settings menu. 
		Tries to apply the current selection of settings when called.
		"""
		# Define helper function.
		def __enable_cancel_button():
			"""Enables the functionality of the "CANCEL" button of the settings menu."""
			dpg.configure_item(item_id['buttons']['cancel'], enabled=True) # enable button
			dpg.bind_item_theme(item_id['buttons']['cancel'], self.default_theme) # remove grayed-out theme.

		def __disable_cancel_button():
			"""Enables the functionality of the "CANCEL" button of the settings menu."""
			dpg.configure_item(item_id['buttons']['cancel'], enabled=False) # disable button
			dpg.bind_item_theme(item_id['buttons']['cancel'], item_id['theme']['disabled']) # apply grayed-out theme

		# Hide the settings window and show the loading screen.
		dpg.configure_item(item_id['windows']['settings_window'], show=False) # Hide settings
		dpg.split_frame() # Guarantee that the following lines are rendered in another frame. (Only one modal window can be active at any time.)
		dpg.configure_item(item_id['windows']['loading_screen'], show=True) # Show loading screen.
		
		

		# Propagate settings from the GUI to the boardshim. Let the boardshim attempt
		# to apply the settings and retrieve the status.
		settings_candidate = self.propagate_settings()
		status = self.game.callback_apply_settings()
		if status:
			# Settings were loaded successfully.
			dpg.configure_item(item_id['text']['loading'], default_value="Successfully applied settings.")
			if not self.settings_are_applied:
				__enable_cancel_button()
				self.settings_are_applied = True
			self.last_working_settings = settings_candidate # Save working settings.
		else:
			# Failure occured while attempting to load settings.
			dpg.configure_item(item_id['text']['loading'], default_value="Failure occured while applying settings.\nPlease check log for details.", pos=(95, 25))
			if self.settings_are_applied:
				__disable_cancel_button()
				self.settings_are_applied = False
			# TODO: MAKE SURE TO HANDLE EVENTUAL ERRORS

		# Freeze loading animation and wait a few seconds.
		dpg.configure_item(item_id['indicator']['settings_loading'], speed=0)
		time.sleep(2.5)

		# Hide the loading screen and reset it to default values.
		dpg.configure_item(item_id['windows']['loading_screen'], show=False) 
		dpg.configure_item(item_id['indicator']['settings_loading'], speed=1)
		dpg.configure_item(item_id['text']['loading'], default_value="Applying settings...", pos=(95, 37))

		# If successful, return the main game screen. Else return to the settings menu.
		if status:
			# Reactivate key-binds for main game screen:
			dpg.configure_item(item_id['registry']['game_key_binds'], show=True)
			# If this settings menu occured during initial setup, 
			# show the help dialogue on the way out. 
			if not self.have_shown_help_dialogue:
				self.callback_show_help_dialogue()
		else:
			# Show the settings menu.
			dpg.split_frame() # Guarantee following lines will be rendered in a new frame.
			dpg.configure_item(item_id['windows']['settings_window'], show=True)


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
		
		self.center_windows()
		self.resize_welcome_window()

	def center_windows(self):
		"""Center all small windows in the viewport."""
		# Get viewport dimensions.
		h = dpg.get_viewport_client_height()
		w = dpg.get_viewport_client_width()
		# Center the settings window in the viewport
		settings_h = dpg.get_item_height(item_id['windows']['settings_window'])
		settings_w = dpg.get_item_width(item_id['windows']['settings_window'])
		dpg.configure_item(item_id['windows']['settings_window'], pos=(w//2-settings_w//2, h//2-settings_h//2))
		print(f"settings: {h}, {w}, {settings_h}, {settings_w}")
		# Center the loading screen in the viewport
		loading_h = dpg.get_item_height(item_id['windows']['loading_screen'])
		loading_w = dpg.get_item_width(item_id['windows']['loading_screen'])
		dpg.configure_item(item_id['windows']['loading_screen'], pos=(w//2-loading_w//2, h//2-loading_h//2))
		print(f"loading:  {h}, {w}, {loading_h}, {loading_w}")

		# Center the help dialogue in the viewport.
		help_h = dpg.get_item_height(item_id['windows']['help_dialogue'])
		help_w = dpg.get_item_width(item_id['windows']['help_dialogue'])
		dpg.configure_item(item_id['windows']['help_dialogue'], pos=(w//2-help_w//2, h//2-help_h//2))

	def resize_welcome_window(self):
		"""Resize and reposition all text items on the welcome screen."""
		# Get viewport dimensions.
		h = dpg.get_viewport_client_height()
		w = dpg.get_viewport_client_width()
		# Title position
		title_width = dpg.get_item_width(item_id['text']['title'])
		title_xpos = w//2 - 325
		title_ypos = int(0.15*h)
		dpg.set_item_pos(item_id['text']['title'], (title_xpos, title_ypos))
		# Tagline position
		tagline_xpos = w//2 - 120
		tagline_ypos = title_ypos + 90
		dpg.set_item_pos(item_id['text']['tagline'], (tagline_xpos, tagline_ypos))
		# Press enter to start position
		enter_xpos = w//2 - 190
		enter_ypos = int(np.maximum(tagline_ypos + 100, 0.6*h)) 
		dpg.set_item_pos(item_id['text']['enter_key'], (enter_xpos, enter_ypos))
		# Copyright position
		copy_xpos = w//2 - 235
		copy_ypos = h - 50
		dpg.set_item_pos(item_id['text']['copyright'], (copy_xpos, copy_ypos))

	

	#----------------------------------------------------------------------
	#----------------------------------------------------------------------
	#----------------------------------------------------------------------

	def callback_start_game(self) -> None:
		"""Callback to start a new game."""
		if not self.game_is_running:
			try:
				logging.info("GUI: Starting game")
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
				self.game_is_running = False
				self.callback_stop_game()

		else:
			logging.info("GUI: Game is already running")

	def callback_stop_game(self, reset_game=False) -> None:
		"""Callback to stop and end a running game."""
		if self.game_is_running:
			logging.info("GUI: Stopping game")
			self.game_is_running = False
			self.game.stop_game()
			self.data.destroy()
			self.thread.join()
		else:
			logging.info("GUI: No game is running")


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





