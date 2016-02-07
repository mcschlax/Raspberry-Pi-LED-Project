#!/usr/bin/python3
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
from _thread import start_new_thread
    
#gpio pins
RED_PIN = 20
GRN_PIN = 21
BLU_PIN = 16

#true when running, false when closing/closed
program_state = True

#constant used when time.sleep is called to reduce cpu load or limit light change rate
sleep_delay = .1

#true when lights are running
light_state = False
#desired duration of lights, seconds
light_duration = 600
#how many times the lights will cycle accoss time
light_cycles = 1
#led brightness = brightness +- (0 to flux)
light_brightness = 5
light_flux = 10

#true when alarm is running
alarm_state = False
#alarm start end value, will be "hour:minute" in 24-hour format
alarm_start = ""
alarm_end = ""

#config file name, along with seciton headers and values
config_file_name = "/home/pi/Raspberry-Pi-LED-Project/LED_Main.ini"
config_alarm_start = "alarm_start"
config_alarm_end = "alarm_end"
config_alarm_time = "alarm_time"
config_light = "light"
config_light_duration = "duration"
confid_light_cycles = "cycles"
config_light_brightness = "brightness"
config_light_flux = "flux"

def checkBrightness(brightness):
    try:
        new_brightness = int(brightness)
    except:
        return False
    return new_brightness >= 0 and new_brightness <= 255

def checkFlux(flux):
    try:
        new_flux = int(flux)
    except:
        return False
    return (light_brightness + new_flux) <= 255 and (light_brightness - new_flux) >= 0

def checkDuration(duration):
    try:
        new_duration = int(duration)
    except:
        return False
    return new_duration > 0

def checkCycles(cycles):
    try:
        new_cycles = int(cycles)
    except:
        return False
    return new_cycles > 0

def checkRGB(r, g, b):
    return checkBrightness(r) and checkBrightness(g) and checkBrightness(b)

def setLights(r, g, b):
    if checkRGB(r, g, b):
        pi.set_PWM_dutycycle(RED_PIN, r)
        pi.set_PWM_dutycycle(GRN_PIN, g)
        pi.set_PWM_dutycycle(BLU_PIN, b)
    time.sleep(sleep_delay)

def startLights():
    global program_state
    global light_state
    global light_duration
    global light_cycles
    global light_brightness
    global light_flux

    #converting duration to number of program loops
    length = light_duration/sleep_delay
    #each color only repeats light_cycles times
    r_frequency = g_frequency = b_frequency = (2 * math.pi)/(length/light_cycles)
    #seperating the three sin curves with a phase shift
    r_phase = 2 * math.pi * 1/3
    g_phase = 2 * math.pi * 2/3
    b_phase = 2 * math.pi * 0/3
    
    for i in range(0, length):
        if not light_state:
            break
        #three seperate sine curves create a rainbow effect
        r = math.sin(r_frequency*i + r_phase) * light_flux + light_brightness
        g = math.sin(g_frequency*i + g_phase) * light_flux + light_brightness
        b = math.sin(b_frequency*i + b_phase) * light_flux + light_brightness
        setLights(r, g, b)
        
def endLights():
    global light_state
    
    light_state = False
    setLights(0,0,0)

def calculateDifference(*times):
	if not times or len(times) > 2:
		return -1
	if len(times) == 1:
		time1 = time.strftime("%H:%M").split(":")
		start_hour = int(time1[0])
		start_minute = int(time1[1])
		time2 = times[0].split(":")
		end_hour = int(time2[0])
		end_minute = int(time2[1])
	else:
		time1 = times[0].split(":")
		start_hour = int(time1[0])
		start_minute = int(time1[1])
		time2 = times[1].split(":")
		end_hour = int(time2[0])
		end_minute = int(time2[1])
	return (((end_hour - start_hour)*60 + (end_minute - start_minute))*60)

def startAlarm(duration):
    length = duration/sleep_delay
    #red light will flash once every second
    r_frequency = (2 * math.pi)/(length/duration)
    
    for i in range(0, length):
        if not alarm_state:
            break
        r = math.sin(r_frequency*i) * (light_flux + light_brightness)
        g = 0
        b = 0
        setLights(r, g, b)
    

def checkValidTime(in_time):
    split_time = in_time.split(":")

    if len(split_time) != 2:
        return ""
    try:
        hour = int(split_time[0])
        minute = int(split_time[1])
    except:
        return ""
    #check hour:minute is 24-hour format
    if hour < 0 or hour >= 24 or minute < 0 or minute >= 60:
        return ""

    #turn back to string
    if hour < 10:
        str_hour = "0" + str(hour)
    else:
        str_hour = str(hour)
    if minute < 10:
        str_minute = "0" + str(minute)
    else:
        str_minute = str(minute)
    return str_hour + ":" + str_minute

def checkValidAlarm(start_time, end_time):
    if checkValidTime(start_time) and checValidTime(end_time):
        return calculateDifference(start_time, end_time) >= 0
    return False

def checkAlarmSet():
    global alarm_start
    global alarm_end
    
    return alarm_start and alarm_end

def showAlarm():
    global alarm_start
    global alarm_end

    message = "Alarm is not set"
    if checkAlarmSet():
        message = "Alarm:\n"
        message += "Start Time: " + alarm_start[0] + ":" + alarm_start[1] + "\n"
        message += "End Time: " + alarm_end[0] + ":" + alarm_end[1]
    
    return message
    
def loadConfig():
    global light_duration
    global light_cycles
    global light_brightness
    global light_flux
    global alarm_start
    global alarm_end
    global config_file_name
    global config_alarm_start
    global config_alarm_end
    global config_alarm_time
    global config_light
    global config_light_duration
    global config_light_cycles
    global config_light_brightness
    global config_light_flux
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file_name)

        new_light_duration = int(config[config_light][config_light_duration])
        new_light_cycles = int(config[config_light][config_light_cycles])
        new_light_brightness = int(config[config_light][config_light_brightness])
        new_light_flux = int(config[config_light][config_light_flux])
        new_alarm_start = config[config_alarm_start][config_alarm_time]
        new_alarm_end = config[config_alarm_end][config_alarm_time]

        valid = True
        if not checkDuration(new_light_duration):
            print ("Within Load, loaded light duration not valid: " + str(new_light_duration))
            valid = False
        if not checkCycles(new_light_cycles):
            print ("Within Load, loaded light cycles not valid: " + str(new_light_cycles))
            valid = False
        if not checkBrightness(new_light_brightness):
            print ("Within Load, loaded light brightness not valid: " + str(new_light_brightness))
            valid = False
        if not checkFlux(new_light_flux):
            print ("Within Load, loaded light flux not valid: " + str(new_light_flux))
            valid = False
        if not checkValidTime(new_alarm_start):
            print ("Within Load, loaded alarm start not valid: " + new_alarm_start)
            valid = False
        if not checkValidTime(new_alarm_end):
            print ("Within Load, loaded alram end not valid: " + new_alarm_end)
            valid = False
        if valid:
            light_duration = new_light_duration
            light_cycles = new_light_cycles
            light_brightness = new_light_brightness
            light_flux = new_light_flux
            alarm_start = checkValidTime(new_alarm_start)
            alarm_end = checkValidTime(new_alarm_end)

    except configparser.Error:
        print ("Within Load, Config Parser had an error")
        pass
    except ValueError:
        print ("Within Load, conversion error")
        pass
    except:
        print ("Within Load, unknown error")
        pass

def saveConfig():
    global light_duration
    global light_cycles
    global light_brightness
    global light_flux
    global alarm_start
    global alarm_end
    global config_file_name
    global config_alarm_start
    global config_alarm_end
    global config_alarm_time
    global config_light
    global config_light_duration
    global config_light_cycles
    global config_light_brightness
    global config_light_flux

    try:
        config = configparser.ConfigParser()

        config[config_alarm_start] = {}
        config[config_alarm_end] = {}
        config[config_light] = {}
        
        config[config_alarm_start][config_alarm_time] = alarm_start
        config[config_alarm_end][config_alarm_time] = alarm_end
        config[config_light][config_brightness] = str(light_duration)
        config[config_light][config_light_duration] = str(light_cycles)
        config[config_light][config_light_cycles] = str(light_brightness)
        config[config_light][config_flux] = str(light_flux)

        with open(config_file_name, "w") as configfile:
            config.write(configfile)

    except configparser.Error:
        print ("Within Save, Config Parser had an error")
        
    except ValueError:
        print ("Within Save, conversion error")

    except:
        print ("Within Save, unknown error")

#main thread
def runInput():
    global program_state
    global light_state
    global light_duration
    global light_cycles
    global light_brightness
    global light_flux
    global alarm_state
    global alarm_start
    global alarm_end
    
    while program_state:
        user_input = input(">>").split(" ")

        command = user_input[0]
        option = ""
        values = ()
        if len(user_input) >= 2:
            option = user_input[1]
            if len(user_input) >= 3:
                values = user_input[2:4]
        
        #exit command
        if command == "exit":
            will_exit = False

            #no option
            if not option:
                will_exit = True
            #save option
            elif option == "save":
                will_exit = True
                print ("Saving")
                saveConfig()
            #help option
            elif option == "help":
                print ("Will terminate program")
                print ("Options:")
                print ("\t\n\t\tWill terminate immediately")
                print ("\tsave\n\t\tWill save before termination")
            else:
                print ("Invalid option please see exit help")

            if will_exit:
                print ("Exiting")
                program_state = False
                light_state = False
                alarm_state = False
                endLights()
                
                print ("Program State: " + str(program_state))
                print ("Light State: " + str(light_state))
                print ("Alarm State: " + str(alarm_state))
                print ("Exited")
            
        #start command
        elif command == "start":
            #light option
            if option == "light":
                if not values:
                    if not light_state:
                        light_state = True
                        print ("Lights started")
                    else:
                        print ("Invalid lights already on, see overview for status")
                else:
                    print ("Invalid number of values for start light please see start help")
            #alarm option
            elif option == "alarm":
                if not values:
                    if checkAlarmSet():
                        if not alarm_state:
                            alarm_state = True
                            print ("Alarm started")
                        else:
                            print ("Invalid alarm already on, see overview for status")
                    else:
                        print ("Invalid alarm needs to be set, see start help or overview for status")       
                else:
                    print ("Invalid number of values for start alarm please see start help")
            #help option
            elif option == "help":
                print ("Will start lights or alarm")
                print ("Options:")
                print ("\tlight\n\t\tWill start the light with set period (seconds)")
                print ("\talarm\n\t\tWill start the alarm with set (start, end) time")
            else:
                print ("Invalid option please see start help")

        #stop command
        if command == "stop":
            #light option
            if option == "light":
                if light_state:
                    light_state = False
                else:
                    print ("Invalid light already off, see overview for status")
            #alarm option
            elif option == "alarm":
                if alarm_state:
                    alarm_state = False
                else:
                    print ("Invalid alarm already off, see overview for status")
            #help option
            elif option == "help":
                print ("Will stop lights or alarm")
                print ("Options:")
                print ("\tlight\n\t\tWill stop the lights")
                print ("\talarm\n\t\tWill stop the alarm")
            else:
                print ("Invalid option please see stop help")

        #change command
        elif command == "change":
            #light option
            if option == "light":
                if len(values) == 1:
                    valid = False
		    #Input cna be in time format
		    new_end_time = checkValidTime(values[0])
                    if checkDuration(values[0]):
                        new_duration = int(values[0])
                        valid = True
                    elif new_end_time:
                        new_duration = calculateDifference(new_end_time)
                        valid = new_duration > 0
                    if valid:
                        #restart light with new duration if necessary
                        if light_state:
                            light_state = False
                            time.sleep(sleep_delay)
                        light_duration = new_duration
                        light_state = True
                        print ("Light's duration changed to: " + str(light_duration))
                    else:
                        print ("Invalid value for light duration please see change help")
                else:
                    print ("Invalid number of values for change light please see change help")
            #alarm option
            elif option == "alarm":
                if len(values) == 2:
		    valid = True
                    if not checkValidTime(values[0]):
			print ("Invalid start time for change alarm please see change help")
			valid = False
		    if checkValidTime(values[1]):
			print ("Invalid end time for change alarm please see change help")
			valid = False
		    if valid:
			alarm_start = values[0]
			alarm_end = values[1]
			print (showAlarm())
                else:
                    print ("Invalid number of values for change alarm please see alarm help")
            #brightness option
            if option == "brightness":
                if len(values) == 1:
		    if checkBrightness(values[0]):
			light_brightness = int(values[0])
		    else:
			print ("Invalid value for change brightness please see change help")
                else:
                    print ("Invalid number of values for change brightness please see change help")
            #flux option
            elif option == "flux":
                if len(values) == 1:
		    if checkFlux(values[0]):
			light_flux = int(values[0])
		    else:
			print ("Invalid value for change brightness please see change help")
                else:
                    print ("Invalid number of values for change brightness please see change help")
            #help option
            elif option == "help":
                print ("Will change light duration, alarm (start, end) time, brightness, flux")
                print ("Options:")
                print ("\tlight <duration>\n\t\tWill change the light duration to the desired value, must be greater than zero (seconds)")
                print ("\talarm <start hour>:<start minute> <end hour>:<end minute>\n\t\tWill start the alarm after setting it to desired (start, end) time")
                print ("\brightness <value>\n\t\tWill change the brightness to the desired value, must be >= 0 and <= 255")
                print ("\flux <value>\n\t\tWill change the brightness fluctuation to the desired amount, must have brightness - flux >= 0 and brightness + flux <= 
255")
            else:
                print ("Invalid option please see change help")
                
        #save command
        elif command == "save":
            will_save = False

            #no option
            if not option:
                will_save = True
            #help option
            elif option == "help":
                print ("Will save program's values")
                print ("Options:")
                print ("\t\n\t\tWill save the program's values listed in overview to LED_Main.ini")
            else:
                print ("Invalid option please see save help")
            
            if will_save:
                print("Saving")
                saveConfig()
        
        #load command
        elif command == "load":
            #no option is default and will load
            will_load = not option
            
            #help option
            if option == "help":
                print ("Will load program's values")
                print ("Options:")
                print ("\t\n\t\tWill load the program's values listed in overview from LED_Main.ini")
            else:
                print ("Invalid option please see load help")
            if will_load:
                loadConfig()
        
        #overview command
        elif command == "overview":
            print ("Program State: " + str(program_state))
            print ("Light State: " + str(light_state))
            print ("Alarm State: " + str(alarm_state))
            print (showAlarm())
            print ("Light Duration: " + str(light_duration))
            print ("Light Cycles: " + str(light_cycles))
            print ("Light Brightness: " + str(light_brightness))
            print ("Light Flux: " + str(light_flux))

        #list command
        elif command == "list":
            print ("exit <options>")
            print ("start <options> <values>")
            print ("stop <options>")
            print ("change <options> <values>")
            print ("save")
            print ("load")
            print ("overview")
            print ("list")

        else:
            print ("Invalid command, type list for all valid commands")
            
        time.sleep(sleep_delay) #to reduce cpu load

#threaded lights
def runLight():
    global program_state
    global light_state
    
    while program_state:
        if light_state:
            startLights()
            endLights()
        else:
           time.sleep(sleep_delay)

#threaded alarm
def runAlarm():
    global program_state
    global alarm_state
    global alarm_start
    global alarm_end

    while program_state:
        if alarm_state:
            #if the current time == alarm_start
            if not calculateDifference(alarm_start):
                startAlarm(calculateDifference(alarm_start, alarm_end))
            else:
                time.sleep(sleep_delay*10)
        time.sleep(sleep_delay)

if __name__ == "__main__":
    pi = pigpio.pi()

    loadConfig()
    start_new_thread(runAlarm, ()) #third thread for alarm timer
    start_new_thread(runLight, ()) #second thread for light display
    runInput() #main thread checks input
         
    pi.stop()
