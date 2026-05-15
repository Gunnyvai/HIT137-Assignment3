"""
app.py

Group member: Ramesh Acharya
"""

import tkinter as tk
from tkinter import filedialog, messagebox

from image_processor import ImageProcessor
from game_state       import GameState
from widgets          import (
    # Colour palette constants (imported for use in this file)
    WHITE, GRAY_50, GRAY_100, GRAY_200, GRAY_400, GRAY_600, GRAY_900,
    TEAL_500, TEAL_50, RED_500, BLUE_500,
    # Font constants
    FONT_DISPLAY, FONT_SUBTITLE, FONT_HEADING, FONT_BODY, FONT_MSG,
    # Widget classes
    PrimaryButton, GhostButton, StatBar, ImageCanvas, MessageBar,
)

ROUND_SECONDS = 120     # Each round lasts 2 minutes (120 seconds)


class SpotTheDifferenceApp:
    """
    Main application class that owns the window, menu, layout, timer,
    and all event handlers.

    Delegates image processing to ImageProcessor and game logic to GameState.
    Demonstrates class interaction: this class composes and coordinates
    all other classes in the project.
    """

    WIN_W = 1220    # Fixed window width in pixels
    WIN_H = 760     # Fixed window height in pixels

    def __init__(self, root: tk.Tk):
        """
        Initialise the application.

        Creates the ImageProcessor and GameState objects, then builds
        the complete UI. Coordinates are tracked (scale, offsets) to
        map canvas clicks back to image-space positions.

        Parameters:
            root -- the Tkinter root window passed in from main()
        """
        self._root      = root
        self._processor = ImageProcessor()   # Handles all OpenCV operations
        self._state     = GameState()        # Tracks score, mistakes, and state
        self._scale     = 1.0               # Scale factor: image -> display
        self._off_x     = 0                 # X offset: image centred in canvas
        self._off_y     = 0                 # Y offset: image centred in canvas
        self._setup_window()
        self._build_menu()
        self._build_ui()

    # ── Window setup ──────────────────────────────────────────────────

    def _setup_window(self) -> None:
        """
        Configure the root window: title, background, fixed size, and
        centred position on the screen.
        """
        self._root.title("Spot the Difference")
        self._root.configure(bg=GRAY_50)
        self._root.resizable(False, False)
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x  = (sw - self.WIN_W) // 2
        y  = (sh - self.WIN_H) // 2
        self._root.geometry(f"{self.WIN_W}x{self.WIN_H}+{x}+{y}")

    # ── Menu bar ──────────────────────────────────────────────────────

    def _build_menu(self) -> None:
        """
        Build the top menu bar with Game and Help menus.

        Game menu: Load Image, Reveal All, Exit
        Help menu: How to Play, About
        """
        menu_bar = tk.Menu(self._root, bg=WHITE, fg=GRAY_900,
                           activebackground=TEAL_50,
                           activeforeground=TEAL_500,
                           relief="flat", bd=0)

        game_menu = tk.Menu(menu_bar, tearoff=0,
                            bg=WHITE, fg=GRAY_900,
                            activebackground=TEAL_50,
                            activeforeground=TEAL_500)
        game_menu.add_command(label="Load Image",  command=self._load_image)
        game_menu.add_command(label="Reveal All",  command=self._reveal_all)
        game_menu.add_separator()
        game_menu.add_command(label="Exit",        command=self._root.quit)
        menu_bar.add_cascade(label="Game", menu=game_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0,
                            bg=WHITE, fg=GRAY_900,
                            activebackground=TEAL_50,
                            activeforeground=TEAL_500)
        help_menu.add_command(label="How to Play", command=self._show_help)
        help_menu.add_command(label="About",       command=self._show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self._root.config(menu=menu_bar)

    # ── UI layout ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """
        Build all UI sections in order from top to bottom:
          1. Top bar (title + action buttons)
          2. Stats row (score, remaining, mistakes, timer)
          3. Image panels (original left, modified right)
          4. Message bar (status text at the bottom)
        """
        self._build_topbar()
        self._build_stats()
        self._build_panels()
        self._build_messagebar()

    def _build_topbar(self) -> None:
        """
        Build the top bar containing the app title, subtitle,
        and the Reveal All + Load Image buttons on the right.
        """
        bar = tk.Frame(self._root, bg=WHITE,
                       highlightthickness=1,
                       highlightbackground=GRAY_200)
        bar.pack(fill="x")

        # Left side: brand with coloured accent bar
        brand = tk.Frame(bar, bg=WHITE)
        brand.pack(side="left", padx=24, pady=14)
        tk.Frame(brand, bg=TEAL_500, width=4, height=32).pack(
            side="left", fill="y", padx=(0, 12))

        title_text = tk.Frame(brand, bg=WHITE)
        title_text.pack(side="left")
        tk.Label(title_text, text="Spot the Difference",
                 bg=WHITE, fg=GRAY_900, font=FONT_DISPLAY).pack(anchor="w")
        tk.Label(title_text,
                 text="Find all 5 hidden changes  ·  "
                      "Max 3 mistakes  ·  2 minutes per round",
                 bg=WHITE, fg=GRAY_400, font=FONT_SUBTITLE).pack(anchor="w")

        # Right side: action buttons
        btns = tk.Frame(bar, bg=WHITE)
        btns.pack(side="right", padx=24, pady=14)
        GhostButton(btns, text="Reveal All",
                    command=self._reveal_all,
                    colour=GRAY_400).pack(side="left", padx=(0, 8))
        PrimaryButton(btns, text="Load Image",
                      command=self._load_image).pack(side="left")

    def _build_stats(self) -> None:
        """
        Build the stats row below the top bar.
        Creates a StatBar (Score, Remaining, Found, Mistakes, Timer)
        and stores a direct reference to the timer for start/stop control.
        """
        tk.Frame(self._root, bg=GRAY_200, height=1).pack(fill="x")
        wrapper = tk.Frame(self._root, bg=GRAY_50)
        wrapper.pack(fill="x", padx=24, pady=14)
        self._stat_bar = StatBar(wrapper)
        self._stat_bar.pack(side="left")
        # Direct reference so _load_image and _on_canvas_click can control it
        self._timer = self._stat_bar.timer

    def _build_panels(self) -> None:
        """
        Build the two side-by-side image panels.
        - Left panel: Original Image (non-clickable, reference only)
        - Right panel: Modified Image (clickable, player interacts here)
        A vertical divider separates the two panels.
        """
        tk.Frame(self._root, bg=GRAY_200, height=1).pack(fill="x")
        panels_outer = tk.Frame(self._root, bg=GRAY_50)
        panels_outer.pack(fill="both", expand=True, padx=24, pady=14)

        self._orig_panel = ImageCanvas(
            panels_outer, title="Original Image",
            accent=GRAY_400, clickable=False)
        self._orig_panel.pack(side="left")

        # Thin vertical divider between the two panels
        tk.Frame(panels_outer, bg=GRAY_200,
                 width=1).pack(side="left", fill="y", padx=16)

        self._mod_panel = ImageCanvas(
            panels_outer, title="Modified Image",
            accent=TEAL_500, clickable=True,
            click_callback=self._on_canvas_click)
        self._mod_panel.pack(side="left")

    def _build_messagebar(self) -> None:
        """
        Build the bottom status message bar.
        Pinned to the bottom of the window via side="bottom".
        """
        self._msg_bar = MessageBar(self._root)
        self._msg_bar.pack(fill="x", side="bottom")

    # ── Image loading ─────────────────────────────────────────────────

    def _load_image(self) -> None:
        """
        Open a file picker dialog, load the chosen image, reset game state,
        and start the 2-minute countdown timer.

        Steps:
          1. Show file dialog filtered to image formats
          2. Call ImageProcessor.load() — returns False if file is unreadable
          3. Attach the processor to GameState (resets per-round state)
          4. Refresh both canvases with the new image pair
          5. Refresh stat displays
          6. Start the countdown timer with on_expire callback
        """
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("All files",   "*.*"),
            ],
        )
        if not path:
            return   # User cancelled the dialog

        if not self._processor.load(path):
            messagebox.showerror(
                "Cannot Open Image",
                "The selected file could not be opened.\n"
                "Please choose a JPG, PNG, or BMP image.",
            )
            return

        self._state.attach_processor(self._processor)
        self._refresh_canvases()
        self._refresh_stats()

        # Start the 2-minute countdown; auto-reveal fires on expiry
        self._timer.start(
            seconds   = ROUND_SECONDS,
            on_expire = self._on_timer_expired,
        )
        self._msg("Image loaded — you have 2 minutes.  "
                  "Click the Modified panel to find differences.")

    # ── Timer expiry callback ─────────────────────────────────────────

    def _on_timer_expired(self) -> None:
        """
        Called automatically by TimerWidget when the countdown reaches zero.

        Auto-reveals all remaining unfound differences in blue on both panels,
        then shows an informational dialog telling the player how many they found.
        Does nothing if the round is already over (all found or already revealed).
        """
        if not self._state.loaded or self._state.revealed:
            return

        # Reveal and mark all unfound regions in blue
        self._state.reveal_all()
        for region in self._state.regions:
            if not region.found:
                self._draw_circle_both(region, BLUE_500)

        self._refresh_stats()
        self._msg(
            f"Time's up!  Found {self._state.found_count} / 5.  "
            "Load a new image to play again.")

        messagebox.showinfo(
            "Time's Up!",
            f"The 2-minute timer has expired.\n\n"
            f"You found  {self._state.found_count} / 5  differences.\n"
            f"The remaining differences are shown in blue.\n\n"
            "Load a new image to start a fresh round.",
        )

    # ── Canvas click handler ──────────────────────────────────────────

    def _on_canvas_click(self, canvas_x: int, canvas_y: int) -> None:
        """
        Handle a click on the Modified Image canvas.

        Steps:
          1. Convert canvas coordinates to original image coordinates
          2. Pass to GameState.register_click() for hit/miss evaluation
          3. If hit: draw red circle on both panels, check for round complete
          4. If miss: update stats, check for lockout (3 mistakes)
          5. Update stat display and status message accordingly

        Parameters:
            canvas_x, canvas_y -- pixel coordinates of the click on the canvas
        """
        if not self._state.loaded:
            return

        dw = ImageCanvas.DISPLAY_W
        dh = ImageCanvas.DISPLAY_H

        # Convert from canvas space to original image space
        img_x, img_y = self._processor.canvas_to_image(
            canvas_x, canvas_y, dw, dh)

        result = self._state.register_click(img_x, img_y)

        if result["hit"]:
            # Correct click — draw red circle and check for completion
            self._draw_circle_both(result["region"], RED_500)
            self._refresh_stats()

            if result["all_found"]:
                self._timer.stop()   # Stop timer — player won before time ran out
                self._msg(
                    f"All 5 differences found!  "
                    f"Total score: {self._state.cumulative_score}")
                messagebox.showinfo(
                    "Well done!",
                    f"You found all 5 differences!\n\n"
                    f"Cumulative score: {self._state.cumulative_score}\n\n"
                    "Load a new image to keep playing.",
                )
            else:
                self._msg(
                    f"Correct!  "
                    f"{self._state.remaining_count} difference(s) remaining.")

        elif result["mistake"]:
            # Wrong click — update stats and check for lockout
            self._refresh_stats()
            if result["locked"]:
                self._timer.stop()   # Stop timer — round over due to mistakes
                self._msg(
                    f"3 mistakes reached — round over.  "
                    f"You found {self._state.found_count} / 5.")
                messagebox.showwarning(
                    "Round Over",
                    f"You made 3 mistakes.\n"
                    f"Differences found: {self._state.found_count} / 5\n\n"
                    "Load a new image to try again, "
                    "or press Reveal All to see the answers.",
                )
            else:
                left = self._state.MAX_MISTAKES - self._state.mistakes
                self._msg(f"Not quite.  {left} mistake(s) remaining.")
        else:
            # Click blocked (round already over)
            self._msg("Round over — load a new image to play again.")

    # ── Manual reveal ─────────────────────────────────────────────────

    def _reveal_all(self) -> None:
        """
        Reveal all unfound differences in blue when the player presses
        the Reveal All button (or selects it from the Game menu).

        Stops the timer, calls GameState.reveal_all() to lock the round,
        then draws blue circles over all unfound regions on both panels.
        Does nothing if no image is loaded or if already revealed.
        """
        if not self._state.loaded or self._state.revealed:
            return

        self._timer.stop()
        self._state.reveal_all()

        for region in self._state.regions:
            if not region.found:
                self._draw_circle_both(region, BLUE_500)

        self._refresh_stats()
        self._msg(
            "Differences revealed in blue.  "
            "Load a new image to start a new round.")

    # ── Helper methods ────────────────────────────────────────────────

    def _refresh_canvases(self) -> None:
        """
        Display the newly loaded image pair on both panels.

        Retrieves the scale and offset values so that circle coordinates
        can be mapped correctly from image space to canvas space.
        Re-draws any circles that were already found (e.g. when refreshing).
        """
        dw = ImageCanvas.DISPLAY_W
        dh = ImageCanvas.DISPLAY_H
        orig_rgb, mod_rgb = self._processor.display_pair(dw, dh)

        # Store scale/offset for use in _draw_circle_both
        self._scale, self._off_x, self._off_y = \
            self._processor.scale_info(dw, dh)

        self._orig_panel.reset()
        self._mod_panel.reset()
        self._orig_panel.show_image(orig_rgb)
        self._mod_panel.show_image(mod_rgb)

        # Re-draw any already-found circles (e.g. after a reload)
        for region in self._state.regions:
            if region.found:
                self._draw_circle_both(region, RED_500)

    def _draw_circle_both(self, region, colour: str) -> None:
        """
        Draw an indicator circle over a difference region on both panels.

        Converts the region's centre from image coordinates to canvas
        coordinates using the stored scale and offset, then calls
        add_circle() on both the original and modified panels.

        Parameters:
            region -- DifferenceRegion whose centre determines circle position
            colour -- RED_500 for found, BLUE_500 for revealed
        """
        icx, icy = region.center
        ccx = int(icx * self._scale) + self._off_x   # Canvas X
        ccy = int(icy * self._scale) + self._off_y   # Canvas Y
        cr  = int(region.radius * self._scale)        # Canvas radius
        self._orig_panel.add_circle(ccx, ccy, cr, colour)
        self._mod_panel.add_circle(ccx, ccy, cr, colour)

    def _refresh_stats(self) -> None:
        """
        Push current game values to the StatBar for display.
        Called after every click and after loading a new image.
        """
        self._stat_bar.update(
            score     = self._state.cumulative_score,
            remaining = self._state.remaining_count,
            found     = self._state.found_count,
            mistakes  = self._state.mistakes,
        )

    def _msg(self, text: str) -> None:
        """
        Update the bottom message bar with a status string.
        Wrapper around MessageBar.set() to keep call sites concise.
        """
        self._msg_bar.set(text)

    # ── Help dialogs ──────────────────────────────────────────────────

    def _show_help(self) -> None:
        """
        Display the How to Play instructions dialog.
        Explains image loading, clicking, mistakes, timer, and reveal.
        """
        messagebox.showinfo(
            "How to Play",
            "1.  Click  Load Image  and choose any JPG, PNG, or BMP file.\n\n"
            "2.  Two images appear side by side.\n"
            "    The Modified image (right) contains 5 hidden differences.\n\n"
            "3.  Click on the Modified image where you spot a difference.\n"
            "    A red circle marks correct finds on both images.\n\n"
            "4.  You have 3 mistakes and 2 minutes per round.\n"
            "    The timer turns amber below 30 s and red below 10 s.\n"
            "    Remaining differences are revealed automatically when\n"
            "    the timer expires.\n\n"
            "5.  Find all 5 before time runs out to win!\n\n"
            "6.  Press  Reveal All  to show answers at any time.",
        )

    def _show_about(self) -> None:
        """Display the About dialog with project and team information."""
        messagebox.showinfo(
            "About",
            "Spot the Difference\n"
            "HIT137  ·  Group Assignment 3\n\n"
            "Built with Python · Tkinter · OpenCV",
        )


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """
    Application entry point.
    Creates the Tkinter root window, instantiates the app, and starts
    the main event loop. All logic runs inside SpotTheDifferenceApp.
    """
    root = tk.Tk()
    SpotTheDifferenceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()