# gds_viewer without gdspy: the cell rule, the interactive window (layer list, pattern redraw after zoom) and the
# command line. Run from the repo root:   python -m pytest tests

import os
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import gdstk  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)

import gds_viewer  # noqa: E402


def layout():
    """$$$CONTEXT_INFO$$$ first and largest, a small device cell placed nowhere, and the design: Metal1 (pattern),
    TopMetal2 with a filler shape (hidden at first), a Metal1 boundary (outline only) and a text."""
    lib = gdstk.Library()
    lib.new_cell("$$$CONTEXT_INFO$$$").add(gdstk.rectangle((0, 0), (1000, 1000), layer=1))
    lib.new_cell("small_device").add(gdstk.rectangle((0, 0), (10, 10), layer=8))
    design = lib.new_cell("DESIGN")
    design.add(gdstk.rectangle((0, 0), (200, 100), layer=8),
               gdstk.rectangle((50, 20), (150, 80), layer=134),
               gdstk.rectangle((60, 30), (70, 40), layer=134, datatype=22),
               gdstk.rectangle((0, 40), (5, 60), layer=8, datatype=4),
               gdstk.Label("IN", (2, 50), layer=8, texttype=25))
    return lib


def test_pick_cell_takes_the_largest_design_cell():
    lib = layout()
    assert lib.top_level()[0].name != "DESIGN"
    assert gds_viewer.pick_cell(lib, None).name == "DESIGN"
    assert gds_viewer.pick_cell(lib, "small_device").name == "small_device"
    with pytest.raises(SystemExit):
        gds_viewer.pick_cell(lib, "missing")


def test_layer_label():
    assert gds_viewer.layer_label((8, 0)) == "Metal1.drawing 8/0"
    assert gds_viewer.layer_label((134, 22)) == "TopMetal2.filler 134/22"
    assert gds_viewer.layer_label((201, 0)) == "201/0"


def test_window_layers_and_pattern_redraw():
    window = gds_viewer.LayoutWindow(gds_viewer.pick_cell(layout(), None))
    window.fig.canvas.draw()
    metal1 = window.layers[(8, 0)]
    assert window.layers[(134, 22)]["visible"] is False          # filler purpose starts off
    assert window.layers[(134, 22)]["image"] is None
    assert window.layers[(8, 4)]["tile"] is None                  # boundary: outline only, no pattern
    assert any(a.get_text() == "IN" for a in window.layers[(8, 25)]["artists"])
    assert metal1["image"] is not None

    # zoomed in 20x: the pattern is redrawn over the view only, at screen resolution (not 20x coarser)
    full_width = metal1["image"].get_array().shape[1]
    window.ax.set_xlim(90, 100)
    window.ax.set_ylim(45, 55)
    window._redraw_patterns()
    image = metal1["image"]
    x0, x1, y0, y1 = image.get_extent()
    (vx0, vx1) = window.ax.get_xlim()                            # 90..100, widened to the window's shape
    assert x0 <= vx0 and x1 >= vx1 and x1 - x0 < (vx1 - vx0) + 1
    tile_h, tile_w = metal1["tile"].shape[:2]
    px_per_um = image.get_array().shape[1] / (x1 - x0)
    assert image.get_array().shape[1] < 2 * full_width
    assert abs(x0 * px_per_um / tile_w - round(x0 * px_per_um / tile_w)) < 1e-6      # anchored to the tile grid

    # the layer list switches a layer off and on, its pattern with it
    index = window._keys_in_list.index((8, 0))
    window.checks.set_active(index)
    assert metal1["visible"] is False and metal1["image"] is None
    assert not any(a.get_visible() for a in metal1["artists"])
    window.checks.set_active(index)
    assert metal1["visible"] is True and metal1["image"] is not None


def test_command_line_screenshot_without_gdspy(tmp_path):
    """The command line reads with gdstk: it runs with gdspy blocked."""
    gds = tmp_path / "multi.gds"
    layout().write_gds(str(gds))
    blocker = tmp_path / "blocker"
    blocker.mkdir()
    (blocker / "sitecustomize.py").write_text("import sys\nsys.modules['gdspy'] = None\n")
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(blocker), ROOT]), MPLBACKEND="Agg")
    png = tmp_path / "out.png"
    run = subprocess.run([sys.executable, os.path.join(ROOT, "gds_viewer.py"), str(gds), "--screenshot", str(png),
                          "--width", "400"], capture_output=True, text=True, env=env)
    assert run.returncode == 0, run.stderr
    assert "Displaying cell 'DESIGN'" in run.stdout
    assert png.stat().st_size > 0


def test_layers_without_style_do_not_hide_the_circuit(tmp_path):
    """A helper layer without SG13G2 style (here 800/0, a box over the circuit) is an outline, not a grey fill."""
    lib = layout()
    lib["DESIGN"].add(gdstk.rectangle((10, 10), (190, 90), layer=800))
    cell = gds_viewer.pick_cell(lib, None)
    window = gds_viewer.LayoutWindow(cell)
    patch = window.layers[(800, 0)]["artists"][0]
    assert patch.get_facecolor()[3] == 0 and patch.get_edgecolor()[3] > 0
    assert gds_viewer._layer_style((800, 0)) == (gds_viewer.DEFAULT_COLOR, "helper", None)
    assert gds_viewer._layer_style((800, 0), {800: "#ff0000"})[1] == "solid"

    # the screenshot: Metal1's pattern shows through in the middle of the box
    from matplotlib.image import imread
    png = tmp_path / "shot.png"
    gds_viewer.render_screenshot(cell, str(png), width_px=400)
    image = imread(str(png))
    h, w = image.shape[:2]
    middle = image[int(h * 0.15):int(h * 0.25), int(w * 0.05):int(w * 0.15), :3]     # Metal1 only, inside 800/0
    grey = np.array([0xa0, 0xa0, 0xa0]) / 255
    assert not np.all(np.abs(middle - grey).max(axis=2) < 0.02)


def test_zoom_box_of_another_shape_fills_the_drawing_area():
    """A tall zoom box in a wide window: the drawing area keeps its size (the shown range gets wider), and the
    patterns cover the whole shown range. Drawing again does not start another pattern redraw."""
    window = gds_viewer.LayoutWindow(gds_viewer.pick_cell(layout(), None))
    window.fig.canvas.draw()
    full_width = window.ax.get_window_extent().width
    window.ax.set_xlim(95, 105)
    window.ax.set_ylim(0, 100)
    window._redraw_patterns()
    window.fig.canvas.draw()
    assert abs(window.ax.get_window_extent().width - full_width) < 1
    (vx0, vx1), (vy0, vy1) = window.ax.get_xlim(), window.ax.get_ylim()
    assert vx1 - vx0 > 50                                      # widened to the window's shape
    x0, x1, y0, y1 = window.layers[(8, 0)]["image"].get_extent()
    assert x0 <= max(vx0, 0) + 1e-6 and x1 >= min(vx1, 200) - 1e-6   # Metal1 (0..200) patterned wherever shown

    starts = []
    window._timer.start = lambda: starts.append(1)
    window.fig.canvas.draw()
    window.fig.canvas.draw()
    assert starts == []
