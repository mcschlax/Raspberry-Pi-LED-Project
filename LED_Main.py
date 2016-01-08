#LED_Main
#Mark Schlax
#1/7/2016
#
#Using pigpiod, send power through the Pi to turn on and off analog RGB LEDs
#in a rainbow fashion. Can also be used as an alarm clock if a time is inputed
#or read in from a config file

import pigpio
import math
import time
import configparser
import os
from _thread import start_new_thread

#true when running, false when closing/closed
program_state = True

#constant used when time.sleep is called to reduce cpu load or limit light change rate
sleep_delay = .1

#when rainbow is running
rainbow_state = False

#desired amount of time lights on, seconds
light_desired_time = 600
#led brightness = brightness +- (0 to flux)
light_brightness = 5
light_flux = 10
    
#gpio pins
RED_PIN = 20
GRN_PIN = 21
BLU_PIN = 16

#true when clock is set, false otherwise
clock_set = False
#true when clock is running
clock_state = False
#alarm clock start end values
clock_start_hour = -1
clock_start_minute = -1
clock_end_hour = -1
clock_end_minute = -1

#alarm clock config
#ini file name, along with seciton headers and values
config_file_name = "/home/pi/LED_Main.ini"
config_clock_start = "clock_start"
config_clock_end = "clock_end"
config_clock_hour = "clock_hour"
config_clock_minute = "clock_minute"
config_light = "config_light"
config_brightness = "config_brightness"
config_flux = "config_flux"

def setLights(r, g, b):
    pi.set_PWM_dutycycle(RED_PIN, checkBrightness(r))
    pi.set_PWM_dutycycle(GRN_PIN, checkBrightness(g))
    pi.set_PWM_dutycycle(BLU_PIN, checkBrightness(b))
    time.sleep(sleep_delay)

def checkBrightness(v):
    if v < 0:
        return 0
    if v > 255:
        return 255
    return v

def startLights(desired_time, incoming_state):
    global program_state
    global light_brightness
    global light_flux
    
    #light values
    length = desired_time/sleep_delay
    r_frequency = g_frequency = b_frequency = (2 * math.pi)/length #each color only repeats once
    r_phase = 2 * math.pi * 1/3
    g_phase = 2 * math.pi * 2/3
    b_phase = 2 * math.pi * 0/3
    
    i = 0
    while program_state and ((rainbow_state and incoming_state == "rainbow") or (clock_state and incoming_state == "clock")) and i < length:
        r = math.sin(r_frequency*i + r_phase) * light_flux + light_brightness
        g = math.sin(g_frequency*i + g_phase) * light_flux + light_brightness
        b = math.sin(b_frequency*i + b_phase) * light_flux + light_brightness
        setLights(r, g, b)
        i += 1
        
def endLights():
    setLights(0,0,0)

def checkValidClock(start_hour, start_minute, end_hour, end_minute):
    global clock_start_hour
    global clock_start_minute
    global clock_end_hour
    global clock_end_minute
    global clock_set
    global clock_state
    
    start_hour = (int)(start_hour)
    start_minute = (int)(start_minute)
    end_hour = (int)(end_hour)
    end_minute = (int)(end_minute)
    message = "Clock:\nStart Time: " + (str)(start_hour) + ":" + (str)(start_minute) + "\n" + "End Time: " + (str)(end_hour) + ":" + (str)(end_minute)

    #hours are (0,23), minutes are (0, 59), start hour must be < end hour unless start hour = end hour and start minute <= end minute
    #basically an alarm clock...
    if (start_hour >= 0 and start_hour <= end_hour and end_hour < 24 and start_minute >= 0 and start_minute < 60 and end_minute >= 0 and end_minute < 60 and ((start_hour != end_hour) or (start_hour == end_hour and start_minute <= end_minute))):
        clock_start_hour = start_hour
        clock_start_minute = start_minute
        clock_end_hour = end_hour
        clock_end_minute = end_minute
        clock_set = True
        clock_state = True
    else:
        message = "Invalid: \n" + message
    
    return message

def showClock():
    global clock_start_hour
    global clock_start_minute
    global clock_end_hour
    global clock_end_minute
    global clock_set

    if clock_set:
        return "Clock:\nStart Time: " + (str)(clock_start_hour) + ":" + (str)(clock_start_minute) + "\n" + "End Time: " + (str)(clock_end_hour) + ":" + (str)(clock_end_minute)
    return "Clock is not set"
    
def loadConfig():
    global config_file_name
    global config_clock_start
    global config_clock_end
    global config_clock_hour
    global config_clock_minute
    global config_light
    global config_brightness
    global config_flux
    global clock_set
    global light_brightness
    global light_flux
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file_name)

        start_hour = (int)(config[config_clock_start][config_clock_hour])
        start_minute = (int)(config[config_clock_start][config_clock_minute])
        end_hour = (int)(config[config_clock_end][config_clock_hour])
        end_minute = (int)(config[config_clock_end][config_clock_minute])

        brightness = (int)(config[config_light][config_brightness])
        flux = (int)(config[config_light][config_flux])
        
        checkValidClock(start_hour, start_minute, end_hour, end_minute)
        
        #remove invalid config file if necessary
        if not clock_set:
            os.remove(config_file_name)
        else:
            #config is valid, meaning clock was set, so set lights
            light_brightness = checkBrightness(brightness)
            light_flux = checkBrightness(flux)
    except:
        print ("Load error")
        pass

def writeConfig():
    global config_clock_start
    global config_clock_end
    global config_clock_hour
    global config_clock_minute
    global clock_start_hour
    global clock_start_minute
    global clock_end_hour
    global clock_end_minute
    global config_light
    global config_brightness
    global config_flux
    global light_brightness
    global light_flux

    try:
        config = configparser.ConfigParser()

        config[config_clock_start] = {}
        config[config_clock_end] = {}
        config[config_light] = {}
        
        config[config_clock_start][config_clock_hour] = (str)(clock_start_hour)
        config[config_clock_start][config_clock_minute] = (str)(clock_start_minute)
        config[config_clock_end][config_clock_hour] = (str)(clock_end_hour)
        config[config_clock_end][config_clock_minute] = (str)(clock_end_minute)
        config[config_light][config_brightness] = (str)(light_brightness)
        config[config_light][config_flux] = (str)(light_flux)

        with open(config_file_name, "w") as configfile:
            config.write(configfile)
    except:
        print ("Write error")
        pass

#main thread
def runInput():
    global program_state
    global rainbow_state
    global clock_state
    global clock_set
    global light_desired_time
    global light_brightness
    global light_flux
    
    while program_state == True:
        user_input = input("Input: ")
        
        if user_input == "exit":
            if clock_set:
                user_input = input("Save?: ")
                if user_input == "yes":
                    writeConfig()
            
            rainbow_state = False
            clock_state = False
            program_state = False
            
            print ("Finished")
            
        elif user_input == "start rainbow":
            if rainbow_state:
                print ("Rainbow already on")
            else:
                light_desired_time = (int)(input("How long?: "))
                rainbow_state = True
                print ("Rainbow started")
            
        elif user_input == "stop rainbow":
            if not rainbow_state:
                print ("Rainbow already stopped")
            else:
                rainbow_state = False
                print("Rainbow stopped")

        elif user_input == "change brightness":
            light_brightness = checkBrightness((int)(input("New brightness: ")))

        elif user_input == "change flux":
            light_flux = checkBrightness((int)(input("New flux: ")))
            
        elif user_input == "start clock":
            if clock_set:
                if clock_state:
                    print ("Clock already on")
                else:
                    clock_state = True
                    print ("Clock started")
            else:
                print ("Clock is not set")

        elif user_input == "stop clock":
            if not clock_state:
                if clock_set:
                    print ("Clock already stopped")
                else:
                    print ("Clock is not set")
            else:
                clock_state = False
                print ("clock stopped")
                
        elif user_input == "set clock":
            start_hour = input("Start hour (0,23): ")
            start_minute = input("Start minute (0,59): ")
            end_hour = input("End hour (0,23): ")
            end_minute = input("End minute (0,59): ")
            
            message = checkValidClock(start_hour, start_minute, end_hour, end_minute)
            print (message)

        elif user_input == "save":
            writeConfig()

        elif user_input == "load":
            loadConfig()
        
        elif user_input == "time":
            print ("Time: " + time.strftime("%H:%M"))

        elif user_input == "ps":
            print ("Program State: " + (str)(program_state))
            print ("Rainbow State: " + (str)(rainbow_state))
            print ("Clock State: " + (str)(clock_state))
            print (showClock())
            print ("Light Brightness: " + (str)(light_brightness))
            print ("Light Flux: " + (str)(light_flux))
        
        elif user_input == "ls":
            print ("exit")
            print ("start rainbow")
            print ("stop rainbow")
            print ("change brightness")
            print ("change flux")
            print ("start clock")
            print ("stop clock")
            print ("show clock")
            print ("set clock")
            print ("time")
            print ("ps")
            print ("ls")
        else:
            print ("unrecognized: " + user_input)
            
        time.sleep(sleep_delay) #to reduce cpu load

#threaded rainbow
def runRainbow():
    global program_state
    global rainbow_state
    global light_desired_time
    
    while program_state:
        if rainbow_state:
            startLights(light_desired_time, "rainbow")
            endLights()
            rainbow_state = False
        else:
           time.sleep(sleep_delay)

#threaded clock
def runClock():
    global program_state
    global clock_state

    while program_state:
        if clock_state:
            current_hour = (int)(time.strftime("%H"))
            current_minute = (int)(time.strftime("%M"))
            if (current_hour == clock_start_hour and current_minute == clock_start_minute):
                total_time = (int)(((clock_end_hour * 60 + clock_end_minute) * 60) - ((clock_start_hour * 60 + clock_start_minute) * 60))
                
                startLights(total_time, "clock")
                endLights()
            else:
                time.sleep(sleep_delay*10)
        time.sleep(sleep_delay)

if __name__ == "__main__":
    pi = pigpio.pi()

    loadConfig()
    start_new_thread(runClock, ()) #third thread for clock timer
    start_new_thread(runRainbow, ()) #second thread for rainbow display
    runInput() #main thread checks input
         
    pi.stop()
