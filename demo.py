#THIS CODE WAS WRITTEN BY SHAIK ABDULLAH, (while working as a robotics intern at EcoOrbit AI Solutions Pvt. Ltd.)

from serial.tools import list_ports
from pydobot import Dobot

port = list_ports.comports()[0].device
device = Dobot(port=port, verbose=True)     #Establish Connection with the bot

print(device._get_arm_orientation())   #AA AA:3:50:0:00:206 here 00 means Left and 01:205 means right
device._set_arm_orientation('R')     #L is left and R is right arm orientation

device._Clear_All_Alarm_States()        #Clears all alarms
#device.speed(10000,10000)     #Under construction. Currently unnecessary
device._set_ptp_joint_params(100, 100, 100, 100, 100, 100, 100, 100)       #speeds of velocity along x, y, z, r axes acceleration along x, y, z, r axes Max=100, Min=0
device.grip(1)      #Turn ON air pump
device.suck(0)      # 0 for sucking in air, 1 for blowing out air

#device.move_to(159.7595, 14.5572, 233.5419, 71.5233, wait=True)     #decent initial position, move_to() uses shortest time path
device.move_to_jump(271.0673, -262.8100, 100, -24.8673, wait= True)  #parameters: x, y, z, r
#device._set_ptp_jump_params(20.0000, 200.000) #change these params to change height and limit values of jump. These are defalt values
device.move_to_jump(-97.0460, 353.3612, 200.3829, 128.9536, wait=True)

device.grip(0)      #Turn OFF air pump

device.close()