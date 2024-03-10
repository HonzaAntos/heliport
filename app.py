from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from urllib import request
import xml.etree.ElementTree as ET
import time
from time import sleep
import threading
# RPi.GPIO can not install to python via pip3 install..
import RPi.GPIO as GPIO
import array
from ola.ClientWrapper import ClientWrapper
import gpiozero
from gpiozero import Button

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///heliport.db'
database = SQLAlchemy()
db = SQLAlchemy(app)

my_url = "http://89.190.88.186:88/"

click_count = 0
is_clicked = False
timer_done = False
running_multiple = False


# first thread below = t1
def checker_thread():
    while True:
        time.sleep(60)
        checker()


# second thread below = t2
def checker_thread_first_click():
    while True:
        sleep(0.1)
        checker_click()


# third thread below = t3
def checker_thread_multiple_click():
    while True:
        sleep(0.2)
        checker_click_multiple()


# fourth thread below = t4
def checker_thread_timer():
    timer(0, 5)


def checker_click():
    global running_multiple
    global click_count
    global is_clicked
    if not running_multiple:
        print("running first click")
        # pin 11 on raspberry & 17 = GPIO on board => SAME
        GPIO.setwarnings(False)  # Ignore warning for now
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(17, GPIO.IN)

        # waiting for rising edge
        try:
            while True:
                GPIO.wait_for_edge(17, GPIO.RISING)
                print("--> Pressed <--")
                start = time.time()
                time.sleep(0.2)

                while GPIO.input(17) == GPIO.HIGH:
                    time.sleep(0.02)

                length = time.time() - start
                print(length)

                # edge filter detector
                if length > 5:
                    print("Long Press --- Do nothing")
                elif length > 1:
                    print("Medium Press --- Do nothing as well")
                else:
                    print("Short Press")
                    print("Port 17 is 1-True---> is_clicked")
                    is_clicked = True
                    checker_thread_timer()

        except KeyboardInterrupt:
            GPIO.cleanup()


def timer(itt, sec):
    # itt = start time, sec = how long should timer works in seconds
    global timer_done
    timer_done = False
    # print("itt", itt)
    while itt < sec:
        time.sleep(1)
        itt = itt + 1
        print(itt)
        if itt == sec:
            timer_done = True


def checker_click_multiple():
    if not timer_done:
        print("multiple running")
        global running_multiple
        running_multiple = True

       # def DmxSent(state):
           # wrapper.Stop()

        global click_count
        GPIO.setwarnings(False)  # Ignore warning for now
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(17, GPIO.IN)

        while GPIO.input(17):
            print("--> Pressed in multiple <--")
            start_time = time.time()
            time.sleep(0.1)

            while GPIO.input(17) == GPIO.HIGH:
                time.sleep(0.05)

            length_time = time.time() - start_time
            print(length_time)

            # edge filter detector
            if length_time > 3:
                print("Long Press --- turn off the lights")
                click_count = 0
            elif length_time > 1:
                print("Medium Press  --- nothing to do")
            else:
                print("Short Press")
                print("click_count ++")
                click_count = click_count + 1

        print("##############", click_count, "##############")

        if click_count == 1:
            print("brightness = 33% --- BLUE")
            # print("time:", t_start)
            universe = 1
            # here change "1" if you named your universe differently on http://192.168.0.109:9090/ola.html
            data = array.array('B', [10, 50, 255])
            wrapper = ClientWrapper()
            client = wrapper.Client()
            client.SendDmx(universe, data, DmxSent)
            wrapper.Run()
            # sending DMX file from example - i don´t know if all of these examples works
        if click_count == 2:
            print("brightness = 67% --- GREEN")
            universe = 1
            data = array.array('B', [50, 255, 10])
            wrapper = ClientWrapper()
            client = wrapper.Client()
            client.SendDmx(universe, data, DmxSent)
            wrapper.Run()
            # sending DMX file from example
        if click_count == 3:
            print("brightness = 100% --- RED")
            universe = 1
            data = array.array('B', [255, 50, 10])
            wrapper = ClientWrapper()
            client = wrapper.Client()
            client.SendDmx(universe, data, DmxSent)
            wrapper.Run()
            # sending DMX file from example
        if click_count > 3:
            print("RESET COUNT")
            click_count = 0
            t_start = 0
    else:
        print("timeout!!!!")
        running_multiple = False


def reading_data():
    url = 'https://api.meteo-pocasi.cz/api.xml?action=get-meteo-data&client=xml&id=00004799ujT8Ul6looxb8ods4SudMyuS2LMno2wilQrFBy00myc'
    # url address with xml file, every 60 (+- 3s) change data on this page
    # print("Retrieving", url)
    html = request.urlopen(url)
    data = html.read()
    # print("Retrieved", len(data), "characters")

    tree = ET.fromstring(data)
    results = tree.findall('.//sensor')
    # finding value sensor from url

    icount = len(results)
    valueArray = []
    typeSensorArray = []

    # getting values from meteo-station
    for result in results:
        value = float(result.find('value').text)
        valueArray.append(value)
        typeSensor = result.find('type').text
        typeSensorArray.append(typeSensor)
        # print(result.tag, typeSensor, value)
        # print("*****")

    windSpeed = valueArray[12]
    windGust = valueArray[13]
    windDirection = valueArray[11]
    print(windSpeed, windGust, windDirection)
    print("<<<<<--->>>>>")
    #    print(valueArray)
    #    print("<<<<<--->>>>>")
    #    print("<<<<<--->>>>>")
    #    print(typeSensorArray)
    #    print("<<<<<--->>>>>")
    #    print("_____")
    #    print(icount)
    #    print("_____")
    #    print(data)
    #    print("_____")
    #    print(tree)
    #    print("_____")
    #    print(results)
    #    print("_____")
    lights(windSpeed, windGust, windDirection)
    return windSpeed, windGust, windDirection


def lights(windSpeed, windGust, windDirection):

    def DmxSent(state):
        if not state.Succeeded():
            wrapper.Stop()

    if windDirection == 0:
        print("1 wind direction: ", windDirection)
        print("ukazka jak by mel program fungovat - nevim jak jsou svetla fyzicky zapojene, tohle je jen odhad")
        print("R = cervena barva, 0 = oranzova + blikani, B= modra, sipka = smer vetru")
        print("                   1   -R-                                        S                 ")
        print("              2   -R-  / \  -R-    16                                               ")
        print("         3     -R-    /|||\    -R-   15                   SZ             SV         ")
        print("       4     -O-     / ||| \     -O-    14                                          ")
        print("       5     -O-       |||       -O-    13    _______  Z       svetove       V      ")
        print("       6     -O-       |||       -O-    12    -------            str                ")
        print("         7     -B-     |||     -B-    11                  JZ              JV        ")
        print("               8  -B-  |||  -B-   10                                                ")
        print("                   9   -B-                                        J                 ")
        print("brightness = 100% --- RED")
        universe = 1
        data = array.array('B', [
            255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 128, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            255, 128, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 128, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 128, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            255, 128, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 128, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ])


        # B = binary (0-255 value)
        # [R,G,B,-, STROBE, -,-,-,-,-,-,-,-,-,-]
        wrapper = ClientWrapper()
        client = wrapper.Client()
        client.SendDmx(universe, data, DmxSent)
        wrapper.Run()
        # sending DMX file from example

    if windDirection == 45:
        print("2 wind direction: ", windDirection)

    if windDirection == 90:
        print("3 wind direction: ", windDirection)

    if windDirection == 135:
        print("4 wind direction: ", windDirection)

    if windDirection == 180:
        print("5 wind direction: ", windDirection)
        print("                      -B-")
        print("                 -B-  |||  -B-")
        print("              -B-     |||     -B-")
        print("            -O-       |||       -O-")
        print("            -O-       |||       -O-")
        print("            -O-     \ ||| /     -O-")
        print("              -R-    \|||/    -R-")
        print("                 -R-  \ /  -R-")
        print("                      -R-")

    if windDirection == 225:
        print("6 wind direction: ", windDirection)

    if windDirection == 270:
        print("7 wind direction: ", windDirection)

    if windDirection == 315:
        print("8 wind direction: ", windDirection)


class Heliport(db.Model):
    windSpeed, windGust, windDirection = reading_data()
    print("------------------------------")
    print("storing to db")
    print(windSpeed, windGust, windDirection)
    print("--------------------------")
    id = db.Column(db.Integer, primary_key=True)
    windSpeed = db.Column(db.Float)
    windGust = db.Column(db.Float)
    windDirection = db.Column(db.Float)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id


def checker():
    # print("checker running...")
    reading_data()


@app.route('/', methods=['GET'])
def index():
    windSpeed, windGust, windDirection = reading_data()
    # print("index running too")
    # print(windSpeed, windGust, windDirection)
    return '<h1 align="center">Heliport!</h1>' \
           '<table style="width:100%">' \
           '<tr>' \
           '<th>Rychlost vetru</th>' \
           '<th>Naraz vetru</th>' \
           '<th>Smer vetru</th>' \
           '</tr>' \
           '<tr>' \
           '<th> {windSpeed} </th>' \
           '<th> {windGust} </th>' \
           '<th> {windDirection} </th>' \
           '</table>'.format(windSpeed=windSpeed, windGust=windGust, windDirection=windDirection)


if __name__ == "__main__":
    t1 = threading.Thread(target=checker_thread)
    t2 = threading.Thread(target=checker_thread_first_click)
    t3 = threading.Thread(target=checker_thread_multiple_click)
    t4 = threading.Thread(target=checker_thread_timer)
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t1.join()
    t2.join()
    t3.join()
    t4.join()
    # t2.join(timeout=5)
    app.run(debug=True)

"""""
without join:
+---+---+------------------                     main-thread
    |   |
    |   +...........                            child-thread(short)
    +..................................         child-thread(long)

with join
+---+---+------------------***********+###      main-thread
    |   |                             |
    |   +...........join()            |         child-thread(short)
    +......................join()......         child-thread(long)

with join and daemon thread
+-+--+---+------------------***********+###     parent-thread
  |  |   |                             |
  |  |   +...........join()            |        child-thread(short)
  |  +......................join()......        child-thread(long)
  +,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,     child-thread(long + daemonized)

'-' main-thread/parent-thread/main-program execution
'.' child-thread execution
'#' optional parent-thread execution after join()-blocked parent-thread could 
    continue
'*' main-thread 'sleeping' in join-method, waiting for child-thread to finish
',' daemonized thread - 'ignores' lifetime of other threads;
    terminates when main-programs exits; is normally meant for 
    join-independent tasks
    
 ***************************************  HELP  ****************************************************   
    
    settings raspberry ola 
            https://www.openlighting.org/ola/developer-documentation/python-api/
            
    ola examples git:
            https://github.com/OpenLightingProject/ola/tree/master/python/examples
            https://github.com/RichardKrikler/RaspberryPi_DMX-Light
            
    something like tutorial on DMX (USB) on youtube:
            https://www.youtube.com/watch?v=3rJIqyxE3aY
            
    setting ola / new universe and devices:
            http://192.168.0.109:9090/ola.html (localHost)
            newest : http://192.168.25.214:9090/ola.html
        
    setting output mode on raspberry:
            https://bitwizard.nl/wiki/Dmx_interface_for_raspberry_pi    
            
"""
