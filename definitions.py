# Sets up all important config variables
import dearpygui.dearpygui as dpg

# Set up all IDs required by items in Dear PyGui
item_id = {
	"windows": {
		"main_window": dpg.generate_uuid(),
		"welcome_window": dpg.generate_uuid(),
		"settings_window": dpg.generate_uuid(),
		"loading_screen": dpg.generate_uuid(),
		"help_dialogue": dpg.generate_uuid(),
		"child_window": dpg.generate_uuid(),
	},
	"plots": {
		"timeseries1": dpg.generate_uuid(),
		"timeseries2": dpg.generate_uuid(),
		"bar1": dpg.generate_uuid(),
		"bar2": dpg.generate_uuid(),
		"metric1": dpg.generate_uuid(),
		"metric2": dpg.generate_uuid(),
	},
	"line_series": {
		"timeseries1": dpg.generate_uuid(),
		"timeseries2": dpg.generate_uuid(),
		"metric1": dpg.generate_uuid(),
		"metric2": dpg.generate_uuid()
	},
	"bar1_series": [dpg.generate_uuid(), dpg.generate_uuid(), dpg.generate_uuid(), 
	               dpg.generate_uuid(), dpg.generate_uuid()],
	"bar2_series": [dpg.generate_uuid(), dpg.generate_uuid(), dpg.generate_uuid(), 
	               dpg.generate_uuid(), dpg.generate_uuid()],
	"axes": {
		"timeseries1_yaxis": dpg.generate_uuid(),
		"timeseries1_xaxis": dpg.generate_uuid(),
		"timeseries2_yaxis": dpg.generate_uuid(),
		"timeseries2_xaxis": dpg.generate_uuid(),
		"bar1_yaxis": dpg.generate_uuid(),
		"bar1_xaxis": dpg.generate_uuid(),
		"bar2_yaxis": dpg.generate_uuid(),
		"bar2_xaxis": dpg.generate_uuid(),
		"metric1_yaxis": dpg.generate_uuid(),
		"metric1_xaxis": dpg.generate_uuid(),
		"metric2_yaxis": dpg.generate_uuid(),
		"metric2_xaxis": dpg.generate_uuid()
	},
	"buttons": {
		'start_stop': dpg.generate_uuid(),
		"exit": dpg.generate_uuid(),
		"settings": dpg.generate_uuid(),
		"ok": dpg.generate_uuid(),
		"reset": dpg.generate_uuid(),
		"cancel": dpg.generate_uuid(),
		"loading": dpg.generate_uuid(),
		"help_open": dpg.generate_uuid(),
		"help_close": dpg.generate_uuid(),
		"img_swe_main": dpg.generate_uuid(),
		"img_eng_main": dpg.generate_uuid(),
		"img_swe_welc": dpg.generate_uuid(),
		"img_swe_welc": dpg.generate_uuid(),
	},
	"combos": {
		"board_id": dpg.generate_uuid()
	},
	"text": {
		"title": dpg.generate_uuid(),
		"tagline": dpg.generate_uuid(),
		"enter_key": dpg.generate_uuid(),
		"copyright": dpg.generate_uuid(),
		"help": dpg.generate_uuid(),
		"loading": dpg.generate_uuid(),
		"title_game": dpg.generate_uuid(),
		'info_game': dpg.generate_uuid(),
		'p1_status': dpg.generate_uuid(),
		'p2_status': dpg.generate_uuid(),
	},
	"registry": {
		"enter_key": dpg.generate_uuid(),
		"game_key_binds": dpg.generate_uuid(),
	},
	"theme": {
		"disabled": dpg.generate_uuid(),
		'start_green': dpg.generate_uuid(),
		'stop_red': dpg.generate_uuid(),
	},
	"indicator": {
		"settings_loading": dpg.generate_uuid(),
	},
	"textures": {
		"spritesheet": dpg.generate_uuid(),
	},
	"images": {
		"p1_icon": dpg.generate_uuid(),
		"p2_icon": dpg.generate_uuid(),
	}, 
	"drawlist": dpg.generate_uuid(),
}

# All descriptive texts in the game, in swedish and english.
labels = {
	"start_btn": {
		"eng": "Start",
		"swe": "Starta",
	},
	"stop_btn": {
		"eng": "Stop",
		"swe": "Stopp",
	},
	"help_btn": {
		"eng": "Help",
		"swe": "Hj??lp",
	},
	"exit_btn": {
		"eng": "Exit",
		"swe": "Avsluta",
	},
	"settings_btn": {
		"eng": "Advanced Settings",
		"swe": "Avancerade Inst??llningar",
	},
	"p1_ts_title": {
		"eng": "Player 1 - Time Series",
		"swe": "Spelare 1 - Tidsserie",
	},
	"p2_ts_title": {
		"eng": "Player 2 - Time Series",
		"swe": "Spelare 2 - Tidsserie",
	},
	"ts_xax": {
		"eng": "Time (s)",
		"swe": "Tid (s)",
	},
	"ts_yax": {
		"eng": "Voltage (uV)",
		"swe": "Elektrisk Sp??nning (uV)",
	},
	"p1_br_title": {
		"eng": "Player 1 - Band Power",
		"swe": "Spelare 1 - Frekvensband",
	},
	"p2_br_title": {
		"eng": "Player 2 - Band Power",
		"swe": "Spelare 2 - Frekvensband",
	},
	"br_yax": {
		"eng": "Power (uV)^2/Hz",
		"swe": "Effekt (uV)^2/Hz",
	},
	"p1_me_title": {
		"eng": "Player 1 - Focus Metric",
		"swe": "Spelare 1 - Fokusm??ttal",
	},
	"p2_me_title": {
		"eng": "Player 2 - Focus Metric",
		"swe": "Spelare 2 - Fokusm??ttal",
	},
	"me_xax": {
		"eng": "Time (s)",
		"swe": "Tid (s)",
	},
	"me_yax": {
		"eng": "Metric value",
		"swe": "M??ttal",
	},
	"help_title": {
		"eng": "Help",
		"swe": "Hj??lp",
	},
	"help_close": {
		"eng": "Close",
		"swe": "St??ng",
	},
	"help_text": {
		"eng": "This is a help text",
		"swe": "Detta ??r en hj??lpsam text.",
	},
	"settings_title": {
		"eng": "Settings",
		"swe": "Inst??llningar",
	},
	"sett_boardid": {
		"eng": "Board ID",
		"swe": "Board ID",
	},
	"settings_ok": {
		"eng": "OK",
		"swe": "OK",
	},
	"settings_reset": {
		"eng": "Reset",
		"swe": "??terst??ll",
	},
	"settings_cancel": {
		"eng": "Cancel",
		"swe": "Avbryt",
	},
	"info_game": {
		"eng": "Short, fun and engaging tagline or description of the game, shorter than the help dialogue, but still useful.", 
		"swe": "F??rs??k att l??sa labyrinten med din kompis genom att blunda och slappna av!",
	},
	"loading_applying": {
		"eng": "Applying settings...",
		"swe": "Applicerar inst??llningar...",
	},
	"loading_success": {
		"eng": "Successfully applied settings.",
		"swe": "Inst??llningarna har applicerats.",
	},
	"loading_failure": {
		"eng": "Failure occured while applying settings.\nPlease check log for details.",
		"swe": "Fel uppstod under applicering av inst??llningarna.\nV??nligen kontrollera loggen f??r detaljer.",
	},
	"welcome_title": {
		"eng": "BrainGame Curiosum",
		"swe": "BrainGame Curiosum",
	},
	"welcome_tagline": {
		"eng": "This is a tagline",
		"swe": "Detta ??r en slogan",
	},
	"welcome_enter": {
		"eng": "Press ENTER to start",
		"swe": "Tryck ENTER f??r att starta",
	},
	"welcome_copyright": {
		"eng": "Copyright by Alfons Edbom Devall, Alfred Leimar, Elsa Magnusson, Elias Olofsson, Jacob Persson & Jennica Sandberg",
		"swe": "Copyright av Alfons Edbom Devall, Alfred Leimar, Elsa Magnusson, Elias Olofsson, Jacob Persson & Jennica Sandberg",
	},
	"status_paused": {
		"eng": "Stopped",
		"swe": "Stannad",
	},
	"status_wait": {
		"eng": "Running...",
		"swe": "K??r...",
	},
	"status_detected": {
		"eng": "Peak Detected!",
		"swe": "Topp detekterad!",
	},
	"status_left": {
		"eng": "Turning left...",
		"swe": "Roterar v??nster...",
	},
	"status_right": {
		"eng": "Turning right...",
		"swe": "Roterar h??ger...",
	},
	"status_forward": {
		"eng": "Turning forwards...",
		"swe": "Roterar fram??t...",
	},
	"status_backward": {
		"eng": "Turning backwards...",
		"swe": "Roterar bak??t...",
	},
}

