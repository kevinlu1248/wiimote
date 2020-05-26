from time import sleep
import subprocess
from typing import List

import cwiid

import numpy as np
import pyautogui as gui
from skimage.transform import ProjectiveTransform

SCREENX, SCREENY = gui.size()
MX, MY = cwiid.IR_X_MAX, cwiid.IR_Y_MAX


def move(x: float, y: float) -> None:
    gui.moveTo(x * SCREENX, (1 - y) * SCREENY)


def get_battery(wm) -> float:
    return wm.state["battery"] / cwiid.BATTERY_MAX


def confirm_connected(wm) -> None:
    wm.led = 0
    for _ in range(2):
        wm.led = 15
        wm.rumble = 1
        sleep(0.2)
        wm.led = 0
        wm.rumble = 0
        sleep(0.2)
    wm.led = 9
    wm.rumble = 0
    wm.rpt_mode = cwiid.RPT_IR ^ cwiid.RPT_BTN
    print("Current battery: {}%".format(round(get_battery(wm) * 100)))


def source_to_projection(src: List, verbose: bool = False):
    # for point in src:
    # print(round(point[0],3), round(point[1], 3))
    src = np.asarray(src)  # bottom_left, top_left, top_right, bottom_right
    dst = np.asarray([[0, 0], [0, 1], [1, 1], [1, 0]])
    pt = ProjectiveTransform()
    pt.estimate(src, dst)
    return pt


def getIR(wm, do_normalize: bool = False):
    state = wm.state["ir_src"][0]
    if state:
        x, y = state["pos"]
        size = state["size"]
        if do_normalize:
            x /= MX
            y /= MY
        return x, y, size
    else:
        return None
