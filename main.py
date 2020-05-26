import sys
from collections import deque
from time import sleep
import select

import turtle
import cwiid
import pyautogui as gui

from helpers import *

REFRESH_RATE = 0.01  # MAX


def main():
    # connecting
    print("Connecting, press 1 + 2 simultaneously...")

    do_try_again = True
    try:
        wm
    except:
        while do_try_again:
            try:
                wm = cwiid.Wiimote()
            except:
                sys.stdout.flush()
                sys.stdout.write(
                    "Connection failed, retrying... (press CTRL+C to quit)\n"
                )
            else:
                do_try_again = False

    # confirm connected
    print("Connected successfully.")
    confirm_connected(wm)

    # TODO: Add testing phase
    print("Enter testing phase? (y/N)")
    if sys.stdin.readline().rstrip() == "y":
        print("Starting testing phase, press any key to exit testing phase.")

        screen = turtle.getscreen()
        screen.setup(500, 500)
        screen.colormode(255)
        turt = turtle.Turtle()
        turt.ht()
        turt.speed("fastest")
        turt.up()

        mx, my = cwiid.IR_X_MAX, cwiid.IR_Y_MAX

        def getNormalizedIR():
            state = wm.state["ir_src"][0]
            if state:
                x, y = state["pos"]
                size = state["size"]
                x /= mx
                y /= my
                return x, y, size
            else:
                return None

        def circle(x, y, r=5, color=(0, 0, 0)):
            nonlocal turt
            x = x * 500 - 250
            y = y * 500 - 250
            turt.goto(x, y)
            turt.pd()
            turt.pencolor(*color)
            turt.circle(r)
            turt.pu()

        MAX_LEN = 10
        history = deque(maxlen=MAX_LEN)

        while 1:
            # if select.select([sys.stdin,], [], [], 0.0)[0]:
            #     break
            state = getNormalizedIR()
            if state:
                x, y, size = state
                circle(x, y, size)
                if len(history) >= MAX_LEN:
                    nx, ny, nsize = history.popleft()
                    circle(nx, ny, nsize, (255, 255, 255))
                history.append((x, y, size))
        screen.bye()

    # calibration
    print("Calibrating with the following points:")
    src = []
    locations = ["Bottom left: ", "Top left: ", "Top right: ", "Bottom right"]
    sys.stdout.write(locations[len(src)])
    while len(src) < 4:
        sleep(REFRESH_RATE)
        ir = getIR(wm, do_normalize=False)
        if ir:
            x, y, size = ir
            src.append((x, y))
            print(x, y)
            if len(src) < 4:
                sys.stdout.write(locations[len(src)])
            sleep(0.5)

    pt = source_to_projection(src, verbose=True)
    print("Done calibrating\n")

    THRESHOLD = 30
    last_click = THRESHOLD
    gui.PAUSE = 0
    pos = (0, 0)

    # TODO fix mouse
    while 1:
        sleep(REFRESH_RATE)
        ir = getIR(wm)
        if ir:
            x, y, size = ir  # if 0 <= x <= 1 and 0 <= y <= 1:
            tx, ty = pt([x, y])[0]
            if last_click <= THRESHOLD:
                gui.mouseDown()
            else:
                gui.mouseUp()
            move(tx, ty)
            last_click = 0
        else:
            if last_click <= THRESHOLD:
                gui.mouseDown()
            else:
                gui.mouseUp()
            last_click += 1
        sys.stdout.write("\r" + str(last_click <= THRESHOLD) + " ")


if __name__ == "__main__":
    main()
