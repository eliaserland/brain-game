from time import sleep
import dearpygui.dearpygui as dpg
dpg.create_context() # Dearpygui context MUST be created before gui import.
from gui import GUI
from definitions import item_id
from dpg_util import enter_viewport_fullscreen

programName = 'BrainGame Curiosum'

def main():
	gui = GUI()
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
	enter_viewport_fullscreen()
	#------------------------
	# (these lines are always needed)
	dpg.start_dearpygui()
	dpg.destroy_context()

if __name__ == '__main__':
	main()