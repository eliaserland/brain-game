import os
import time
import logging
import threading
import numpy as np

import dearpygui.dearpygui as dpg
from brainflow.board_shim import BoardIds

import braingame
from definitions import item_id, labels
from util import FPS, serial_ports
from dpg_util import *
import fonts

toggle_state = True # Initialization

# Parameters:
basepath = "resources" # Folder containing images.
images = ["sweden.png", "united_kingdom.png"] # Flags
lang = "eng" # Default language. Valid options: "swe", "eng".

class GUI:
	def __init__(self) -> None:
		"""Creates and initializes all windows for the graphical user interface."""
		# Create an instance of the main game.
		self.braingame = braingame.BrainGameInterface()
		self.braingame_is_running = False
		self.settings_are_applied = False
		self.have_shown_help_dialogue = False
		self.welcome_screen_visible = True
		self.init_time = time.time()
		self.start_time = 0
		self.stop_time = 1
		self.p1_time = 0
		self.p2_time = 0
		self.flags = [[True, False, False], [True, False, False]]
		self.p1_last_action = ""
		self.p2_last_action = ""
		
		# Create and initialize all GUI windows.
		self.__create_welcome_window()
		self.__create_main_window()
		self.__create_loading_screen()
		self.__create_settings_menu()
		self.__create_help_dialogue()

		# Set global callbacks.
		dpg.set_frame_callback(frame=1, callback=self.__startup_settings) # Executes on first frame.
		dpg.set_viewport_resize_callback(callback=self.window_resize) # Executes on window resize.
		dpg.set_exit_callback(callback=self.callback_quit_program) # Executes on program window exit.		

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
			dpg.add_text(labels['welcome_title'][lang], tag=item_id['text']['title'])
			dpg.add_text(labels['welcome_tagline'][lang], tag=item_id['text']['tagline'])
			dpg.add_text(labels['welcome_enter'][lang], tag=item_id['text']['enter_key'])
			dpg.add_text(labels['welcome_copyright'][lang], tag=item_id['text']['copyright'])
			# Flag-image buttons for language selection.
			with dpg.group(horizontal=True):
				item_id['buttons']["img_swe_main"] = add_and_load_image_button(os.path.join(basepath, images[0]), callback=self.set_swedish)
				item_id['buttons']["img_eng_main"] = add_and_load_image_button(os.path.join(basepath, images[1]), callback=self.set_english)
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

		# Key bind: Game start/stop toggle on enter-key and spacebar. Default state: deactivated.
		with dpg.handler_registry(tag=item_id['registry']['game_key_binds'], show=False):
			dpg.add_key_press_handler(key=dpg.mvKey_Return, callback=self.toggle_start_stop_game)
			dpg.add_key_press_handler(key=dpg.mvKey_Spacebar, callback=self.toggle_start_stop_game)

		# Create the window. Initially hidden.
		with dpg.window(tag=item_id['windows']['main_window'], show=False):
			with dpg.group(horizontal=True): # Horizontal grouping.
				# Left column: add game buttons and text items
				self.col_width = 200
				with dpg.child_window(tag=item_id['windows']['child_window'], width=self.col_width):
					dpg.add_spacer(height=5)
					dpg.add_text(' BrainGame\n Curisosum', tag=item_id['text']['title_game'])
					dpg.add_spacer(height=10)
					dpg.add_text(labels["info_game"][lang], tag=item_id['text']['info_game'], wrap=self.col_width-8)
					dpg.add_spacer(height=10)
					# Main game buttons
					btn_width = self.col_width - 16
					btn_h1 = 70
					btn_h2 = 35
					dpg.add_button(label=labels['start_btn'][lang], width=btn_width, height=btn_h1, tag=item_id['buttons']['start_stop'], callback=self.toggle_start_stop_game)
					dpg.add_button(label=labels['help_btn'][lang], width=btn_width, height=btn_h2, tag=item_id['buttons']['help_open'], callback=self.callback_show_help_dialogue)
					dpg.add_button(label=labels['exit_btn'][lang], width=btn_width, height=btn_h2, tag=item_id['buttons']['exit'], callback=self.callback_exit_game)
					# Flag-image buttons for language selection.
					with dpg.group(horizontal=True):
						item_id['buttons']["img_swe_main"] = add_and_load_image_button(os.path.join(basepath, images[0]), callback=self.set_swedish)
						item_id['buttons']["img_eng_main"] = add_and_load_image_button(os.path.join(basepath, images[1]), callback=self.set_english)
					# Settings button.
					dpg.add_button(label=labels['settings_btn'][lang], width=btn_width, height=btn_h2, tag=item_id['buttons']['settings'], callback=self.callback_show_settings_menu)
				# Set fonts.
				dpg.bind_item_font(item_id['text']['title_game'], fonts.large_bold)
				dpg.bind_item_font(item_id['text']['info_game'], fonts.intermediate_font)
				
				# Green theme for the start/stop button.
				with dpg.theme(tag=item_id['theme']['start_green']):
					with dpg.theme_component(dpg.mvButton): 
						dpg.add_theme_color(dpg.mvThemeCol_Button, (25, 105, 47))
						dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 168, 82))
						dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (49, 181, 85))
				# Red theme for the start/stop button.
				with dpg.theme(tag=item_id['theme']['stop_red']):
					with dpg.theme_component(dpg.mvButton): 
						dpg.add_theme_color(dpg.mvThemeCol_Button, (145, 10, 10))
						dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (179, 16, 16))
						dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (194, 17, 17))
				# Set initial theme of start/stop button.
				dpg.bind_item_theme(item_id['buttons']['start_stop'], item_id['theme']['start_green'])

				# Right column: add plotting window with respective graphs.
				with dpg.child_window(autosize_x=True):
					# Create all graphs for plotting:
					self.__create_all_graphs()
	
	def __create_all_graphs(self):
		"""Create and initialize all plotting graphs of the main game window."""
		y_min, y_max = -100, 100 # Time series y-axis limits.

		# --- TIME SERIES GRAPHS ---
		with dpg.plot(label=labels['p1_ts_title'][lang], tag=item_id['plots']['timeseries1'], anti_aliased=True):
			# REQUIRED: create x and y axes
			dpg.add_plot_axis(dpg.mvXAxis, label=labels['ts_xax'][lang], tag=item_id['axes']['timeseries1_xaxis'], no_gridlines=True)
			dpg.add_plot_axis(dpg.mvYAxis, label=labels['ts_yax'][lang], tag=item_id['axes']['timeseries1_yaxis'], no_gridlines=True)

			# series belong to a y axis
			dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=item_id['axes']['timeseries1_yaxis'], tag=item_id['line_series']['timeseries1'])
			dpg.set_axis_limits(item_id['axes']['timeseries1_yaxis'], y_min, y_max)
			dpg.set_axis_limits(item_id['axes']['timeseries1_xaxis'], -5, 0)

		with dpg.plot(label=labels['p2_ts_title'][lang], tag=item_id['plots']['timeseries2'], anti_aliased=True):
			# REQUIRED: create x and y axes
			dpg.add_plot_axis(dpg.mvXAxis, label=labels['ts_xax'][lang], tag=item_id['axes']['timeseries2_xaxis'], no_gridlines=True)
			dpg.add_plot_axis(dpg.mvYAxis, label=labels['ts_yax'][lang], tag=item_id['axes']['timeseries2_yaxis'], no_gridlines=True)

			# series belong to a y axis
			dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=item_id['axes']['timeseries2_yaxis'], tag=item_id['line_series']['timeseries2'])
			dpg.set_axis_limits(item_id['axes']['timeseries2_yaxis'], y_min, y_max)
			dpg.set_axis_limits(item_id['axes']['timeseries2_xaxis'], -5, 0)
		
		# --- BAR SERIES GRAPHS ---
		# Ticks, initial values, bar widths
		tick_pos = list(range(5))
		tick_labels = ['Delta\n1-4Hz', 'Theta\n4-8Hz', 'Alpha\n8-13Hz', '  Beta\n13-30Hz', 'Gamma\n30-50Hz']
		xticks = tuple(zip(tick_labels, tick_pos))
		y_init = [1]*5
		y_min, y_max = 10**-5, 10**2
		bar_width = 0.85
	
		with dpg.plot(label=labels["p1_br_title"][lang], tag=item_id['plots']['bar1']): # TODO: manual scaling in resize function
			# create x axis
			dpg.add_plot_axis(dpg.mvXAxis, tag=item_id['axes']['bar1_xaxis'], no_gridlines=True)
			dpg.set_axis_limits(dpg.last_item(), tick_pos[0]-bar_width/2-(1-bar_width), tick_pos[-1]+bar_width/2+(1-bar_width) )
			dpg.set_axis_ticks(dpg.last_item(), xticks)

			# create y axis
			with dpg.plot_axis(dpg.mvYAxis, tag=item_id['axes']['bar1_yaxis'], label=labels['br_yax'][lang], log_scale=True):
				dpg.set_axis_limits(dpg.last_item(), y_min, y_max)
				for i, (xpos, yval) in enumerate(zip(tick_pos, y_init)):
					dpg.add_bar_series([xpos], [yval], tag=item_id["bar1_series"][i], weight=bar_width)

		with dpg.plot(label=labels["p2_br_title"][lang], tag=item_id['plots']['bar2']): # TODO: manual scaling in resize function
			# create x axis
			dpg.add_plot_axis(dpg.mvXAxis, tag=item_id['axes']['bar2_xaxis'], no_gridlines=True)
			dpg.set_axis_limits(dpg.last_item(), tick_pos[0]-bar_width/2-(1-bar_width), tick_pos[-1]+bar_width/2+(1-bar_width) )
			dpg.set_axis_ticks(dpg.last_item(), xticks)

			# create y axis
			with dpg.plot_axis(dpg.mvYAxis, tag=item_id['axes']['bar2_yaxis'], label=labels['br_yax'][lang], log_scale=True):
				dpg.set_axis_limits(dpg.last_item(), y_min, y_max)
				for i, (xpos, yval) in enumerate(zip(tick_pos, y_init)):
					dpg.add_bar_series([xpos], [yval], tag=item_id["bar2_series"][i], weight=bar_width)

		# -- FOCUS METRIC GRAPHS ---
		with dpg.plot(label=labels['p1_me_title'][lang], tag=item_id['plots']['metric1'],  anti_aliased=True):
			# REQUIRED: create x and y axes
			dpg.add_plot_axis(dpg.mvXAxis, label=labels['me_xax'][lang], tag=item_id['axes']['metric1_xaxis'], no_gridlines=True)
			dpg.add_plot_axis(dpg.mvYAxis, label=labels['me_yax'][lang], tag=item_id['axes']['metric1_yaxis'], no_gridlines=True)

			# series belong to a y axis
			dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=item_id['axes']['metric1_yaxis'], tag=item_id['line_series']['metric1'])
			dpg.set_axis_limits(item_id['axes']['metric1_yaxis'], -0.005, 1.005)
			dpg.set_axis_limits(item_id['axes']['metric1_xaxis'], -5, 0)
		
		with dpg.plot(label=labels['p2_me_title'][lang], tag=item_id['plots']['metric2'],  anti_aliased=True):
			# REQUIRED: create x and y axes
			dpg.add_plot_axis(dpg.mvXAxis, label=labels['me_xax'][lang], tag=item_id['axes']['metric2_xaxis'], no_gridlines=True)
			dpg.add_plot_axis(dpg.mvYAxis, label=labels['me_yax'][lang], tag=item_id['axes']['metric2_yaxis'], no_gridlines=True)

			# series belong to a y axis
			dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=item_id['axes']['metric2_yaxis'], tag=item_id['line_series']['metric2'])
			dpg.set_axis_limits(item_id['axes']['metric2_yaxis'], -0.005, 1.005)
			dpg.set_axis_limits(item_id['axes']['metric2_xaxis'], -5, 0)

		# --- STATUS INDICATORS ---
		# Status text at bottom of the main game screen
		dpg.add_text(labels['status_paused'][lang], pos=(0,0), tag=item_id['text']['p1_status'])
		dpg.add_text(labels['status_paused'][lang], pos=(0,0), tag=item_id['text']['p2_status'])
		dpg.bind_item_font(item_id['text']['p1_status'], fonts.medium_font)
		dpg.bind_item_font(item_id['text']['p2_status'], fonts.medium_font)

		# Animated status icons
		width, height, channels, data = dpg.load_image(os.path.join(basepath, "spritesheet_3by28.png"))
		with dpg.texture_registry():
			dpg.add_static_texture(width, height, data, tag=item_id['textures']['spritesheet'])
		with dpg.drawlist(tag=item_id['drawlist'], width=100, height=100):
			dpg.draw_image(item_id['textures']['spritesheet'], (0, 0), (100, 100), uv_min=(13/28, 0), uv_max=(14/28, 1/3), tag=item_id['images']['p1_icon'], show=True)
			dpg.draw_image(item_id['textures']['spritesheet'], (0, 0), (100, 100), uv_min=(13/28, 0), uv_max=(14/28, 1/3), tag=item_id['images']['p2_icon'], show=True)
		

	def __create_loading_screen(self):
		"""Create the loading screen."""
		# Create the window. Initially hidden.
		with dpg.window(tag=item_id['windows']['loading_screen'], height=100, width=450, show=False, no_resize=True, 
		                no_close=False, no_move=True, no_title_bar=True, modal=True):
			dpg.add_loading_indicator(tag=item_id['indicator']['settings_loading'], pos=(20, 19), style=0)
			dpg.add_text(labels['loading_applying'][lang], pos=(95, 35), tag=item_id['text']['loading'])

	def __create_help_dialogue(self):
		"""Create the help dialogue."""
		# Create the window. Initially hidden.
		h, w = 500, 700
		with dpg.window(label=labels['help_title'][lang], tag=item_id['windows']['help_dialogue'], height=h, width=w, show=False, 
		                no_resize=True, no_move=True, modal=True, no_title_bar=False, on_close=self.callback_close_help_dialogue):
			dpg.add_text(labels['help_text'][lang], tag=item_id['text']['help'])
			btn_h, btn_w = 35, 200-16
			dpg.add_button(label=labels['help_close'][lang], tag=item_id['buttons']['help_close'], callback=self.callback_close_help_dialogue, pos=(w//2 - btn_w//2, h-50), height=btn_h, width=btn_w)

	def __create_settings_menu(self):
		"""Create the settings menu."""
		# Contains the last settings which was successfully applied.
		self.last_working_settings = None
		# Create the settings window.
		h, w = 150, 450
		with dpg.window(tag=item_id['windows']['settings_window'], label=labels['settings_title'][lang], height=h, width=w, 
		                modal=True, show=False, no_close=True, no_move=True, no_resize=True, no_collapse=True):
			# Create drop-down menu for Board-ID selector:
			all_boards = BoardIds._member_names_
			dpg.add_combo(all_boards, label=labels['sett_boardid'][lang], default_value=all_boards[2], tag=item_id['combos']['board_id'])

			# Create bottom row of buttons: OK, Reset & Cancel.
			dpg.add_spacer(height=10)
			with dpg.group(horizontal=True): 
				btn_w, btn_h = 100, 30 
				dpg.add_button(label=labels['settings_ok'][lang], callback=self.callback_settings_ok, width=btn_w, height=btn_h, tag=item_id['buttons']['ok'], pos=(w//2-btn_w//2 - btn_w-8, h-btn_h-8))
				dpg.add_button(label=labels['settings_reset'][lang], callback=self.callback_settings_reset, width=btn_w, height=btn_h, tag=item_id['buttons']['reset'], pos=(w//2-btn_w//2, h-btn_h-8))
				dpg.add_button(label=labels['settings_cancel'][lang], callback=self.callback_settings_cancel, width=btn_w, height=btn_h, tag=item_id['buttons']['cancel'], pos=(w//2-btn_w//2+btn_w+8, h-btn_h-8), enabled=False) # Initially disabled.

				# Gray out the cancel button initially. Used to indicate that settings must be loaded successfully at least once at program startup.
				self.default_theme = dpg.get_item_theme(item_id['buttons']['cancel'])
				with dpg.theme(tag=item_id['theme']['disabled']):
					with dpg.theme_component(dpg.mvButton, enabled_state=False): 
						dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (51, 51, 55))
						dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (51, 51, 55))
						dpg.add_theme_color(dpg.mvThemeCol_Text, (151, 151, 151))
				dpg.bind_item_theme(item_id['buttons']['cancel'], item_id['theme']['disabled'])

	def callback_render_frame(self):
		"""Callback function executed at every rendered frame."""
		if self.welcome_screen_visible: 
			# Make "enter-key" phrase pulsate at the welcome screen.
			t = time.time() - self.init_time
			opacity = int(128*np.sin(3*t) + 128) # In range [0, 256)
			dpg.configure_item(item_id['text']['enter_key'], color=(255, 255, 255, opacity))
		else:
			# Helper functions related to the animation of the two status icons.
			def softstep(x: float, alpha: float=1):
				return np.maximum(0, np.minimum(alpha*x, 1))

			def stop_animation(dt: float, duration: float=0.3, num_frames: int=28):
				idx = np.floor(0.5*softstep(dt, alpha=1/duration)*num_frames)
				return (idx/num_frames, 0), ((idx+1)/num_frames, 1/3)
			
			def start_animation(dt: float, duration: float=0.3, num_frames: int=28):
				idx = np.floor(0.5*(1-softstep(dt, alpha=1/duration))*num_frames)
				return (idx/num_frames, 0), ((idx+1)/num_frames, 1/3)

			def checkmark_animation(dt: float, duration: float=1.25, num_frames:int=28):
				idx = np.floor(softstep(dt, alpha=1/duration)*num_frames)
				return idx/num_frames, (idx+1)/num_frames
			
			def cogwheel_animation(dt: float, duration: float=2.5, num_frames: int=28):
				idx = np.floor(softstep(dt, alpha=1/duration)*2*num_frames) % num_frames
				return idx/num_frames, (idx+1)/num_frames

			def action_animation(dt: float, player: int, status_id: str, status_dir: str):
				checkmark_duration = 1.25 # in seconds
				cogwheel_duration = 2 # in seconds
				if dt < checkmark_duration:
					# Play the checkmark animation
					u_min, u_max = checkmark_animation(dt, duration=checkmark_duration)
					v_min, v_max = 1/3, 2/3
					if self.flags[player][0]:
						self.flags[player][0] = False
						self.flags[player][1] = True
						dpg.configure_item(item_id['text'][status_id], default_value=labels['status_detected'][lang])
				elif dt-checkmark_duration < cogwheel_duration:
					# Play cogwheel animation
					u_min, u_max = cogwheel_animation(dt-checkmark_duration, duration=cogwheel_duration)
					v_min, v_max = 2/3, 1
					if self.flags[player][1]:
						self.flags[player][1] = False
						self.flags[player][2] = True 
						dpg.configure_item(item_id['text'][status_id], default_value=labels[status_dir][lang])
				else:
					# Display the static "play" icon
					u_min, u_max = 0, 1/28
					v_min, v_max = 0, 1/3
					if self.flags[player][2]:
						self.flags[player][2] = False
						self.flags[player][0] = True
						dpg.configure_item(item_id['text'][status_id], default_value=labels['status_wait'][lang])
				return (u_min, v_min), (u_max, v_max)

			now = time.time()
			time_newest_event = np.max([self.start_time, self.stop_time, self.p1_time, self.p2_time])
			if now-time_newest_event < 15:
				if self.stop_time > np.max([self.start_time, self.p1_time, self.p2_time]):
					# Stop animation
					uv_min_p1, uv_max_p1 = stop_animation(now-self.stop_time)
					uv_min_p2, uv_max_p2 = uv_min_p1, uv_max_p1
				elif self.start_time > np.max([self.p1_time, self.p2_time]):
					# Start animation
					uv_min_p1, uv_max_p1 = start_animation(now-self.start_time)
					uv_min_p2, uv_max_p2 = uv_min_p1, uv_max_p1
				else:
					# Action animation player 1 & 2
					uv_min_p1, uv_max_p1 = action_animation(now-self.p1_time, player=0, status_id="p1_status", status_dir=self.p1_last_action)
					uv_min_p2, uv_max_p2 = action_animation(now-self.p2_time, player=1, status_id="p2_status", status_dir=self.p2_last_action)

				dpg.configure_item(item_id['images']['p1_icon'], uv_min=uv_min_p1, uv_max=uv_max_p1)
				dpg.configure_item(item_id['images']['p2_icon'], uv_min=uv_min_p2, uv_max=uv_max_p2)

	def trigger_start_animation(self):
		"""
		Trigger the "start" animation sequence for the two status icons.
		"""
		self.start_time = time.time()
		dpg.configure_item(item_id['text']['p1_status'], default_value=labels['status_wait'][lang])
		dpg.configure_item(item_id['text']['p2_status'], default_value=labels['status_wait'][lang])

	def trigger_stop_animation(self):
		"""
		Trigger the "stop" animation sequence for the two status icons. 
		"""
		self.stop_time = time.time()
		dpg.configure_item(item_id['text']['p1_status'], default_value=labels['status_paused'][lang])
		dpg.configure_item(item_id['text']['p2_status'], default_value=labels['status_paused'][lang])

	def trigger_action_animation(self, player: int, direction: int):
		"""
		Trigger animation sequence for one of the two status icons, in the
		specified direction.
		"""
		p1_actions = ["status_left", "status_right"]
		p2_actions = ["status_forward", "status_backward"]
		if player == 0:
			self.p1_last_action = p1_actions[direction]
			self.p1_time = time.time()
		elif player == 1:
			self.p2_last_action = p2_actions[direction]
			self.p2_time = time.time()
		else:
			raise BaseException

#self.trigger_action_animation(1, 0) # TODO: USE THIS SOMEWHERE



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
		self.welcome_screen_visible = False
		
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
		self.welcome_screen_visible = True

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
		self.braingame.callback_set_board_id(board_id)

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
			settings = [0, ] # Defaults: [Synthetic board, ...]
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
		self.have_shown_help_dialogue = True

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
		status = self.braingame.callback_apply_settings()
		if status:
			# Settings were loaded successfully.
			dpg.configure_item(item_id['text']['loading'], default_value=labels['loading_success'][lang])
			if not self.settings_are_applied:
				__enable_cancel_button()
				self.settings_are_applied = True
			self.last_working_settings = settings_candidate # Save working settings.
		else:
			# Failure occured while attempting to load settings.
			dpg.configure_item(item_id['text']['loading'], default_value=labels['loading_failure'][lang], pos=(95, 25))
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
		dpg.configure_item(item_id['text']['loading'], default_value=labels['loading_applying'][lang], pos=(95, 37))

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

		h = dpg.get_viewport_client_height()
		w = dpg.get_viewport_client_width()

		# Resizing and repositioning of the plots.
		xpos = [0, 1, 0, 1, 0, 1]
		ypos = [0, 0, 1, 1, 2, 2]
		plt_h, plt_w = h//3.3 - 24/3, w//2 - self.col_width//2 - 16 
		for i, plot in enumerate(item_id['plots'].values()):
			pos = (plt_w*xpos[i], plt_h*ypos[i])
			dpg.configure_item(plot, height=plt_h, width=plt_w, pos=pos)

		# Position of flag-buttons and settings-button.
		dpg.configure_item(item_id['buttons']["img_swe_main"], pos=(8, h-124))
		dpg.configure_item(item_id['buttons']['settings'], pos=(8, h-60))
		
		# Position and scaling of the animated icons.
		status_h, status_w = int(h-3*plt_h+24), int(2*plt_w) # Size of entire bottom "stripe" area for status indicators
		icon_w = int(0.4*status_h)
		y_offset = -5
		x_offset = -60
		# Canvas to draw the icons on
		dpg.configure_item(item_id['drawlist'], width=w-self.col_width-40, height=h-32) 
		# Animated icons:
		dpg.configure_item(item_id['images']['p1_icon'], pmin=(status_w/4-icon_w/2+x_offset, h-status_h/2-icon_w/2+y_offset), pmax=(status_w/4+icon_w/2+x_offset, h-status_h/2+icon_w/2+y_offset))
		dpg.configure_item(item_id['images']['p2_icon'], pmin=(status_w*3/4-icon_w/2+x_offset, h-status_h/2-icon_w/2+y_offset), pmax=(status_w*3/4+icon_w/2+x_offset, h-status_h/2+icon_w/2+y_offset))
		# Status text at the bottom of the screen
		relx_offset = 30
		dpg.configure_item(item_id['text']['p1_status'], pos=(status_w/4+icon_w/2+x_offset+relx_offset, h-status_h/2-14))
		dpg.configure_item(item_id['text']['p2_status'], pos=(status_w*3/4+icon_w/2+x_offset+relx_offset, h-status_h/2-14))

		# Call additional functions.
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
		# Title position (manual adjustment for each language)
		title_xpos = {
			"eng": w//2 - 325,
			"swe": w//2 - 325,
		}
		title_ypos = int(0.15*h)
		dpg.set_item_pos(item_id['text']['title'], (title_xpos[lang], title_ypos))
		# Tagline position
		tagline_xpos = {
			"eng": w//2 - 120, 
			"swe": w//2 - 135,
		}
		tagline_ypos = title_ypos + 90
		dpg.set_item_pos(item_id['text']['tagline'], (tagline_xpos[lang], tagline_ypos))
		# Press enter to start position
		enter_xpos = {
			"eng": w//2 - 160,
			"swe": w//2 - 195,
		}
		enter_ypos = int(np.maximum(tagline_ypos + 100, 0.6*h)) 
		dpg.set_item_pos(item_id['text']['enter_key'], (enter_xpos[lang], enter_ypos))
		# Copyright position
		copy_xpos = {
			"eng": w//2 - 445,
			"swe": w//2 - 445,
		}
		copy_ypos = h - 50
		dpg.set_item_pos(item_id['text']['copyright'], (copy_xpos[lang], copy_ypos))

	def set_swedish(self):
		self.set_language("swe")
		self.window_resize()

	def set_english(self):
		self.set_language("eng")
		self.window_resize()

	def set_language(self, language):
		"""Apply the specifed language to all text items and labels."""
		global lang
		lang = language # Set the global language

		# Set start/stop button.
		if self.braingame_is_running:
			dpg.configure_item(item_id['buttons']['start_stop'], label=labels['stop_btn'][lang])
		else: 
			dpg.configure_item(item_id['buttons']['start_stop'], label=labels['start_btn'][lang])
		# Set help, exit, settings buttons.
		dpg.configure_item(item_id['buttons']['help_open'], label=labels['help_btn'][lang])
		dpg.configure_item(item_id['buttons']['exit'], label=labels['exit_btn'][lang])
		dpg.configure_item(item_id['buttons']['settings'], label=labels['settings_btn'][lang])
		
		# Short description on main game screen.
		dpg.configure_item(item_id['text']['info_game'], default_value=labels["info_game"][lang])

		# Welcome screen
		dpg.configure_item(item_id['text']['title'], default_value=labels['welcome_title'][lang])
		dpg.configure_item(item_id['text']['tagline'], default_value=labels['welcome_tagline'][lang])
		dpg.configure_item(item_id['text']['enter_key'], default_value=labels['welcome_enter'][lang])
		dpg.configure_item(item_id['text']['copyright'], default_value=labels['welcome_copyright'][lang])

		# Plots - Time series
		dpg.configure_item(item_id['plots']['timeseries1'], label=labels['p1_ts_title'][lang])
		dpg.configure_item(item_id['plots']['timeseries2'], label=labels['p2_ts_title'][lang])
		dpg.configure_item(item_id['axes']['timeseries1_xaxis'], label=labels['ts_xax'][lang])
		dpg.configure_item(item_id['axes']['timeseries1_yaxis'], label=labels['ts_yax'][lang])
		dpg.configure_item(item_id['axes']['timeseries2_xaxis'], label=labels['ts_xax'][lang])
		dpg.configure_item(item_id['axes']['timeseries2_yaxis'], label=labels['ts_yax'][lang])

		# Plots - Band Power
		dpg.configure_item(item_id['plots']['bar1'], label=labels["p1_br_title"][lang])
		dpg.configure_item(item_id['plots']['bar2'], label=labels["p2_br_title"][lang])
		dpg.configure_item(item_id['axes']['bar1_yaxis'], label=labels['br_yax'][lang])
		dpg.configure_item(item_id['axes']['bar2_yaxis'], label=labels['br_yax'][lang])
	
		# Plots - Focus Metric
		dpg.configure_item(item_id['plots']['metric1'], label=labels['p1_me_title'][lang])
		dpg.configure_item(item_id['plots']['metric2'], label=labels['p2_me_title'][lang])
		dpg.configure_item(item_id['axes']['metric1_xaxis'], label=labels['me_xax'][lang])
		dpg.configure_item(item_id['axes']['metric1_yaxis'], label=labels['me_yax'][lang])
		dpg.configure_item(item_id['axes']['metric2_xaxis'], label=labels['me_xax'][lang])
		dpg.configure_item(item_id['axes']['metric2_yaxis'], label=labels['me_yax'][lang])

		# Status text
		if self.braingame_is_running:
			dpg.configure_item(item_id['text']['p1_status'], default_value=labels['status_wait'][lang])
			dpg.configure_item(item_id['text']['p2_status'], default_value=labels['status_wait'][lang])
		else:
			dpg.configure_item(item_id['text']['p1_status'], default_value=labels['status_paused'][lang])
			dpg.configure_item(item_id['text']['p2_status'], default_value=labels['status_paused'][lang])

		# Help dialogue
		dpg.configure_item(item_id['windows']['help_dialogue'], label=labels['help_title'][lang])
		dpg.configure_item(item_id['text']['help'], default_value=labels['help_text'][lang])
		dpg.configure_item(item_id['buttons']['help_close'], label=labels['help_close'][lang])

		# Settings window
		dpg.configure_item(item_id['windows']['settings_window'], label=labels['settings_title'][lang])
		dpg.configure_item(item_id['combos']['board_id'], label=labels['sett_boardid'][lang])
		dpg.configure_item(item_id['buttons']['ok'], label=labels['settings_ok'][lang])
		dpg.configure_item(item_id['buttons']['reset'], label=labels['settings_reset'][lang])
		dpg.configure_item(item_id['buttons']['cancel'], label=labels['settings_cancel'][lang])

		# Loading screen
		dpg.configure_item(item_id['text']['loading'], default_value=labels['loading_applying'][lang])

	#----------------------------------------------------------------------
	#----------------------------------------------------------------------
	#----------------------------------------------------------------------

	def toggle_start_stop_game(self):
		"""Wrapper function for game start/stop toggle functionality."""
		global toggle_state
		if toggle_state:
			self.callback_start_game()
		else:
			self.callback_stop_game()

	def callback_start_game(self) -> None:
		"""Callback to start a new game."""
		global toggle_state
		if not self.braingame_is_running:
			try:
				logging.info("GUI: Starting game")
				# Start the main game.
				self.braingame.start_game(fresh_start=False)
				# Set flag & start the gui plotting thread.
				self.braingame_is_running = True
				self.thread = threading.Thread(target=self.__gui_loop, daemon=False)
				self.thread.start()

				#-----
				# Set theme of start/stop button
				dpg.configure_item(item_id['buttons']['start_stop'], label=labels['stop_btn'][lang])
				dpg.bind_item_theme(item_id['buttons']['start_stop'], item_id['theme']['stop_red'])
				# Toggle start/stop state.
				toggle_state = not toggle_state
				# "Start"-animation of status icon
				self.trigger_start_animation()
				#----

			except BaseException:
				logging.warning('Exception', exc_info=True)
				self.braingame_is_running = False
				self.callback_stop_game()

		else:
			logging.info("GUI: callback_start_game: Game is already running")

	def __gui_loop(self):
		"""Main thread function for updating the GUI plots during a game."""
		fps_timer = FPS()
		while self.braingame_is_running:
			# Increment game logic, get data and update graphs.
			quantities, actions, data  = self.braingame.update_game()
			self.__update_plots((quantities, actions))
			
			# Print fps counter
			fps = fps_timer.calc()
			print(f"FPS: {fps:.3f}", end='\r')

	def callback_stop_game(self, reset_game=False) -> None:
		"""Callback to stop and end a running game."""
		global toggle_state
		if self.braingame_is_running:
			logging.info("GUI: Stopping game")
			self.braingame_is_running = False
			self.thread.join()
			self.braingame.stop_game()
			#----
			# Set theme of start/stop button
			dpg.configure_item(item_id['buttons']['start_stop'], label=labels['start_btn'][lang])
			dpg.bind_item_theme(item_id['buttons']['start_stop'], item_id['theme']['start_green'])
			# Toggle start/stop state.
			toggle_state = not toggle_state
			# "Stop"-animation of status icon.
			self.trigger_stop_animation()
			#----
		else:
			logging.info("GUI: No game is running")

	def callback_quit_program(self):
		self.callback_stop_game()
		self.braingame.quit_game()

	def __update_plots(self, data):
			(player1, player2), actions = data
			time1, timeseries1 = player1['time_series']
			time2, timeseries2 = player2['time_series']
			metric_time1, metric1 = player1['focus_metric']
			metric_time2, metric2 = player2['focus_metric']

			band_power1 = player1['band_power']
			band_power2 = player2['band_power']

			#print("Actions: " + ' '.join(actions) + f"  {metric1[-1]:.5f} {metric2[-1]:.5f}", end='\r')
			dpg.set_value(item_id['line_series']['timeseries1'], [list(time1), list(timeseries1)])
			dpg.set_value(item_id['line_series']['timeseries2'], [list(time2), list(timeseries2)])
			dpg.set_value(item_id['line_series']['metric1'], [list(metric_time1), list(metric1)])
			dpg.set_value(item_id['line_series']['metric2'], [list(metric_time2), list(metric2)])

			# Update bar graphs with power band data.
			for i, (xpos, yval) in enumerate(zip(range(5), band_power1)):
				dpg.set_value(item_id["bar1_series"][i], ([xpos],[yval]))
			for i, (xpos, yval) in enumerate(zip(range(5), band_power2)):
				dpg.set_value(item_id["bar2_series"][i], ([xpos],[yval]))

	def callback_timeseries_settings(self):
		pass

	def callback_focus_settings(self):
		pass


def add_and_load_image_button(image_path, parent=None, callback=None):
	width, height, channels, data = dpg.load_image(image_path)
	with dpg.texture_registry() as reg_id:
		texture_id = dpg.add_static_texture(width, height, data, parent=reg_id)
	if parent is None:
		return dpg.add_image_button(texture_id, width=80, height=80/1.6, callback=callback)
	else:
		return dpg.add_image_button(texture_id, width=80, height=80/1.6, parent=parent, callback=callback)


