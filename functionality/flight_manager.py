import logging
import socket
import sys
import threading
import time


from tools.Singleton import Singleton


class FlightManager(metaclass=Singleton):

    DEFAULT_DISTANCE = 20
    DEFAULT_SPEED = 10
    DEFAULT_ANGLE = 10
    DEFAULT_HEIGHT = 20

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
        self.response = None
        self.stop_event = threading.Event()
        self._response_thread = threading.Thread(
            target=self.receive_response,
            args=(self.stop_event,))
        self._response_thread.start()
        self.is_commanded = False

    def receive_response(self, stop_event):
        while not stop_event.is_set():
            try:
                self.response, ip = self.socket.recvfrom(3000)
                self.logger.info({'action': 'receive_response',
                                 'response': self.response})
            except socket.error as ex:
                self.logger.error({'action': 'receive_response',
                                  'ex': ex})
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

    def takeoff(self, event=None):
        return self.send_command('takeoff')

    def land(self, event=None):
        return self.send_command('land')

    def move(self, direction, distance):
        return self.send_command(f'{direction} {distance}')

    def up(self, distance=DEFAULT_DISTANCE, event=None):
        return self.move('up', distance=FlightManager.DEFAULT_DISTANCE)

    def down(self, distance=DEFAULT_DISTANCE, event=None):
        return self.move('down', distance=FlightManager.DEFAULT_DISTANCE)

    def left(self, distance=DEFAULT_DISTANCE, event=None):
        return self.move('left', distance=FlightManager.DEFAULT_DISTANCE)

    def right(self, distance=DEFAULT_DISTANCE, event=None):
        return self.move('right', distance=FlightManager.DEFAULT_DISTANCE)

    def forward(self, distance=DEFAULT_DISTANCE, event=None):
        return self.move('forward', distance=FlightManager.DEFAULT_DISTANCE)

    def back(self, distance=DEFAULT_DISTANCE, event=None):
        return self.move('back', distance=FlightManager.DEFAULT_DISTANCE)

    def set_speed(self, speed):
        return self.send_command(f'speed {speed}')

    def clockwise(self, degree=DEFAULT_ANGLE, event=None):
        return self.move('cw', FlightManager.DEFAULT_ANGLE)

    def counter_clockwise(self, degree=DEFAULT_ANGLE, event=None):
        return self.move('ccw', FlightManager.DEFAULT_ANGLE)

    def stop_move(self, event=None):
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
