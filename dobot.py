import serial
import struct
import time
import threading
import warnings

from .message import Message
from .enums import PTPMode
from .enums.CommunicationProtocolIDs import CommunicationProtocolIDs
from .enums.ControlValues import ControlValues


class Dobot:

    def __init__(self, port, verbose=False):
        threading.Thread.__init__(self)

        self._on = True
        self.verbose = verbose
        self.lock = threading.Lock()
        self.ser = serial.Serial(port,
                                 baudrate=115200,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS)
        is_open = self.ser.isOpen()
        if self.verbose:
            print('pydobot: %s open' % self.ser.name if is_open else 'failed to open serial port')

        self._set_queued_cmd_start_exec()
        self._set_queued_cmd_clear()
        self._set_ptp_joint_params(200, 200, 200, 200, 10, 200, 200, 200)
        self._set_ptp_coordinate_params(velocity=200, acceleration=200)
        self._set_ptp_jump_params(20.0000, 200.000)             #SETS HEIGHT AND LIMIT PARAMETERS
        self._set_ptp_common_params(velocity=100, acceleration=100)
        self._get_pose()

    """
        Gets the current command index
    """
    def _get_queued_cmd_current_index(self):
        msg = Message()
        msg.id = CommunicationProtocolIDs.GET_QUEUED_CMD_CURRENT_INDEX
        response = self._send_command(msg)
        idx = struct.unpack_from('L', response.params, 0)[0]
        return idx

    """
        Gets the real-time pose of the Dobot
    """
    def _get_pose(self):
        msg = Message()
        msg.id = CommunicationProtocolIDs.GET_POSE
        response = self._send_command(msg)
        self.x = struct.unpack_from('f', response.params, 0)[0]
        self.y = struct.unpack_from('f', response.params, 4)[0]
        self.z = struct.unpack_from('f', response.params, 8)[0]
        self.r = struct.unpack_from('f', response.params, 12)[0]
        self.j1 = struct.unpack_from('f', response.params, 16)[0]
        self.j2 = struct.unpack_from('f', response.params, 20)[0]
        self.j3 = struct.unpack_from('f', response.params, 24)[0]
        self.j4 = struct.unpack_from('f', response.params, 28)[0]

        if self.verbose:
            print("pydobot: x:%03.1f \
                            y:%03.1f \
                            z:%03.1f \
                            r:%03.1f \
                            j1:%03.1f \
                            j2:%03.1f \
                            j3:%03.1f \
                            j4:%03.1f" %
                  (self.x, self.y, self.z, self.r, self.j1, self.j2, self.j3, self.j4))
        return response

    def _read_message(self):
        time.sleep(0.1)
        b = self.ser.read_all()
        if len(b) > 0:
            msg = Message(b)
            if self.verbose:
                print('pydobot: <<', msg)
            return msg
        return

    def _send_command(self, msg, wait=False):
        self.lock.acquire()
        self._send_message(msg)
        response = self._read_message()
        self.lock.release()

        if not wait:
            return response

        expected_idx = struct.unpack_from('L', response.params, 0)[0]
        if self.verbose:
            print('pydobot: waiting for command', expected_idx)

        while True:
            current_idx = self._get_queued_cmd_current_index()

            if current_idx != expected_idx:
                time.sleep(0.1)
                continue

            if self.verbose:
                print('pydobot: command %d executed' % current_idx)
            break

        return response

    def _send_message(self, msg):
        time.sleep(0.1)
        if self.verbose:
            print('pydobot: >>', msg)
        self.ser.write(msg.bytes())

    """
        Executes the CP Command
    """
    def _set_cp_cmd(self, x, y, z):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_CP_CMD
        msg.ctrl = ControlValues.THREE
        msg.params = bytearray(bytes([0x01]))
        msg.params.extend(bytearray(struct.pack('f', x)))
        msg.params.extend(bytearray(struct.pack('f', y)))
        msg.params.extend(bytearray(struct.pack('f', z)))
        msg.params.append(0x00)
        return self._send_command(msg)

    """
        Sets the status of the gripper
    """
    def _set_end_effector_gripper(self, enable=False):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_GET_END_EFFECTOR_GRIPPER
        msg.ctrl = ControlValues.THREE
        msg.params = bytearray([])
        msg.params.extend(bytearray([0x01]))
        if enable is True:
            msg.params.extend(bytearray([0x01]))
        else:
            msg.params.extend(bytearray([0x00]))
        return self._send_command(msg)

    """
        
    """
    def _set_end_effector_suction_cup(self, enable=False):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_GET_END_EFFECTOR_SUCTION_CUP
        msg.ctrl = ControlValues.THREE
        msg.params = bytearray([])
        msg.params.extend(bytearray([0x01]))
        if enable is True:
            msg.params.extend(bytearray([0x01]))
        else:
            msg.params.extend(bytearray([0x00]))
        return self._send_command(msg)
    
    """
        Sets the velocity ratio and the acceleration ratio in PTP mode
    """
    def _set_ptp_joint_params(self, v_x, v_y, v_z, v_r, a_x, a_y, a_z, a_r):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_GET_PTP_JOINT_PARAMS
        msg.ctrl = ControlValues.THREE
        msg.params = bytearray([])
        msg.params.extend(bytearray(struct.pack('f', v_x)))
        msg.params.extend(bytearray(struct.pack('f', v_y)))
        msg.params.extend(bytearray(struct.pack('f', v_z)))
        msg.params.extend(bytearray(struct.pack('f', v_r)))
        msg.params.extend(bytearray(struct.pack('f', a_x)))
        msg.params.extend(bytearray(struct.pack('f', a_y)))
        msg.params.extend(bytearray(struct.pack('f', a_z)))
        msg.params.extend(bytearray(struct.pack('f', a_r)))
        return self._send_command(msg)

    """
        Sets the velocity and acceleration of the Cartesian coordinate axes in PTP mode
    """
    def _set_ptp_coordinate_params(self, velocity, acceleration):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_GET_PTP_COORDINATE_PARAMS
        msg.ctrl = ControlValues.THREE
        msg.params = bytearray([])
        msg.params.extend(bytearray(struct.pack('f', velocity)))
        msg.params.extend(bytearray(struct.pack('f', velocity)))
        msg.params.extend(bytearray(struct.pack('f', acceleration)))
        msg.params.extend(bytearray(struct.pack('f', acceleration)))
        return self._send_command(msg)

    """
       Sets the lifting height and the maximum lifting height in JUMP mode
    """
    def _set_ptp_jump_params(self, jump, limit):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_GET_PTP_JUMP_PARAMS
        msg.ctrl = ControlValues.THREE
        msg.params = bytearray([])
        msg.params.extend(bytearray(struct.pack('f', jump)))
        msg.params.extend(bytearray(struct.pack('f', limit)))
        return self._send_command(msg)


    """
        Sets the velocity ratio, acceleration ratio in PTP mode
    """
    def _set_ptp_common_params(self, velocity, acceleration):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_GET_PTP_COMMON_PARAMS
        msg.ctrl = ControlValues.THREE
        msg.params = bytearray([])
        msg.params.extend(bytearray(struct.pack('f', velocity)))
        msg.params.extend(bytearray(struct.pack('f', acceleration)))
        return (self._send_command(msg)).params

    """
        Get and Set the Arm Orientation of the dobot
        Functions added by Shaik Abdullah
    """
    def _get_arm_orientation(self):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_GET_ARM_ORIENTATION
        msg.ctrl = ControlValues.ZERO 
        return self._send_command(msg)
    
    def _set_arm_orientation(self, orientation):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_GET_ARM_ORIENTATION
        msg.ctrl = ControlValues.THREE
        msg.params = bytearray([])
        if orientation is 'L':
            msg.params.extend(bytearray([0x00]))
        elif orientation is 'R':
            msg.params.extend(bytearray([0x01]))
        else:
            print('Arm Orientation is defined as L or R')
        return self._send_command(msg)
    
    """Clear all alarms, by SHAIK ABDULLAH"""

    def _Clear_All_Alarm_States(self):
        msg = Message()
        msg.id = 20
        msg.ctrl = 0x01
        return self._send_command(msg)
    """
        Executes PTP command
    """
    def _set_ptp_cmd(self, x, y, z, r, mode, wait):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_PTP_CMD
        msg.ctrl = ControlValues.THREE
        msg.params = bytearray([])
        msg.params.extend(bytearray([mode.value]))
        msg.params.extend(bytearray(struct.pack('f', x)))
        msg.params.extend(bytearray(struct.pack('f', y)))
        msg.params.extend(bytearray(struct.pack('f', z)))
        msg.params.extend(bytearray(struct.pack('f', r)))
        return self._send_command(msg, wait)

    """
        Clears command queue
    """
    def _set_queued_cmd_clear(self):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_QUEUED_CMD_CLEAR
        msg.ctrl = ControlValues.ONE
        return self._send_command(msg)

    """
        Start command
    """
    def _set_queued_cmd_start_exec(self):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_QUEUED_CMD_START_EXEC
        msg.ctrl = ControlValues.ONE
        return self._send_command(msg)

    """
        Wait command
    """
    def _set_wait_cmd(self, ms):
        msg = Message()
        msg.id = 110
        msg.ctrl = 0x03
        msg.params = bytearray(struct.pack('I', ms))
        return self._send_command(msg)

    """
        Stop command
    """
    def _set_queued_cmd_stop_exec(self):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_QUEUED_CMD_STOP_EXEC
        msg.ctrl = ControlValues.ONE
        return self._send_command(msg)

    def _get_eio_level(self, address):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_GET_EIO
        msg.ctrl = ControlValues.ZERO
        msg.params = bytearray([])
        msg.params.extend(bytearray([address]))
        return self._send_command(msg)

    def _set_eio_level(self, address, level):
        msg = Message()
        msg.id = CommunicationProtocolIDs.SET_GET_EIO
        msg.ctrl = ControlValues.ONE
        msg.params = bytearray([])
        msg.params.extend(bytearray([address]))
        msg.params.extend(bytearray([level]))
        return self._send_command(msg)

    def get_eio(self, addr):
        return self._get_eio_level(addr)

    def set_eio(self, addr, val):
        return self._set_eio_level(addr, val)

    def close(self):
        self._on = False
        self.lock.acquire()
        self.ser.close()
        if self.verbose:
            print('pydobot: %s closed' % self.ser.name)
        self.lock.release()

    def go(self, x, y, z, r=0.):
        warnings.warn('go() is deprecated, use move_to() instead')
        self.move_to(x, y, z, r)

    def move_to(self, x, y, z, r, wait=False):
        self._set_ptp_cmd(x, y, z, r, mode=PTPMode.MOVJ_XYZ, wait=wait)

    #function added by SHAIK ABDULLAH

    def move_to_jump(self, x, y, z, r, wait=False):
        self._set_ptp_cmd(x, y, z, r, mode=PTPMode.JUMP_XYZ, wait=wait)
    
    
    """
    def suck(self, enable):
        self._set_end_effector_suction_cup(enable)

    def grip(self, enable):
        self._set_end_effector_gripper(enable)
    
    """
    def suck(self, enable):
        self._set_eio_level(17,enable)
  
    def grip(self, enable):
        self._set_eio_level(18,not enable)
               
    #changed such and grip function, by Shaik Abdullah

    def speed(self, velocity=100., acceleration=100.):
        self._set_ptp_common_params(velocity, acceleration)
        self._set_ptp_coordinate_params(velocity, acceleration)

    def wait(self, ms):
        self._set_wait_cmd(ms)

    def pose(self):
        response = self._get_pose()
        x = struct.unpack_from('f', response.params, 0)[0]
        y = struct.unpack_from('f', response.params, 4)[0]
        z = struct.unpack_from('f', response.params, 8)[0]
        r = struct.unpack_from('f', response.params, 12)[0]
        j1 = struct.unpack_from('f', response.params, 16)[0]
        j2 = struct.unpack_from('f', response.params, 20)[0]
        j3 = struct.unpack_from('f', response.params, 24)[0]
        j4 = struct.unpack_from('f', response.params, 28)[0]
        return x, y, z, r, j1, j2, j3, j4
