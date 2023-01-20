#!/usr/bin/env python3

from config import *
import RPi.GPIO as GPIO
import time
import os
import board
import neopixel
import random

execute = True

colors = [(255, 0, 0),(0, 255, 0),(0, 0, 255),(255, 255, 0),(0, 255, 255),(255, 0, 255)]
colorWhite = (255,255,255)
colorBlank = (0,0,0)
numberOfColors = 6
chosingColor = False
pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
shoot = [0,0,0,0,0]
code = [0,0,0,0,0]
pixelsPosition = 0
numberOfPositions = 6
browseHints = False
win = False
SIZE_OF_BOARD = 5

# Czarna szpilka - pionek został umieszczony na właściwym miejscu
# Biała szpilka  - właściwy kolor, ale na niewłaściwym miejscu
# hints = [czarne szpilki, biale szpilki]
hints = [0, 0]


#poczatkowe ustawienie zmiennych w grze
def setup():
    global chosingColor
    global browseHints
    global win
    global shoot
    global code    

    pixels.fill(colors[0])
    pixels[5]=(colorBlank)
    pixels[6]=(colorBlank)
    pixels[7]=(colorBlank)
    pixels[pixelsPosition] = colorWhite
    pixels.show()

    chosingColor = False
    browseHints = False
    win = False

    shoot = [0,0,0,0,0]
    code = [random.randint(0, 5) for _ in range(5)]


def encoderCallback(channel):
    global chosingColor
    global pixels
    global pixelsPosition
    global shoot
    global numberOfColors
    global numberOfPositions
    global colors
    global browseHints

    enRight = GPIO.input(encoderRight)

    if browseHints:
        #dzialanie encodera podczas przeglądania poprzednich strzałów i podpowiedzi na wyświetlaczu
    else:
        if chosingColor: 
            if enRight == 0:
                shoot[pixelsPosition] += 1
                shoot[pixelsPosition] %= numberOfColors
                pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
            if enRight == 1:
                shoot[pixelsPosition] -= 1 + numberOfColors
                shoot[pixelsPosition] %= numberOfColors
                pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
        else:
            if enRight == 0:
                if pixelsPosition == 5:
                    pixels[pixelsPosition] = colorBlank
                else:
                    pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
                pixelsPosition += 1
                pixelsPosition %= numberOfPositions
                pixels[pixelsPosition] = colorWhite
            if enRight == 1:
                if pixelsPosition == 5:
                    pixels[pixelsPosition] = colorBlank
                else:
                    pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
                pixelsPosition -= 1 + numberOfPositions
                pixelsPosition %= numberOfPositions
                pixels[pixelsPosition] = colorWhite
        pixels.show()

def buttonRedPressedCallback(channel):
    global chosingColor
    global pixels
    global pixelsPosition
    global shoot
    global colorWhite
    global colors

    if pixelsPosition != 5:
        if chosingColor:
            chosingColor = False
            pixels[pixelsPosition] = colorWhite
        else:
            chosingColor = True
            pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
        pixels.show()

def buttonGreenPressedCallback(channel):
    if pixelsPosition == 5:
        checkGuess()
        #kod dodający nowy strzał na wyświetlacz
    else:
        browseHints = True
        #kod zajmujący się przeglądaniem poprzednich strzałów i podpowiedzi na wyświetlaczu

def checkGuess():
    for position in range(SIZE_OF_BOARD):
        if code[position] == shoot[position]:
            hints[0] += 1

    for position in range(SIZE_OF_BOARD):
        if shoot[position] in code and code[position] != shoot[position]:
            hints[1] += 1

def play():
    global win

    setup()

    while not win:
        time.sleep(0.1)


if __name__ == "__main__":
    print("\nProgram started")
    #zalogowanie się użytkownika

    GPIO.add_event_detect(encoderLeft, GPIO.FALLING, callback=encoderCallback, bouncetime=200)
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=buttonRedPressedCallback, bouncetime=200)
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=buttonGreenPressedCallback, bouncetime=200)

    play()

    #kod odpowiedzialny za uruchomienie gry ponownie lub zakończenie rozgrywki

    #wylogowanie się użytkownika (przesłanie odpowiedzi do bazy)

    GPIO.cleanup()
    
    print("\nProgram finished")
