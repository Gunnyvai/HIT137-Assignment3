# Spot the Difference — HIT137 Group Assignment 3

## How to Run

```bash
pip install -r requirements.txt
python app.py
```

Supports JPG, PNG, BMP images.

---

## Project Structure & Team Split

| File | Owner | Responsibility |
|------|-------|---------------|
| `difference_region.py` | Member 1 | Data model for a single difference region |
| `image_processor.py` | Member 1 | OpenCV image loading, cloning, and 5 alterations |
| `game_state.py` | Member 2 | `BaseGame` → `GameState` inheritance; click logic; scoring |
| `widgets.py` | Member 3 | All custom Tkinter widget classes |
| `app.py` | Member 4 | Root window, menu, event wiring, layout |

---

## OOP Requirements Met

| Requirement | Implementation |
|---|---|
| At least 3 classes | `DifferenceRegion`, `ImageProcessor`, `BaseGame`, `GameState`, `ImageCanvas`, `StatBar`, `GlowButton`, `MessageBar`, `SpotTheDifferenceApp` |
| Encapsulation | All internal state uses `_private` attributes with property accessors |
| Constructor (`__init__`) | Every class defines `__init__` |
| Methods | All classes expose focused public methods |
| Class interaction | `app.py` composes `ImageProcessor` + `GameState` + widget classes |
| Inheritance | `GameState` inherits from `BaseGame` |
| Polymorphism | `reset_round()` defined in `BaseGame`, overridden in `GameState` |

---

## Functional Requirements Met

| Requirement | Where |
|---|---|
| Load JPG / PNG / BMP | `app.py → _load_image()` via `filedialog` |
| Side-by-side display | `app.py → _build_panels()` |
| Only modified image is clickable | `ImageCanvas(clickable=True/False)` |
| Exactly 5 differences per image | `ImageProcessor._build_modified()` |
| Non-overlapping differences | `DifferenceRegion.overlaps()` check |
| Random position and type each load | `random.shuffle` + `random.randint` |
| At least 3 alteration types | 5 types: colour shift, brightness, hue rotate, blur, invert blend |
| All manipulation via OpenCV | `image_processor.py` uses only `cv2` and `numpy` |
| Remaining counter | `StatBar` — REMAINING card |
| Cumulative score | `GameState._cumulative_score` |
| Red circle on both images when found | `app.py → _draw_circle_both(region, RED)` |
| Win notification when all 5 found | `messagebox.showinfo` in `_on_canvas_click` |
| Mistake counter displayed | `MistakePips` widget |
| Max 3 mistakes → round locked | `GameState.register_click()` |
| Clear prompt when max mistakes reached | `messagebox.showwarning` |
| Reveal All button → blue circles | `app.py → _reveal_all()` |
| Load new image to restart | `_load_image()` calls `reset_round()` |
