import tkinter as tk

# ============================================================
# DISPLAY
# ============================================================

DISPLAY_COLS = 25
DISPLAY_ROWS = 11

ACTIVE_COLS = 23
ACTIVE_ROWS = 9

ACTIVE_START_COL = 1
ACTIVE_START_ROW = 1

PIXEL_SIZE = 20
PIXEL_GAP = 5

BG_COLOR = "black"
OFF_COLOR = "black"
GRID_COLOR = "#494848"

ON_COLOR = "#CEDC13"
DIM_COLOR = "#202020"
TITLE_COLOR = "#FFD000"

# ============================================================
# TIMING / COUNTS
# ============================================================

FLASH_ON_MS = 3000
FLASH_OFF_MS = 400
FLASH_REPEAT = 10

SWEEP_DELAY_MS = 200

COLUMN_LOOP_COUNT = 2
ROW_LOOP_COUNT = 2

COLUMN_WIDTH = 3   # light 2 columns at a time
ROW_HEIGHT = 3     # light 2 rows at a time

# ============================================================
# MAP (23 x 9)
# "1" = active LED position
# ============================================================

MAP_23x9 = [
    "01011111100111111111111",
    "11010011100100111100111",
    "01010111100101111101111",
    "01011111101111111111111",
    "01011111100111111111111",
    "01011111101111111111111",
    "01010111100101111101111",
    "01011011100110111110111",
    "11111111100111111111111",
]

# ============================================================

class LEDTestProgram:
    def __init__(self, root):
        self.root = root
        self.root.title("LED Test Program")
        self.stopped = False

        self.canvas = tk.Canvas(
            root,
            width=self.cells_to_px(DISPLAY_COLS),
            height=self.cells_to_px(DISPLAY_ROWS),
            bg=BG_COLOR,
            highlightthickness=0
        )
        self.canvas.pack()

        self.cells = {}
        self.build_grid()

        self.root.bind("<Escape>", self.stop_program)

        self.flash_cycle = 0
        self.flash_state_on = True

        self.col_loop = 0
        self.col_index = 0
        self.col_direction = 1   # 1 = left->right, -1 = right->left

        self.row_loop = 0
        self.row_index = 0
        self.row_direction = 1   # 1 = top->bottom, -1 = bottom->top

        self.start_flash_phase()

    # --------------------------------------------------------
    # BASIC
    # --------------------------------------------------------

    def stop_program(self, event=None):
        self.stopped = True
        self.root.destroy()

    def cells_to_px(self, cells):
        return cells * PIXEL_SIZE + max(0, cells - 1) * PIXEL_GAP

    def build_grid(self):
        for r in range(DISPLAY_ROWS):
            for c in range(DISPLAY_COLS):
                x = c * (PIXEL_SIZE + PIXEL_GAP)
                y = r * (PIXEL_SIZE + PIXEL_GAP)
    #--------------------------------------
    #rect = self.canvas.create_rectangle(
    #--------------------------------------
 
                rect = self.canvas.create_oval( 
                    x, y,
                    x + PIXEL_SIZE,
                    y + PIXEL_SIZE,
                    fill=OFF_COLOR,
                    outline=GRID_COLOR
                )
                self.cells[(r, c)] = rect

    def clear_all(self):
        for rect in self.cells.values():
            self.canvas.itemconfig(rect, fill=OFF_COLOR)

    def set_pixel(self, r, c, color=ON_COLOR):
        if (r, c) in self.cells:
            self.canvas.itemconfig(self.cells[(r, c)], fill=color)

    def draw_title(self, text):
        self.canvas.delete("title")
        self.canvas.create_text(
            self.cells_to_px(DISPLAY_COLS) // 2,
            8,
            text=text,
            fill=TITLE_COLOR,
            font=("Courier New", 12, "bold"),
            anchor="n",
            tags="title"
        )

    # --------------------------------------------------------
    # MAP HELPERS
    # --------------------------------------------------------

    def draw_full_map(self, color=ON_COLOR):
        for r, row_bits in enumerate(MAP_23x9):
            for c, bit in enumerate(row_bits):
                if bit == "1":
                    self.set_pixel(ACTIVE_START_ROW + r, ACTIVE_START_COL + c, color)

    def draw_full_dim_map(self):
        self.draw_full_map(DIM_COLOR)

    def draw_column_block(self, active_col_start, color=ON_COLOR):
        for c_offset in range(COLUMN_WIDTH):
            col = active_col_start + c_offset
            if 0 <= col < ACTIVE_COLS:
                for r, row_bits in enumerate(MAP_23x9):
                    if row_bits[col] == "1":
                        self.set_pixel(
                            ACTIVE_START_ROW + r,
                            ACTIVE_START_COL + col,
                            color
                        )

    def draw_row_block(self, active_row_start, color=ON_COLOR):
        for r_offset in range(ROW_HEIGHT):
            row = active_row_start + r_offset
            if 0 <= row < ACTIVE_ROWS:
                row_bits = MAP_23x9[row]
                for c, bit in enumerate(row_bits):
                    if bit == "1":
                        self.set_pixel(
                            ACTIVE_START_ROW + row,
                            ACTIVE_START_COL + c,
                            color
                        )

    # --------------------------------------------------------
    # PHASE 1: FLASH FULL ON / OFF
    # --------------------------------------------------------

    def start_flash_phase(self):
        self.flash_cycle = 0
        self.flash_state_on = True
        self.run_flash_phase()

    def run_flash_phase(self):
        if self.stopped:
            return

        if self.flash_cycle >= FLASH_REPEAT:
            self.start_column_phase()
            return

        self.clear_all()
        self.draw_title(f"FULL FLASH {self.flash_cycle + 1}/{FLASH_REPEAT}")

        if self.flash_state_on:
            self.draw_full_map(ON_COLOR)
            self.flash_state_on = False
            self.root.after(FLASH_ON_MS, self.run_flash_phase)
        else:
            self.flash_state_on = True
            self.flash_cycle += 1
            self.root.after(FLASH_OFF_MS, self.run_flash_phase)

    # --------------------------------------------------------
    # PHASE 2: COLUMN SWEEP
    # left->right, then right->left = 1 loop
    # --------------------------------------------------------

    def start_column_phase(self):
        self.col_loop = 0
        self.col_index = 0
        self.col_direction = 1
        self.run_column_phase()

    def run_column_phase(self):
        if self.stopped:
            return

        if self.col_loop >= COLUMN_LOOP_COUNT:
            self.start_row_phase()
            return

        self.clear_all()
        self.draw_full_dim_map()

        direction_text = "L -> R" if self.col_direction == 1 else "R -> L"
        self.draw_title(
            f"2-COLUMN {direction_text}  LOOP {self.col_loop + 1}/{COLUMN_LOOP_COUNT}"
        )

        self.draw_column_block(self.col_index, ON_COLOR)

        if self.col_direction == 1:
            if self.col_index < ACTIVE_COLS - COLUMN_WIDTH:
                self.col_index += 1
            else:
                self.col_direction = -1
                self.col_index = ACTIVE_COLS - COLUMN_WIDTH
        else:
            if self.col_index > 0:
                self.col_index -= 1
            else:
                self.col_direction = 1
                self.col_index = 0
                self.col_loop += 1

        self.root.after(SWEEP_DELAY_MS, self.run_column_phase)

    # --------------------------------------------------------
    # PHASE 3: ROW SWEEP
    # top->bottom, then bottom->top = 1 loop
    # --------------------------------------------------------

    def start_row_phase(self):
        self.row_loop = 0
        self.row_index = 0
        self.row_direction = 1
        self.run_row_phase()

    def run_row_phase(self):
        if self.stopped:
            return

        if self.row_loop >= ROW_LOOP_COUNT:
            self.finish_program()
            return

        self.clear_all()
        self.draw_full_dim_map()

        direction_text = "T -> B" if self.row_direction == 1 else "B -> T"
        self.draw_title(
            f"2-ROW {direction_text}  LOOP {self.row_loop + 1}/{ROW_LOOP_COUNT}"
        )

        self.draw_row_block(self.row_index, ON_COLOR)

        if self.row_direction == 1:
            if self.row_index < ACTIVE_ROWS - ROW_HEIGHT:
                self.row_index += 1
            else:
                self.row_direction = -1
                self.row_index = ACTIVE_ROWS - ROW_HEIGHT
        else:
            if self.row_index > 0:
                self.row_index -= 1
            else:
                self.row_direction = 1
                self.row_index = 0
                self.row_loop += 1

        self.root.after(SWEEP_DELAY_MS, self.run_row_phase)

    # --------------------------------------------------------
    # END
    # --------------------------------------------------------

    def finish_program(self):
        if self.stopped:
            return

        self.start_flash_phase()

# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry("+0+0")
    root.attributes("-topmost", True)
    root.configure(bg=BG_COLOR)
    root.resizable(False, False)

    app = LEDTestProgram(root)
    root.mainloop()
