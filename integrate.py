"""
Alarm System Integration Project

Devices:
stepper motor
photosensor
infra red sensor
buzzer

Objective:
When the light sensor detects an a specific light level it activates the curtain and buzzer functions.
If not already opened, a stepper is instructed to draw open a curtain to let the light in while a buzzer begins to beep.
If the user hovers or places their hand above the alarm, it is interpreted as a shutoff signal to the buzzer.
"""
import smbus
import time
import RPi.GPIO as GPIO
import sys
import select
from threading import Thread, Event

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

A0 = 0x40
A2 = 0x42
buzzer = 25
delay = 1
address = 0x48
distCutoff = 125
global hand_distance

stepper_pins = [12, 16, 20, 21]
GPIO.setup(stepper_pins, GPIO.OUT)
GPIO.setup(buzzer, GPIO.OUT)
GPIO.output(buzzer, GPIO.LOW)

stepper_sequence = []
stepper_sequence.append([GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.LOW])
stepper_sequence.append([GPIO.LOW, GPIO.HIGH, GPIO.LOW, GPIO.LOW])
stepper_sequence.append([GPIO.LOW, GPIO.LOW, GPIO.HIGH, GPIO.LOW])
stepper_sequence.append([GPIO.LOW, GPIO.LOW, GPIO.LOW, GPIO.HIGH])

lightLevel = 100
angle = 90  # desired angle in degrees to be turned into steps
circle = 360
stepsPerRevolution = 512
steps = int(angle / circle * stepsPerRevolution)
open = False

bus = smbus.SMBus(1)


def light():
    bus.write_byte(address, A0)
    return bus.read_byte(address)


def play(frequency, duration):
    period = 1.0 / frequency
    cycles = int(duration * frequency)
    for i in range(cycles):
        GPIO.output(buzzer, GPIO.HIGH)
        time.sleep(period / 2)
        GPIO.output(buzzer, GPIO.LOW)
        time.sleep(period / 2)


def _play():
    play(262, 1)
    play(523, 1)
    play(2093, 1)


def distance():
    global hand_distance
    while True:
        bus.write_byte(address, A2)
        hand_distance = bus.read_byte(address)


def curtain():
    global open
    if open == False:
        for i in range(steps):
            for row in stepper_sequence:
                GPIO.output(stepper_pins, row)
                time.sleep(0.01)
        open = True
    return


def alarm():
    global delay
    for i in range(10):
        GPIO.output(buzzer, GPIO.HIGH)
        time.sleep(delay/2)
        GPIO.output(buzzer, GPIO.LOW)
        time.sleep(delay/2)
    delay -= 0.1
    return


def mainfunc():
    try:
        while True:  # Main while loop
            value = light()  # calls light function and returns the light value
            print(value)
            if light() <= lightLevel:
                curtain()
                _play()
            if hand_distance < 100:
                break
    except KeyboardInterrupt:
        pass


# create a thread for each function
thread1 = threading.Thread(target=distance)
thread2 = threading.Thread(target=mainfunc)

# start the threads
thread1.start()
thread2.start()

# monitor the command line for the "stop" command
while True:
    cmd = input()
    if cmd == "stop":
        stop_requested = True
        break

# wait for the threads to finish
thread1.join()
thread2.join()

GPIO.cleanup()
