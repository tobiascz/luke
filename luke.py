import os
import pygame
import pygame.camera
from pygame.locals import *
from PIL import Image
from threading import Thread
import RPi.GPIO as GPIO
import time
import datetime
import numpy as np

# 20 cm distance , height/width  = 64 64 --> 10*10 = 100cm2 / 10 /64 --> 0.156 pixel
# 40 cm distance , height/width  = 36/36 --> 10*10 = 100cm2 / 10 / 36 --> 0.277/cm/pixel
# 50 cm distance , height/width  = 30/30 --> 10*10 = 100cm2 / 10 /30 --> 0.333
mode_rot_enc =0
distance_glob =0.0
counter_test = 0
capture = True
distance = 0
distdelay = 0
elwidth = 40
elheight = 40
area = 0
formoverlay = 1
flag = 0
Last_RoB_Status = 0
Current_RoB_Status = 0
dist_list = [0,0,0,0,0]
pictureVar = False


os.environ["SDL_FBDEV"] = "/dev/fb1"
os.environ['SDL_VIDEODRIVER'] = "fbcon"

DEVICE = '/dev/video0'
SIZE = (160, 128)
FILENAME = 'capture.png'

BLACK = (0, 0, 0)

# GPIO Modus (BOARD / BCM)
GPIO.setmode(GPIO.BCM)

# GPIO Pins zuweisen
GPIO_TRIGGER = 2
GPIO_ECHO = 3


RoAPin = 17    # pin11
RoBPin = 27    # pin12
RoSPin = 22    # pin13

RoCPin = 4
RoFPin = 14

# poti
GPIO.setup(RoAPin, GPIO.IN)  # input mode
GPIO.setup(RoBPin, GPIO.IN)
GPIO.setup(RoSPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


#buttons

GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def setup():
    changeform()

# Richtung der GPIO-Pins festlegen (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

def rotaryThread():
    while capture:
        rotaryDeal()
        time.sleep(0.005)


def rotaryDeal():
    global flag
    global Last_RoB_Status
    global Current_RoB_Status
    global elwidth
    global mode_rot_enc
    global elheight
    Last_RoB_Status = GPIO.input(RoBPin)
    while (not GPIO.input(RoAPin)):
        Current_RoB_Status = GPIO.input(RoBPin)
        flag = 1
    if flag == 1:
        flag = 0
        if (Last_RoB_Status == 0) and (Current_RoB_Status == 1):
            if(mode_rot_enc == 1 and elwidth < 140):
                elwidth = elwidth +2
            elif(elheight<100):
                elheight = elheight + 2

        if (Last_RoB_Status == 1) and (Current_RoB_Status == 0):
            if(mode_rot_enc == 1 and elwidth > 10):
                elwidth = elwidth -2
            elif(elheight > 10):
                print(str(elheight))
                elheight = elheight - 2


def pixdens(distance):
    return 0.0058 * distance + 0.04


def calc_area_rect(distance, elwidth, elheight):
    pix = pixdens(distance)
    area = (elwidth * pix) * (elheight * pix)
    return round(area, 1)


def calc_area_ellipse(distance, elwidth, elheight):
    pix = pixdens(distance)
    area = ((elwidth * pix) / 2) * ((elheight * pix) / 2) * 3.1415
    return round(area, 1)


def distanz():
    # setze Trigger auf HIGH
    global distance_glob
    global dist_list
    GPIO.output(GPIO_TRIGGER, True)

    # setze Trigger nach 0.01ms aus LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartZeit = time.time()
    StopZeit = time.time()

    # speichere Startzeit
    while GPIO.input(GPIO_ECHO) == 0:
        StartZeit = time.time()

    # speichere Ankunftszeit
    while GPIO.input(GPIO_ECHO) == 1:
        StopZeit = time.time()

    # Zeit Differenz zwischen Start und Ankunft
    TimeElapsed = StopZeit - StartZeit
    # mit der Schallgeschwindigkeit (34300 cm/s) multiplizieren
    # und durch 2 teilen, da hin und zurueck
    distanze = (TimeElapsed * 34300) / 2
    old_dist = distanze
    if(distanze < 300):
        dist_list.pop(0)
        dist_list.append(distanze)
        medi = np.median(dist_list)
        distance_glob = round(medi,1)
    #return distanze


def displaytext(text, size, line, color, clearscreen, screen):
    if clearscreen:
        screen.fill((0, 0, 0))

    font = pygame.font.Font(None, size)
    text = font.render(text, 0, color)
    rotated = pygame.transform.rotate(text, 270)
    textpos = rotated.get_rect()
    textpos.centery = 64
    if line == 1:
        textpos.centerx = 145
        screen.blit(rotated, textpos)
    elif line == 2:
        textpos.centerx = 20
        screen.blit(rotated, textpos)
    elif line == 3:
        textpos.centerx = 120
        screen.blit(rotated, textpos)

def handle(event):
    global capture
    global formoverlay
    global elheight
    global elwidth
    if event.type == KEYDOWN:
        print("elheight: " + str(elheight) + "  elwidth:" + str(elwidth))
    if event.type == QUIT:
        capture = False
    elif event.type == KEYDOWN and event.key == K_s:
        pygame.image.save(screen, FILENAME)
    elif event.type == KEYDOWN and event.key == K_o:
        print("toggle overlay")
        if (formoverlay == 2):
            formoverlay = 0
        elif (formoverlay == 0):
            formoverlay = 1
        elif (formoverlay == 1):
            formoverlay = 2

    elif event.type == KEYDOWN and event.key == K_UP:
        print("UP")
        elheight = elheight + 2
    elif event.type == KEYDOWN and event.key == K_DOWN:
        print("DOWN")
        elheight = elheight - 2
    elif event.type == KEYDOWN and event.key == K_LEFT:
        elwidth = elwidth - 2
    elif event.type == KEYDOWN and event.key == K_RIGHT:
        elwidth = elwidth + 2


def modFrame(frame):
    string_frame = pygame.image.tostring(frame, "RGBA", False)
    im = Image.frombytes("RGBA", SIZE, string_frame)
    b, g, r, a = im.split()
    im = Image.merge("RGB", (r, g, b))
    mode = im.mode
    size = im.size
    data = im.tobytes()
    frame = pygame.image.fromstring(data, size, mode)
    return frame

def camstream():
    global capture
    global distance
    global distdelay
    global elwidth
    global elheight
    global formoverlay
    global area
    global distance_glob
    global pictureVar
    pygame.init()
    pygame.camera.init()
    display = pygame.display.set_mode(SIZE, 0)
    camera = pygame.camera.Camera(DEVICE, SIZE)
    camera.start()
    screen = pygame.surface.Surface(SIZE, 0, display)
    pygame.mouse.set_visible(0)
    thread = Thread(target = rotaryThread)
    thread.start()
    while capture:
        if(not pictureVar):
            frame = camera.get_image(screen)
            frame = modFrame(frame)
            if (formoverlay == 1):
                pygame.draw.ellipse(frame, BLACK, [80 - (elwidth / 2), 64 - (elheight / 2), elwidth, elheight], 3)
            if (formoverlay == 2):
                pygame.draw.rect(frame, BLACK, [80 - (elwidth / 2), 64 - (elheight / 2), elwidth, elheight], 3)
            frame = pygame.transform.rotozoom(frame, 270, 0.8)
            display.fill((0, 0, 0))
            display.blit(frame, (0, 0))
            if (distdelay > 10):
                #distance = round(distanz(), 0)
                thread2 = Thread(target = distanz)
                thread2.start()
                distdelay = 0
                if (formoverlay == 2):
                    area = calc_area_rect(distance_glob, elwidth, elheight)
                elif (formoverlay == 1):
                    area = calc_area_ellipse(distance_glob, elwidth, elheight)
            distdelay = distdelay + 1

            displaytext("Dist: "+ str(distance_glob), 18, 3, (250, 100, 100), False, display)
            displaytext("Area: " + str(area), 25, 1, (250, 100, 100), False, display)
            pygame.display.flip()
            for event in pygame.event.get():
                handle(event)
        else:
            displaytext("Saved", 18, 2, (0, 0, 0), False, display)
            pygame.display.flip()

    camera.stop()
    pygame.quit()
    GPIO.cleanup()
    return


def aevent(ev = None):
    if GPIO.input(17):
        print("A is rising")
    else:
        print("A is falling")

def bevent(ev=None):
    if GPIO.input(27):
        print("B is rising")
    else:
        print("B is falling")

#right --> B_d B_d B_u A_u A_d
#right --> B_d A_d B_u A_u
#right --> B_d B_d A_d B_u A_d



def form():
    global formoverlay
    if (formoverlay == 2):
        formoverlay = 0
    elif (formoverlay == 0):
        formoverlay = 1
    elif (formoverlay == 1):
        formoverlay = 2
    print(str(formoverlay))
start = datetime.datetime.now()
dobbleevent = datetime.datetime.now()

def diameter():
    global start
    global  mode_rot_enc
    global dobbleevent
    current_start = datetime.datetime.now()
    if(current_start-start <  datetime.timedelta(seconds=1)):
        if(current_start - dobbleevent > datetime.timedelta(seconds=1)):
            form()
            dobbleevent = current_start

    else:
        if (mode_rot_enc == 1):
            mode_rot_enc = 0
        else:
            mode_rot_enc = 1
    start = datetime.datetime.now()

def diameterWrap(ev=None):
    diameter()

def takePic(ev=None):
    global pictureVar
    if(pictureVar == True):
        pictureVar = False
    elif (pictureVar == False):
        pictureVar = True

def formChange(ev=None):
    diameter()



def changeform():
    GPIO.add_event_detect(RoSPin, GPIO.FALLING, callback=diameterWrap, bouncetime=20)  # wait for falling
    GPIO.add_event_detect(RoFPin, GPIO.FALLING, callback=takePic, bouncetime =200)
    GPIO.add_event_detect(RoCPin, GPIO.FALLING, callback=formChange, bouncetime=200)
   # GPIO.add_event_detect(RoBPin, GPIO.BOTH, callback=test, bouncetime = 10)
   # GPIO.add_event_detect(RoAPin, GPIO.BOTH, callback=test, bouncetime = 10)



if __name__ == '__main__':
    setup()
    try:
        camstream()
    except KeyboardInterrupt:
        print('stopped')
        GPIO.cleanup()
