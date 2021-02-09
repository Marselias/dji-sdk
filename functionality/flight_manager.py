import cv2
import logging
import numpy as np
import os
import signal
import socket
import sys
import subprocess
import threading
import time


from tools.Singleton import Singleton


class FlightManager(metaclass=Singleton):

    DEFAULT_DISTANCE = 20
    DEFAULT_SPEED = 10
    DEFAULT_ANGLE = 10

    def __init__(self, host_ip='192.168.10.2', host_port=8889,
                 drone_ip='192.168.10.1', drone_port=8889, default_speed=DEFAULT_SPEED):
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        self.logger = logging.getLogger(__name__)
        self.host_ip = host_ip
        self.host_port = host_port
        self.drone_ip = drone_ip
        self.drone_port = drone_port
        self.drone_address = (drone_ip, drone_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host_ip, self.host_port))
        self.speed = default_speed

        # Response Part
        self.response = None
        self.stop_event = threading.Event()
        self._response_thread = threading.Thread(target=self.receive_response, args=(self.stop_event,))
        self._response_thread.start()

        # VideoStream Part
        self.video_state = False
        self.video_handler = None
        self.frame = None
        self._receive_thread = threading.Thread(target=self.receive_stream, args=(self.stop_event,))
        self._receive_thread.start()

    def receive_response(self, stop_event):
        while not stop_event.is_set():
            try:
                self.response, ip = self.socket.recvfrom(3000)
                self.logger.info({'action': 'receive_response', 'response': self.response})
            except socket.error as ex:
                self.logger.error({'action': 'receive_response', 'ex': ex})
                print(self.response)
                break

    def __dell__(self):
        self.stop()

    def stop(self):
        self.stop_event.set()
        retry = 0
        while self._response_thread.is_alive():
            time.sleep(0.3)
            if retry > 30:
                break
            retry += 1
        self.socket.close()
        print('STOPPED')

    def stop_dc(self):
        self.stop_event.set()
        retry = 0
        while self._response_thread.is_alive():
            time.sleep(0.3)
            if retry > 2:
                break
            retry += 1
        self.socket.close()
        print('STOPPED')

    def send_command(self, command):
        self.logger.info({'action': 'send_command', 'command': command})
        self.socket.sendto(command.encode('utf-8'), self.drone_address)

        retry = 0
        while self.response is None:
            time.sleep(0.3)
            if retry > 3:
                break
            retry += 1

        if self.response is None:
            response = None
        else:
            response = self.response.decode('utf-8')
        self.response = None
        return response

    def send_without_response(self, command):
        self.socket.sendto(command.encode('utf-8'), self.drone_address)

    def takeoff(self):
        return self.send_command('takeoff')

    def land(self):
        return self.send_command('land')

    def move(self, direction, distance):
        return self.send_command(f'{direction} {distance}')

    def up(self, distance=DEFAULT_DISTANCE):
        return self.move('up', distance)

    def down(self, distance=DEFAULT_DISTANCE):
        return self.move('down', distance)

    def left(self, distance=DEFAULT_DISTANCE):
        return self.move('left', distance)

    def right(self, distance=DEFAULT_DISTANCE):
        return self.move('right', distance)

    def forward(self, distance=DEFAULT_DISTANCE):
        return self.move('forward', distance)

    def back(self, distance=DEFAULT_DISTANCE):
        return self.move('back', distance)

    def set_speed(self, speed):
        return self.send_command(f'speed {speed}')

    def clockwise(self, degree=DEFAULT_ANGLE):
        return self.move('cw', degree)

    def counter_clockwise(self, degree=DEFAULT_ANGLE):
        return self.move('ccw', degree)

    def stop_move(self):
        print('stopped')
        return self.send_command('stop')

    def send_rc_abcd(self, a, b, c, d):
        self.send_without_response(f'rc {a} {b} {c} {d}')

    def send_left(self, speed, event=None):
        self.send_rc_abcd(-speed, 0, 0, 0)

    def send_right(self, speed, event=None):
        self.send_rc_abcd(speed, 0, 0, 0)

    def send_forward(self, speed, event=None):
        self.send_rc_abcd(0, speed, 0, 0)

    def send_backward(self, speed, event=None):
        self.send_rc_abcd(0, -speed, 0, 0)

    def send_up(self, speed, event=None):
        self.send_rc_abcd(0, 0, speed, 0)

    def send_down(self, speed, event=None):
        self.send_rc_abcd(0, 0, -speed, 0)

    def send_left_yaw(self, speed, event=None):
        self.send_rc_abcd(0, 0, 0, speed)

    def send_right_yaw(self, speed, event=None):
        self.send_rc_abcd(0, 0, 0, -speed)

    def send_stop(self, event=None):
        self.send_rc_abcd(0, 0, 0, 0)

    def receive_stream(self, stop_event):
        while not stop_event.is_set():
            if self.video_state:
                try:
                    ret, self.frame = self.video_handler.read()
                except Exception as e:
                    print(e)
