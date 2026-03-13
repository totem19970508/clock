import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
import time
import requests
import threading

# ============================================================
# DISPLAY GEOMETRY
# ============================================================

DISPLAY_COLS = 25
DISPLAY_ROWS = 11
GLYPH_ROWS = 9

LEFT_BORDER_COLS = 1
RIGHT_BORDER_COLS = 1
TOP_BORDER_ROWS = 1
BOTTOM_BORDER_ROWS = 1
CREDIT_COLOR = "#FFD000"

# slot widths: D1, D2, colon, D3, D4
SLOT_WIDTHS = [3, 6, 2, 6, 6]

# ============================================================
# GLYPHS
# ============================================================

GLYPHS_6 = {
    "0": [
        "011110", "100001", "100001", "100001", "100001",
        "100001", "100001", "100001", "011110"
    ],
    "1": [
        "000010", "000110", "000010", "000010", "000010",
        "000010", "000010", "000010", "000111"
    ],
    "2": [
        "011110", "100001", "000001", "000001", "001110",
        "010000", "100000", "100000", "111111"
    ],
    "3": [
        "011110", "100001", "000001", "000001", "011110",
        "000001", "000001", "100001", "011110"
    ],
    "4": [
        "000010", "000110", "001010", "010010", "100010",
        "111111", "000010", "000010", "000010"
    ],
    "5": [
        "111111", "100000", "100000", "111110", "000001",
        "000001", "000001", "000001", "111110"
    ],
    "6": [
        "011110", "100001", "100000", "100000", "111110",
        "100001", "100001", "100001", "011110"
    ],
    "7": [
        "111111", "000001", "000001", "000010", "000100",
        "001000", "001000", "010000", "010000"
    ],
    "8": [
        "011110", "100001", "100001", "100001", "011110",
        "100001", "100001", "100001", "011110"
    ],
    "9": [
        "011110", "100001", "100001", "100001", "011111",
        "000001", "000001", "100001", "011110"
    ],
    "°": [
        "011000", "100100", "100100", "011000", "000000",
        "000000", "000000", "000000", "000000"
    ],
    " ": [
        "000000", "000000", "000000", "000000", "000000",
        "000000", "000000", "000000", "000000"
    ]
}

GLYPHS_3 = {
    "1": [
        "010", "110", "010", "010", "010",
        "010", "010", "010", "111"
    ],
    " ": [
        "000", "000", "000", "000", "000",
        "000", "000", "000", "000"
    ]
}

GLYPHS_2 = {
    ":": [
        "00",
        "00",
        "00",
        "01",
        "00",
        "01",
        "00",
        "00",
        "00",
    ],
    " ": [
        "00", "00", "00", "00", "00",
        "00", "00", "00", "00"
    ]
}

# ============================================================
# SETTINGS
# ============================================================

PIXEL_SIZE = 24
PIXEL_GAP = 1

ON_COLOR = "white"
OFF_COLOR = "black"
GRID_COLOR = "#D45134"
BG_COLOR = "black"

USE_24H = False

TIME_SHOW_SECONDS = 5
TEMP_SHOW_SECONDS = 5

REFRESH_MS = 200

WEATHER_URL = "https://api.weather.gov/stations/KMIA/observations/latest"
INITIAL_TEMP_F = 75
WEATHER_REFRESH_SECONDS = 30

CREDIT_TEXT = "Eddie C - CLearLED ® "


def c_to_f(temp_c):
    return int(round(temp_c * 9 / 5 + 32))


class BitmapClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Clock + Temperature")

        # Temperature state
        self.last_temp_f = INITIAL_TEMP_F         # startup fallback
        self.has_valid_temp = False               # becomes True after first good read
        self.connection_ok = False                # latest fetch status
        self.last_weather_check = 0.0
        self.weather_fetch_in_progress = False

        self.credit_font = tkfont.Font(family="Courier New", size=10, weight="bold")

        self.canvas = tk.Canvas(
            root,
            width=self.get_display_width_px(),
            height=self.get_display_height_px(),
            bg=BG_COLOR,
            highlightthickness=0
        )
        self.canvas.pack()

        self.cycle_start = time.monotonic()

        # Start with a background weather fetch so UI never blocks
        self.start_weather_fetch(force=True)
        self.update_display()

    # --------------------------------------------------------
    # SIZE
    # --------------------------------------------------------

    def cells_to_px(self, cells):
        return cells * PIXEL_SIZE + max(0, cells - 1) * PIXEL_GAP

    def get_display_width_px(self):
        return self.cells_to_px(DISPLAY_COLS)

    def get_display_height_px(self):
        return self.cells_to_px(DISPLAY_ROWS)

    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    def start_weather_fetch(self, force=False):
        now_mono = time.monotonic()

        if self.weather_fetch_in_progress:
            return

        if not force and (now_mono - self.last_weather_check) < WEATHER_REFRESH_SECONDS:
            return

        self.last_weather_check = now_mono
        self.weather_fetch_in_progress = True

        thread = threading.Thread(target=self._weather_worker, daemon=True)
        thread.start()

    def _weather_worker(self):
        try:
            r = requests.get(WEATHER_URL, timeout=3)
            r.raise_for_status()
            data = r.json()

            temp_c = data["properties"]["temperature"]["value"]

            if temp_c is None:
                self.root.after(0, self._weather_failed)
                return

            new_temp_f = c_to_f(temp_c)
            self.root.after(0, lambda: self._weather_success(new_temp_f))

        except Exception:
            self.root.after(0, self._weather_failed)

    def _weather_success(self, new_temp_f):
        self.last_temp_f = new_temp_f
        self.has_valid_temp = True
        self.connection_ok = True
        self.weather_fetch_in_progress = False

    def _weather_failed(self):
        # Important logic:
        # - before first valid read, last_temp_f stays at INITIAL_TEMP_F (75)
        # - after first valid read, last_temp_f stays at the last good value
        self.connection_ok = False
        self.weather_fetch_in_progress = False

    # --------------------------------------------------------
    # LAYOUT
    # --------------------------------------------------------

    def layout_cell_positions(self):
        x1 = LEFT_BORDER_COLS
        x2 = x1 + SLOT_WIDTHS[0]
        xc = x2 + SLOT_WIDTHS[1]
        x3 = xc + SLOT_WIDTHS[2]
        x4 = x3 + SLOT_WIDTHS[3]
        y = TOP_BORDER_ROWS
        return x1, x2, xc, x3, x4, y

    # --------------------------------------------------------
    # DRAWING
    # --------------------------------------------------------

    def clear(self):
        self.canvas.delete("all")

    def draw_bitmap(self, cell_x, cell_y, bitmap, visible=True):
        rows = len(bitmap)
        cols = len(bitmap[0])

        for r in range(rows):
            for c in range(cols):
                bit_on = (bitmap[r][c] == "1") and visible

                x = (cell_x + c) * (PIXEL_SIZE + PIXEL_GAP)
                y = (cell_y + r) * (PIXEL_SIZE + PIXEL_GAP)

                self.canvas.create_rectangle(
                    x,
                    y,
                    x + PIXEL_SIZE,
                    y + PIXEL_SIZE,
                    fill=ON_COLOR if bit_on else OFF_COLOR,
                    outline=GRID_COLOR
                )

    def draw_slot1(self, x, y, ch):
        self.draw_bitmap(x, y, GLYPHS_3[ch])

    def draw_slot6(self, x, y, ch):
        self.draw_bitmap(x, y, GLYPHS_6[ch])

    def draw_colon(self, x, y, visible=True):
        self.draw_bitmap(x, y, GLYPHS_2[":"], visible)

    def draw_credit(self):
        text_width = self.credit_font.measure(CREDIT_TEXT)
        x_location = self.get_display_width_px() - text_width - 6
        y_location = self.get_display_height_px() - 6

        self.canvas.create_text(
            x_location,
            y_location,
            text=CREDIT_TEXT,
            fill=CREDIT_COLOR,
            font=self.credit_font,
            anchor="sw"
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def colon_visible(self, second):
        # Match your original behavior:
        # - connected: colon solid ON
        # - disconnected: blink every second
        if self.connection_ok:
            return True
        return second % 2 == 0

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    def draw_time(self):
        now = datetime.now()
        text = now.strftime("%H:%M" if USE_24H else "%I:%M")

        if text[0] == "0":
            text = " " + text[1:]

        d1, d2, _, d3, d4 = text

        x1, x2, xc, x3, x4, y = self.layout_cell_positions()

        self.draw_slot1(x1, y, d1)
        self.draw_slot6(x2, y, d2)
        self.draw_colon(xc, y, self.colon_visible(now.second))
        self.draw_slot6(x3, y, d3)
        self.draw_slot6(x4, y, d4)

    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    def draw_temperature(self):
        temp = max(0, min(199, self.last_temp_f))

        x1, x2, xc, x3, x4, y = self.layout_cell_positions()

        if temp < 100:
            t = f"{temp:02d}"
            self.draw_slot1(x1, y, " ")
            self.draw_slot6(x2, y, t[0])
            self.draw_colon(xc, y, False)
            self.draw_slot6(x3, y, t[1])
            self.draw_slot6(x4, y, "°")
        else:
            t = f"{temp:03d}"
            self.draw_slot1(x1, y, t[0])
            self.draw_slot6(x2, y, t[1])
            self.draw_colon(xc, y, False)
            self.draw_slot6(x3, y, t[2])
            self.draw_slot6(x4, y, "°")

    # --------------------------------------------------------
    # MODE
    # --------------------------------------------------------

    def mode(self):
        cycle = TIME_SHOW_SECONDS + TEMP_SHOW_SECONDS
        elapsed = (time.monotonic() - self.cycle_start) % cycle
        if elapsed < TIME_SHOW_SECONDS:
            return "time"
        return "temp"

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    def update_display(self):
        # Non-blocking weather refresh
        self.start_weather_fetch()

        self.clear()

        if self.mode() == "time":
            self.draw_time()
        else:
            self.draw_temperature()

        self.draw_credit()

        self.root.after(REFRESH_MS, self.update_display)


# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry("+0+0")
    root.attributes("-topmost", True)
    root.configure(bg=BG_COLOR)
    root.resizable(False, False)

    def close_app(event=None):
        root.destroy()

    root.bind("<Escape>", close_app)

    app = BitmapClock(root)
    root.mainloop()
