import sys
from time import sleep, time
import threading
from collections import deque

import io
from contextlib import redirect_stdout

import kivy

kivy.require("1.11.1")
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.properties import StringProperty

import cwiid
import turtle
import pyautogui as gui

from helpers import *

gui.PAUSE = 0


# TODO: Add disabled buttons
# TODO: Kill some threads
# TOD: On off button


def thread(func):
    def decorated(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.start()
        return t

    return decorated


class WiimoteUI(GridLayout):
    instruct = StringProperty()
    status = StringProperty()
    connection = StringProperty()
    battery = StringProperty()
    screen = None
    calibrationPoints = []  # add typing
    CAL_LABELS = ["bottom left", "top left", "top right", "bottom right"]
    REFRESH_RATE = 0.01
    THRESHOLD = 30
    bluetoothExists = True
    pt = None
    wm = None

    def __init__(self, **kwargs):
        super(WiimoteUI, self).__init__(**kwargs)

        @thread
        def unthreaded():
            self.instruct = "Lets connect your Wiimote"
            self.status = "Status: connecting..."
            self.connection = "Connection: Not connected"
            self.battery = "Battery: ?%"
            t = self.connect()
            t.join()
            # if WiimoteUI.bluetoothExists:
            #     self.calibrate()

        unthreaded()

    def updateThreshold(self, text):
        WiimoteUI.THRESHOLD = int(text)

    @thread
    def connect(self):
        self.instruct = "Connecting to Wiimote, please press 1 + 2..."
        if not self.wm:
            attempt_number = 1
            while attempt_number:
                try:
                    start = time()
                    self.wm = cwiid.Wiimote()
                except Exception:
                    if time() - start < 1:
                        # Bluetooth error is faster, no other way to check
                        WiimoteUI.bluetoothExists = False
                        self.instruct = "Please install Bluetooth or turn it on."
                        return
                    attempt_number += 1
                    if attempt_number > 2:
                        self.instruct = "Connection failed, retrying with attempt #{}... (continue to press 1 + 2)".format(
                            attempt_number
                        )
                else:
                    attempt_number = 0
        self.instruct = "Connected successfully!"
        self.status = "Status: uncalibrated"
        self.connection = "Connection: connected"
        confirm_connected(self.wm)
        self.battery = "Battery: {}%".format(round(get_battery(self.wm) * 100))

    @thread
    def disconnect(self):
        self.instruct = "Disconnecting..."

        # confirmation
        self.wm.rumble = 1
        sleep(0.5)
        self.wm.rumble = 0
        del self.wm
        self.wm = None
        self.instruct = "Disconnected"
        self.status = "Status: disconnected from Wiimote"
        self.connection = "Status: disconnected"
        self.battery = "Battery: ?%"

    @thread
    def testIR(self):
        # TODO: Convert to Kivy

        self.instruct = "Try to align the edges of the camera close to the screen."
        self.status = "Testing camera"

        # btn1 = kb.Button(text='Hello World 1')
        # btn1.bind(on_press=self.callback)
        # self.add_widget(btn1)

        selfscreen = turtle.getscreen()
        selfscreen.setup(500, 500)
        selfscreen.colormode(255)
        turt = turtle.Turtle()
        turt.ht()
        turt.speed("fastest")
        turt.up()
        mx, my = cwiid.IR_X_MAX, cwiid.IR_Y_MAX

        def getNormalizedIR(wm):
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
            state = getNormalizedIR(self.wm)
            if state:
                x, y, size = state
                circle(x, y, size)
                if len(history) >= MAX_LEN:
                    nx, ny, nsize = history.popleft()
                    circle(nx, ny, nsize, (255, 255, 255))
                history.append((x, y, size))
        self.screen.bye()

    @thread
    def stopTesting(self):
        self.screen.bye()

    def getCalibrationPoint(self):
        while True:
            sleep(WiimoteUI.REFRESH_RATE)
            ir = getIR(self.wm, do_normalize=False)
            if ir:
                x, y, size = ir
                return x, y

    @thread
    def calibrate(self):
        self.status = "Status: calibrating..."
        i = 0
        while i < 4:
            self.instruct = "Click the {} corner of the screen with your IR pen.".format(
                WiimoteUI.CAL_LABELS[i]
            )
            x, y = self.getCalibrationPoint()
            if x and y:
                self.calibrationPoints.append((x, y))
                i += 1
                sleep(0.5)
        self.instruct = "Calculating projection..."
        self.pt = source_to_projection(self.calibrationPoints)
        self.instruct = "Your IR pen is ready to be used as a mouse."
        self.status = "Status: ready"

        last_click = WiimoteUI.THRESHOLD

        while True:
            sleep(WiimoteUI.REFRESH_RATE)
            ir = getIR(self.wm)
            if ir:
                x, y, size = ir  # if 0 <= x <= 1 and 0 <= y <= 1:
                tx, ty = self.pt([x, y])[0]
                if last_click <= WiimoteUI.THRESHOLD:
                    gui.mouseDown()
                else:
                    gui.mouseUp()
                move(tx, ty)
                last_click = 0
            else:
                if last_click <= WiimoteUI.THRESHOLD:
                    gui.mouseDown()
                else:
                    gui.mouseUp()
                last_click += 1
            sys.stdout.write("\r" + str(last_click <= WiimoteUI.THRESHOLD) + " ")


class WiimoteApp(App):
    def build(self):
        return WiimoteUI()


if __name__ == "__main__":
    WiimoteApp().run()
