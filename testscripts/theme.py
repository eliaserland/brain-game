import dearpygui.dearpygui as dpg
import dearpygui_ext.themes as dpg_ext

dpg.create_context()

light_theme = dpg_ext.create_theme_imgui_light()
dark_theme = dpg_ext.create_theme_imgui_dark()

with dpg.window(label="Tutorial", pos=(20, 50), width=275, height=225):
    dpg.add_button(label="Default Theme", callback=lambda: dpg.bind_theme(0))
    dpg.add_button(label="Light Theme", callback=lambda: dpg.bind_theme(light_theme))
    dpg.add_button(label="Dark Theme", callback=lambda: dpg.bind_theme(dark_theme))

with dpg.window(label="Second Window", pos=(120, 150), width=275, height=225, tag="second window"):
    dpg.add_button(label="Local Default Theme", callback=lambda: dpg.bind_item_theme("second window", 0))
    dpg.add_button(label="Local Light Theme", callback=lambda: dpg.bind_item_theme("second window", light_theme))
    dpg.add_button(label="Local Dark Theme", callback=lambda: dpg.bind_item_theme("second window", dark_theme))

dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()