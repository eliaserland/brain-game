import dearpygui.dearpygui as dpg
dpg.create_context()
from gui import GUI
from definitions import item_id

programName = 'BrainGame Curiosum'

def main():
	gui = GUI()
	#------------------------
	# Prepare dearpygui (these lines are always needed)
	dpg.create_context()
	#------------------------

	# Add a font registry
	with dpg.font_registry():
		default_font = dpg.add_font("Resources/Roboto-Regular.ttf", 20)
		#second_font = dpg.add_font("Resources/Roboto/Roboto-Medium.ttf", 18)
	dpg.bind_font(default_font)

	#dpg.show_metrics()
	gui.create_all_windows()
	#dpg.show_debug()
	
	#------------------------
	# (these lines are always needed)
	dpg.create_viewport(title=programName, vsync=True, resizable=True, width=1280, height=800)
	# must be called before showing viewport
	#pg.set_viewport_small_icon("path/to/icon.ico")
	#dpg.set_viewport_large_icon("path/to/icon.ico")
	dpg.setup_dearpygui()
	dpg.show_viewport()
	#------------------------
	
	dpg.set_primary_window(item_id['windows']['main_window'], True)
	dpg.set_viewport_resize_callback(callback=gui.window_resize)
	dpg.set_frame_callback(frame=1, callback=gui.startup_settings)

	# Set handler for fullscreen toggle on the F11-key.
	with dpg.handler_registry():
		dpg.add_key_press_handler(key=dpg.mvKey_F11, callback=dpg.toggle_viewport_fullscreen)
	#dpg.maximize_viewport()

	#------------------------
	# (these lines are always needed)
	dpg.start_dearpygui()
	dpg.destroy_context()

if __name__ == '__main__':
	main()