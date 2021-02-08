import cv2
from PIL import ImageTk, Image
import socket
import tkinter
import threading


from functionality.flight_manager import FlightManager


class MainWindow(tkinter.Tk):

    # Some color patterns
    color1 = '#695958'
    color3 = '#C8EAD3'
    color4 = '#CFFFE5'
    color5 = '#CEDADA'

    def __init__(self):
        super().__init__()
        # Main Window Properties
        self.iconbitmap('images/icon.ico')
        self.geometry('600x600')
        self.resizable(False, False)
        self.config(bg=MainWindow.color5)
        self.title('Tello Drone Controller')

        # Widgets that could be referenced to
        self.host_ip_entry = None
        self.drone_ip_entry = None
        self.host_port_entry = None
        self.drone_port_entry = None
        self.connection_info_label = None
        self.disconnection_info_label = None
        self.connection_canvas = None

        self.connection_frame = None
        self.footer_frame = None
        self.drone = None
        self.controller_window = None
        self.connection_status = False
        self.controller_window_state = False

        self.stream_window = None

        self.build_connection_frame()
        self.build_footer_frame()

        self._displaying_thread = threading.Thread(target=self.display_stream, args=())

    def build_connection_frame(self):
        """Main frame widgets"""
        font1 = ('Arial', 10, 'bold italic')

        self.connection_frame = tkinter.LabelFrame(self, text='UDP Connection', bg=MainWindow.color3, font=font1, bd=5)
        self.host_ip_entry = tkinter.Entry(self.connection_frame)
        self.host_ip_entry.insert(0, socket.gethostbyname(socket.gethostname()))
        self.drone_ip_entry = tkinter.Entry(self.connection_frame)
        self.drone_ip_entry.insert(0, '192.168.10.1')
        self.host_port_entry = tkinter.Entry(self.connection_frame)
        self.host_port_entry.insert(0, '8889')
        self.drone_port_entry = tkinter.Entry(self.connection_frame)
        self.drone_port_entry.insert(0, '8889')

        host_ip_label = tkinter.Label(self.connection_frame, text='Enter Host IP', bg=MainWindow.color3)
        drone_ip_label = tkinter.Label(self.connection_frame, text='Enter Drone IP', bg=MainWindow.color3)
        host_port_label = tkinter.Label(self.connection_frame, text='Enter Host Port', bg=MainWindow.color3)
        drone_port_label = tkinter.Label(self.connection_frame, text='Enter Drone Port', bg=MainWindow.color3)

        self.connection_frame.pack(pady=10)
        self.host_ip_entry.grid(row=0, column=0, padx=5)
        self.drone_ip_entry.grid(row=0, column=1, padx=5)
        self.host_port_entry.grid(row=0, column=2, padx=5)
        self.drone_port_entry.grid(row=0, column=3, padx=5)

        host_ip_label.grid(row=1, column=0)
        drone_ip_label.grid(row=1, column=1)
        host_port_label.grid(row=1, column=2)
        drone_port_label.grid(row=1, column=3)

        connect_button = tkinter.Button(self.connection_frame, text='Connect!', command=self.connect)
        connect_button.grid(row=2, column=0, columnspan=4, sticky='we', pady=(10, 0), padx=10)
        self.connection_info_label = tkinter.Entry(self.connection_frame, bg=self.color3, width=50)
        self.connection_info_label.insert(0, 'Connection action result: ')
        self.connection_info_label.grid(row=3, column=0, padx=10, pady=(0, 10), columnspan=3, sticky='w')

        disconnect_button = tkinter.Button(self.connection_frame, text='Disconnect!', command=self.disconnect)
        disconnect_button.grid(row=4, column=0, columnspan=4, sticky='we', pady=(10, 0), padx=10)
        self.disconnection_info_label = tkinter.Entry(self.connection_frame, bg=self.color3, width=50)
        self.disconnection_info_label.insert(0, 'Disconnection action result: ')
        self.disconnection_info_label.grid(row=5, column=0, padx=10, pady=(0, 10), columnspan=3, sticky='w')

        connection_status_label = tkinter.Label(self.connection_frame, bg=self.color3, text='Connection status')
        connection_status_label.grid(row=6, column=0, columnspan=2, sticky='e')
        self.connection_canvas = tkinter.Canvas(self.connection_frame, bg=self.color3, width=20, height=20)
        self.connection_canvas.grid(row=6, column=2, sticky='w', pady=(0, 5))
        self.connection_canvas.create_oval(2, 2, 20, 20, fill='red', tag='light')

    def build_footer_frame(self):
        """Footer frame build"""
        self.footer_frame = tkinter.LabelFrame(self, bd=2, text='Application compatible with DJI Tello',
                                               labelanchor='se')
        self.footer_frame.pack()
        quit_button = tkinter.Button(self.footer_frame, text='Quit App', command=self.close_app)
        controller_button = tkinter.Button(self.footer_frame, text='Launch Controller',
                                           command=self.build_controller_window)
        but = tkinter.Button(self.footer_frame, text='Stream', command=self.build_video_window)

        but.pack()
        controller_button.pack()
        quit_button.pack()

    def close_app(self):
        if not self.controller_window_state:
            print(self.drone)
            self.destroy()

    def connect(self):
        """Establishing UDP connection with drone"""
        if not self.connection_status:
            try:
                self.drone = FlightManager(self.host_ip_entry.get(), int(self.host_port_entry.get()),
                                           self.drone_ip_entry.get(), int(self.drone_port_entry.get()))
                self.drone.send_command('command')
                self.drone.send_command('streamon')
            except OSError:
                self.connection_info_label.delete(0, tkinter.END)
                self.connection_info_label.insert(0, 'Connection action result: failed to connect!')
                self.disconnection_info_label.delete(0, tkinter.END)
                self.disconnection_info_label.insert(0, 'Disconnection action result: ')

            else:
                self.connection_status = True
                self.connection_info_label.delete(0, tkinter.END)
                self.connection_info_label.insert(0, 'Connection action result: successfully connected!')
                self.disconnection_info_label.delete(0, tkinter.END)
                self.disconnection_info_label.insert(0, 'Disconnection action result: ')
        else:
            self.connection_info_label.delete(0, tkinter.END)
            self.connection_info_label.insert(0, 'Connection action result: already connected!')
            self.disconnection_info_label.delete(0, tkinter.END)
            self.disconnection_info_label.insert(0, 'Disconnection action result: ')

        self.display_status()

    def disconnect(self):
        """Closing UDP connection with drone"""
        if self.connection_status:
            try:
                self.drone.stop_dc()
                self.drone = None
            except socket.error:
                self.disconnection_info_label.delete(0, tkinter.END)
                self.disconnection_info_label.insert(0, 'Disconnection action result: failed to disconnect!')
                self.connection_info_label.delete(0, tkinter.END)
                self.connection_info_label.insert(0, 'Connection action result:')
            else:
                self.connection_status = False
                self.disconnection_info_label.delete(0, tkinter.END)
                self.disconnection_info_label.insert(0, 'Disconnection action result: successfully disconnected!')
                self.connection_info_label.delete(0, tkinter.END)
                self.connection_info_label.insert(0, 'Connection action result:')
        else:
            self.disconnection_info_label.delete(0, tkinter.END)
            self.disconnection_info_label.insert(0, 'Disconnection action result: already disconnected!')
            self.connection_info_label.delete(0, tkinter.END)
            self.connection_info_label.insert(0, 'Connection action result:')
        self.display_status()

    def display_status(self):
        """Light bulb displaying connection status"""
        self.connection_canvas.delete('light')
        if self.connection_status:
            self.connection_canvas.create_oval(2, 2, 20, 20, fill='green', tag='light')
        else:
            self.connection_canvas.create_oval(2, 2, 20, 20, fill='red', tag='light')

    def build_controller_window(self):

        if not self.controller_window_state and self.connection_status:
            self.controller_window_state = True
            self.drone.set_speed(self.drone.speed)

            self.controller_window = ControllerWindow(master=self)
            self.controller_window.protocol('WM_DELETE_WINDOW', self.close_controller)

    def close_controller(self):
        self.controller_window_state = False
        self.controller_window.destroy()

    def build_video_window(self):
        self.drone.video_handler = cv2.VideoCapture('udp://@0.0.0.0:11111')
        self.drone.video_handler.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.drone.video_state = True

        # Start displaying thread
        self._displaying_thread.start()

    def display_stream(self):
        while True:
            try:
                cv2.imshow('VideoStream', self.drone.frame)
            except Exception as e:
                print(e)
                continue
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.drone.video_state = False


class ControllerWindow(tkinter.Toplevel):

    def __init__(self, master=None):
        super().__init__(master=master)
        self.title('Controller Window')
        self.state = False
        # Controller Window frames
        self.c_w_main_frame = None
        self.c_w_footer_frame = None

        # Widgets
        self.buttons = {}
        self.img = {}

        # Objects
        self.drone = FlightManager()
        self.build_main_frame()

    def build_main_frame(self):
        repeat_interval = 1000
        repeat_delay = 100
        self.c_w_main_frame = tkinter.Frame(self)
        self.c_w_main_frame.pack()

        self.buttons['speed'] = tkinter.Scale(self.c_w_main_frame, from_=10, to=100, tickinterval=10.0, resolution=1.0,
                                              orient=tkinter.HORIZONTAL)
        self.buttons['speed'].bind('<ButtonRelease-1>', lambda x: self.drone.set_speed(self.buttons['speed'].get()))

        self.img['takeoff'] = ControllerWindow.resize_photo('images/takeoff.png', 50, 50)
        self.buttons['takeoff'] = tkinter.Button(self.c_w_main_frame, image=self.img['takeoff'],
                                                 command=self.drone.takeoff)
        self.bind('<t>', self.drone.takeoff)

        self.img['land'] = ControllerWindow.resize_photo('images/land.png', 50, 50)
        self.buttons['land'] = tkinter.Button(self.c_w_main_frame, image=self.img['land'],
                                              command=self.drone.land)
        self.bind('<l>', self.drone.land)

        self.img['back'] = ControllerWindow.resize_photo('images/arrow_down.png', 50, 50)
        self.buttons['back'] = tkinter.Button(self.c_w_main_frame, image=self.img['back'],
                                              command=lambda: self.drone.send_backward(self.buttons['speed'].get()),
                                              repeatinterval=repeat_interval, repeatdelay=repeat_delay)
        self.bind('<s>', lambda x: self.drone.send_backward(self.buttons['speed'].get()))
        self.bind('<KeyRelease-s>', self.drone.send_stop)
        self.buttons['back'].bind('<ButtonRelease-1>', self.drone.send_stop)

        self.img['left'] = ControllerWindow.resize_photo('images/arrow_left.png', 50, 50)
        self.buttons['left'] = tkinter.Button(self.c_w_main_frame, image=self.img['left'],
                                              command=lambda: self.drone.send_left(self.buttons['speed'].get()),
                                              repeatinterval=repeat_interval, repeatdelay=repeat_delay)
        self.bind('<a>', lambda x: self.drone.send_left(self.buttons['speed'].get()))
        self.bind('<KeyRelease-a>', self.drone.send_stop)
        self.buttons['left'].bind('<ButtonRelease-1>', self.drone.send_stop)

        self.img['right'] = ControllerWindow.resize_photo('images/arrow_right.png', 50, 50)
        self.buttons['right'] = tkinter.Button(self.c_w_main_frame, image=self.img['right'],
                                               command=lambda: self.drone.send_right(self.buttons['speed'].get()),
                                               repeatinterval=repeat_interval, repeatdelay=repeat_delay)
        self.bind('<d>', lambda x: self.drone.send_right(self.buttons['speed'].get()))
        self.bind('<KeyRelease-d>', self.drone.send_stop)
        self.buttons['right'].bind('<ButtonRelease-1>', self.drone.send_stop)

        self.img['forward'] = ControllerWindow.resize_photo('images/arrow_up.png', 50, 50)
        self.buttons['forward'] = tkinter.Button(self.c_w_main_frame, image=self.img['forward'],
                                                 command=lambda: self.drone.send_forward(self.buttons['speed'].get()),
                                                 repeatinterval=repeat_interval,
                                                 repeatdelay=repeat_delay)
        self.bind('<w>', lambda x: self.drone.send_forward(self.buttons['speed'].get()))
        self.bind('<KeyRelease-w>', self.drone.send_stop)
        self.buttons['forward'].bind('<ButtonRelease-1>', self.drone.send_stop)

        self.img['rotate'] = ControllerWindow.resize_photo('images/clockwise.png', 50, 50)
        self.buttons['rotate'] = tkinter.Button(self.c_w_main_frame, image=self.img['rotate'],
                                                command=lambda: self.drone.send_left_yaw(self.buttons['speed'].get()),
                                                repeatinterval=repeat_interval, repeatdelay=repeat_delay)
        self.bind('<Right>', lambda x: self.drone.send_left_yaw(self.buttons['speed'].get()))
        self.bind('<KeyRelease-Right>', self.drone.send_stop)
        self.buttons['rotate'].bind('<ButtonRelease-1>', self.drone.send_stop)

        self.img['c_rotate'] = ControllerWindow.resize_photo('images/c_clockwise.png', 50, 50)
        self.buttons['c_rotate'] = tkinter.Button(self.c_w_main_frame, image=self.img['c_rotate'],
                                                  command=lambda: self.drone.send_right_yaw(self.buttons['speed'].get()),
                                                  repeatinterval=repeat_interval, repeatdelay=repeat_delay)
        self.bind('<Left>', lambda x: self.drone.send_right_yaw(self.buttons['speed'].get()))
        self.bind('<KeyRelease-Left>', self.drone.send_stop)
        self.buttons['c_rotate'].bind('<ButtonRelease-1>', self.drone.send_stop)

        self.img['up'] = ControllerWindow.resize_photo('images/rarrow_up.png', 50, 50)
        self.buttons['up'] = tkinter.Button(self.c_w_main_frame, image=self.img['up'],
                                            command=lambda: self.drone.send_up(self.buttons['speed'].get()),
                                            repeatinterval=repeat_interval, repeatdelay=repeat_delay)
        self.bind('<Up>', lambda x: self.drone.send_up(self.buttons['speed'].get()))
        self.bind('<KeyRelease-Up>', self.drone.send_stop)
        self.buttons['up'].bind('<ButtonRelease-1>', self.drone.send_stop)

        self.img['down'] = ControllerWindow.resize_photo('images/rarrow_down.png', 50, 50)
        self.buttons['down'] = tkinter.Button(self.c_w_main_frame, image=self.img['down'],
                                              command=lambda: self.drone.send_down(self.buttons['speed'].get()),
                                              repeatinterval=repeat_interval, repeatdelay=repeat_delay)
        self.bind('<Down>', lambda x: self.drone.send_down(self.buttons['speed'].get()))
        self.bind('<KeyRelease-Down>', self.drone.send_stop)
        self.buttons['down'].bind('<ButtonRelease-1>', self.drone.send_stop)

        self.buttons['forward'].grid(row=0, column=0, columnspan=2, pady=5, padx=10)
        self.buttons['left'].grid(row=1, column=0, padx=5)
        self.buttons['right'].grid(row=1, column=1)
        self.buttons['back'].grid(row=2, column=0, columnspan=2, pady=5, padx=10)

        self.buttons['up'].grid(row=0, column=2, columnspan=2, padx=(100, 0))
        self.buttons['rotate'].grid(row=1, column=2, padx=(110, 5))
        self.buttons['c_rotate'].grid(row=1, column=3, padx=(0, 5))
        self.buttons['down'].grid(row=2, column=2, columnspan=2, padx=(100, 0))

        self.buttons['speed'].grid(row=3, column=0, columnspan=4, sticky='we')
        tkinter.Label(self.c_w_main_frame, text='Speed').grid(row=4, column=0, columnspan=4, sticky='we')

        self.buttons['takeoff'].grid(row=5, column=0, columnspan=2, pady=5, padx=10)
        self.buttons['land'].grid(row=5, column=2, columnspan=2, padx=(100, 0))
        tkinter.Label(self.c_w_main_frame, text='Takeoff').grid(row=6, column=0, columnspan=2, pady=5, padx=10)
        tkinter.Label(self.c_w_main_frame, text='Land').grid(row=6, column=2, columnspan=2, pady=5, padx=(100, 0))

    def build_footer_frame(self):
        self.c_w_footer_frame = tkinter.Frame(self)
        self.c_w_main_frame.pack()
        self.buttons['quit'] = tkinter.Button(self.c_w_footer_frame, text='Quit Controller',
                                              command=self.close_controller)
        self.buttons['quit'].pack()

    @staticmethod
    def resize_photo(path, width, height):
        img = Image.open(path)
        img = img.resize((width, height), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        return img

    def close_controller(self):
        self.destroy()
