from time import sleep
import dearpygui.dearpygui as dpg
dpg.create_context() # Dearpygui context MUST be created before import of gui class.
from gui import GUI
from dpg_util import enter_viewport_fullscreen

programName = 'BrainGame Curiosum' # Name displayed on top of the main window.

def main():
	# Initialize the BrainGame graphical user interface.
	gui = GUI()
	#------------------------
	# Create viewport, setup dearpygui and show viewport. (These lines are always needed)
	dpg.create_viewport(title=programName, vsync=True, resizable=True, width=1280, height=800, min_width=960, min_height=600)
	#pg.set_viewport_small_icon("path/to/icon.ico")
	#dpg.set_viewport_large_icon("path/to/icon.ico")
	dpg.setup_dearpygui()
	dpg.show_viewport()
	#------------------------
	# Start the game in fullscreen.
	enter_viewport_fullscreen()
	#------------------------
	# Start dearpygui, and destroy context after exit. (These lines are always needed)
	while dpg.is_dearpygui_running():
		gui.callback_render_frame() # Executed at every frame
		dpg.render_dearpygui_frame() # Renders one frame.
	dpg.destroy_context()

if __name__ == '__main__':
	main()