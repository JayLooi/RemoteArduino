import tkinter as tk
from tkinter import Tk, Frame, Button, PhotoImage, Label, Entry, Scrollbar, Text, Canvas, filedialog, messagebox, ttk
import threading
import os
from ArduinoRemote import ArduinoRemote
from time import time, sleep
import random
import string


def pathJoinCwd(file):
    return os.path.join(os.getcwd(), file)


def randomId(length):
    return ''.join([random.choice(string.ascii_letters + string.digits) for i in range(length)])


APP_ICON = pathJoinCwd('res/icon.png')
CONNECTION_STATUS_IMG = pathJoinCwd('res/cloud_16.png')
DEVICE_STATUS_IMG = pathJoinCwd('res/device_16.png')
OTA_IMG = pathJoinCwd('res/ota_24.png')
DEBUG_IMG = pathJoinCwd('res/debug_24.png')
SETTING_IMG = pathJoinCwd('res/settings_24.png')
UPLOAD_BUTTON_IMG = pathJoinCwd('res/arrow_16.png')
REFRESH_IMG = pathJoinCwd('res/refresh.png')


class App(Tk):
    def __init__(self, icon='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = ''
        self.port = None
        self.username = ''
        self.pw = ''
        self.target_device = ''
        self.rx_topic = ''          # subscribe topic
        self.tx_topic = ''          # publish topic
        self.status_topic = ''
        self.client_id = 'Arduino-Remote-' + randomId(8)
        self.stream_fp = os.path.join(os.getcwd(), 'temp/parsed_hex')
        
        self.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.iconphoto(False, PhotoImage(file=icon))
        self.minsize(720, 540)
        self.geometry('720x540')
        self.side_pane = Frame(self, bg='#d9d9d9')
        self.side_pane.pack(side='left', fill='both')
        self.status_frame = Frame(self.side_pane, padx=5, bg='#d9d9d9')
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.pack(pady=10, anchor='w')
        self.menu_frame = Frame(self.side_pane, bg='#d9d9d9')
        self.menu_frame.pack(pady=30)
        self.selection_ind = Frame(self.menu_frame, bg='#00d5ff', width=5, height=15)
        self.action_pane = Frame(self, bg='white', width=620)
        self.action_pane.pack(side='left', fill='both', expand=True)

        # Side pane
        self.refresh_img = PhotoImage(file=REFRESH_IMG)
        self.refresh_button = Button(self.status_frame, bg='#d9d9d9', relief='flat', bd=0, activebackground='#d9d9d9', image=self.refresh_img, command=self.refreshConnection)
        self.refresh_button.grid(row=0, column=0, sticky='nsw', padx=5, pady=10)
        self.conn_status_frame = Frame(self.status_frame, bg='#d9d9d9')
        self.conn_status_frame.grid(row=1, column=0, sticky='nsew')
        self.conn_status_img = PhotoImage(file=CONNECTION_STATUS_IMG)
        self.conn_status_img_label = Label(self.conn_status_frame, bg='#d9d9d9', image=self.conn_status_img)
        self.conn_status_img_label.pack(side='left', padx=5)
        self.connection_status = tk.StringVar(self, value='Disconnected')
        self.connection_status_label = Label(self.conn_status_frame, bg='#d9d9d9', fg='#ff0000', textvariable=self.connection_status)
        self.connection_status_label.pack(side='left')

        self.dev_status_frame = Frame(self.status_frame, bg='#d9d9d9')
        self.dev_status_frame.grid(row=2, column=0, sticky='nsew')
        self.dev_status_img = PhotoImage(file=DEVICE_STATUS_IMG)
        self.dev_status_img_label = Label(self.dev_status_frame, bg='#d9d9d9', image=self.dev_status_img)
        self.dev_status_img_label.pack(side='left', padx=5)
        self.device_status = tk.StringVar(self, value='Unknown')
        self.device_status_label = Label(self.dev_status_frame, bg='#d9d9d9', fg='#ff0000', textvariable=self.device_status)
        self.device_status_label.pack(side='left')
        
        self.OTA_button = CustomButton(master=self.menu_frame, width=120, height=60,
                                       img_fp=OTA_IMG, text='OTA', compound='left',
                                       anchor='w', indicator=self.selection_ind, padx=20)
        self.debug_button = CustomButton(master=self.menu_frame, width=120, height=60,
                                         img_fp=DEBUG_IMG, text='Log', compound='left',
                                         anchor='w', indicator=self.selection_ind, padx=20)
        self.setting_button = CustomButton(master=self.menu_frame, width=120, height=60,
                                           img_fp=SETTING_IMG, text='Setting', compound='left',
                                           anchor='w', indicator=self.selection_ind, padx=20)
        
        self.selection_ind.tkraise()       # Bring selection indicator forward

        # Action pane
        
        ## -> OTA frame
        self.OTA_frame = OTAFrame(main_win=self, master=self.action_pane, button=self.OTA_button, bg='#fbfbfb')

        ## -> Debug frame
        self.debug_frame = DebugFrame(main_win=self, master=self.action_pane, button=self.debug_button, bg='#fbfbfb')

        ## -> Setting frame
        self.setting_frame = SettingFrame(main_win=self, master=self.action_pane, button=self.setting_button, bg='#fbfbfb')

        self.remote = ArduinoRemote(self.stream_fp, self.client_id, self.host, self.port, self.username, self.pw, self.tx_topic, self.rx_topic,
                                    self.status_topic, self.connectionStatusLog, self.deviceStatusLog, self.OTA_frame.log, self.debug_frame.log)

    def refreshConnection(self):
        self.remote._connect()

    def connectionStatusLog(self, log):
        self.connection_status.set(log)
        self.connection_status_label['fg'] = '#11d438' if self.remote.is_connected else '#ff0000'

    def deviceStatusLog(self, log):
        self.device_status.set(log)
        if log.strip().lower() == 'online':
            self.device_status_label['fg'] = '#11d438'

        else:
            self.remote.debugStop()
            self.debug_frame.debug_button['text'] = 'Debug'
            self.device_status_label['fg'] = '#ff0000'
            

    def onClosing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()


class CustomButton(Button):
    count = 0
    def __init__(self, master, height, width, bd=0, bg='#d9d9d9', activebackground='#e3e3e3',
                 relief='flat',img_fp=None, indicator=None, *args, **kwargs):
        self.button_frame = Frame(master, height=height, width=width)
        self.button_frame.pack_propagate(0)
        self.button_frame.pack()
        if img_fp:
            self.img = PhotoImage(file=img_fp)
            
        else:
            self.img = None

        super().__init__(self.button_frame, height=height, width=width, bd=bd, bg=bg, relief=relief,
                         activebackground=activebackground, image=self.img, *args, **kwargs)
        self.index = CustomButton.count
        CustomButton.count = CustomButton.count + 1
        self.bind('<Enter>', self.onEnter)
        self.bind('<Leave>', self.onLeave)
        self.indicator = indicator
        if self.indicator:
            self.indicator_callback = lambda : self.indicator.place(relx=0, rely=0, x=self.indicator['width']/2,
                                                                    y=(self.index + 0.5)*(self['height']), anchor='center')
            self['command'] = self.indicator_callback
            self.indicator_callback()

        else:
            self.indicator_callback =lambda : None

        self.pack(anchor='n')

    def onEnter(self, e):
        self['bg'] = '#ededed'

    def onLeave(self, e):
        self['bg'] = '#d9d9d9'

    def setCallback(self, callback):
        self['command'] = lambda : (self.indicator_callback(), callback())


class ActionFrame(Frame):
    def __init__(self, main_win, button, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main = main_win
        self.button = button
        self.button.setCallback(lambda: self.tkraise())
        self.place(x=0, y=0, relwidth=1, relheight=1)


class OTAFrame(ActionFrame):
    def __init__(self, bg, *args, **kwargs):
        super().__init__(bg=bg, *args, **kwargs)
        self.hex_fp = tk.StringVar(self, value='')
        self.grid_columnconfigure(0, weight=1)
        self.style = ttk.Style()
        
        # First row
        self.first_row = Frame(self, height=50, bg=bg)
        self.first_row.grid(row=0, column=0, sticky='nsew')
        self.browsed_label = ttk.Entry(self.first_row, state='readonly', textvariable=self.hex_fp, width=50)
        self.browsed_label.pack(side='left', anchor='n', padx=10, pady=10, fill='x', expand=True)

        self.browse_hex_button = ttk.Button(self.first_row,  text='Browse', command=self.browseHexFile)
        self.browse_hex_button.pack(side='left', anchor='n', padx=10, pady=7)

        self.upload_button_img = PhotoImage(file=UPLOAD_BUTTON_IMG)
        self.upload_button = ttk.Button(self.first_row, image=self.upload_button_img, command=self.uploadHex)
        self.upload_button.pack(side='left', anchor='n', padx=10, pady=6)

        # Second row
        self.second_row = Frame(self, bg=bg)
        self.second_row.grid(row=1, column=0, sticky='nsew')
        self.ota_progress_bar = ttk.Progressbar(self.second_row, orient='horizontal', mode='determinate')
        self.style.layout('upload.Horizontal.TProgressbar',
                          [*self.style.layout('upload.Horizontal.TProgressbar'),
                           ('Horizontal.TProgressbar.label', {'sticky': ''})])
        self.style.configure('upload.Horizontal.TProgressbar', text='')
        self.ota_progress_bar['style'] = 'upload.Horizontal.TProgressbar'
        self.ota_progress_bar.pack(side='left', padx=10, pady=10, anchor='w', fill='x', expand=True)

        # Third row
        self.grid_rowconfigure(2, weight=1)
        self.third_row = Frame(self, bg='white', bd=0, highlightbackground='#f0f0f0', highlightcolor='#f0f0f0', highlightthickness=1)
        self.third_row.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
        self.log_scrollbar = Scrollbar(self.third_row, orient='vertical')
        self.log_scrollbar.pack(side='right', anchor='w', fill='y')
        self.log_text_box = Text(self.third_row, relief='solid', bd=0, yscrollcommand=self.log_scrollbar.set, padx=5)
        self.log_text_box.pack(side='left', anchor='w', fill='both', expand=True)
        self.log_text_box.bind('<Key>', lambda key: 'break')
        self.log_scrollbar['command'] = self.log_text_box.yview

    def browseHexFile(self):
        self.hex_fp.set(filedialog.askopenfilename(title='Select hex file', filetypes=[('Hex files', '*.hex')]))

    def log(self, log):
        self.log_text_box.insert('end', log + '\n')
        self.log_text_box.see('end')

    def uploadHex(self):
        self.upload_button['state'] = 'disabled'
        self.browse_hex_button['state'] = 'disabled'
        self.main.debug_button['state'] = 'disabled'
        self.main.setting_button['state'] = 'disabled'
        self.main.refresh_button['state'] = 'disabled'
        self.style.configure('upload.Horizontal.TProgressbar', text='')
        self.ota_progress_bar['value'] = 0
        self.log_text_box.delete(1.0, 'end')
        fp = self.hex_fp.get()
        if os.path.isfile(fp):
            flasher = self.main.remote
            TIMEOUT = 5
            flasher.chooseHexFile(self.hex_fp.get())
            flasher.flashStart()
            self.main.debug_frame.debug_button['text'] = 'Debug'
            self.thread = threading.Thread(target=self.setTimeout, args=(TIMEOUT, ))
            self.thread.start()

        else:
            messagebox.showerror(title='Error', message='Invalid hex file!')
            self.upload_button['state'] = 'normal'
            self.browse_hex_button['state'] = 'normal'
            self.main.debug_button['state'] = 'normal'
            self.main.setting_button['state'] = 'normal'
            self.main.refresh_button['state'] = 'normal'

    # set timeout - if no response from device, then end the process.
    def setTimeout(self, timeout):
        flasher = self.main.remote
        start_time = time()
        self.ota_progress_bar['mode'] = 'indeterminate'
        self.ota_progress_bar['maximum'] = 50
        self.ota_progress_bar['value'] = 0
        self.ota_progress_bar.start()
        self.log('[INFO] Preparing to flash %s.' % self.main.target_device)
        while 1:
            sleep(0.01)
            self.update_idletasks()
            if flasher.is_flashing or (time() - start_time) >= timeout:
                break
        
        self.ota_progress_bar.stop()
        self.ota_progress_bar['value'] = 0
        self.ota_progress_bar['mode'] = 'determinate'
        self.ota_progress_bar['maximum'] = flasher.n_of_bytes
        if flasher.is_flashing:
            start_time = time()
            prev_sent_bytes = 0
            update_time = time()
            while flasher.is_flashing:
                self.ota_progress_bar['value'] = flasher.sent_bytes
                self.style.configure('upload.Horizontal.TProgressbar', text='%.2f%%' % ((flasher.sent_bytes / flasher.n_of_bytes) * 100))
                is_timeout = time() - update_time > 3
                sleep(0.001)
                if (flasher.sent_bytes != prev_sent_bytes ) and not is_timeout:
                    prev_sent_bytes = flasher.sent_bytes
                    update_time = time()

                elif is_timeout:
                    self.log('[FAILED] Timeout in waiting response from the device!')
                    flasher.is_flashing = False

                self.update_idletasks()

            end_time = time()
            self.log('[INFO] Time elapsed: %.2f s' % (end_time - start_time))

        else:
            self.log('[FAILED] Not response from device!')

        flasher.resetOnMessageCallback()
        flasher.hex_stream_f.close()
        
        self.upload_button['state'] = 'normal'
        self.browse_hex_button['state'] = 'normal'
        self.main.debug_button['state'] = 'normal'
        self.main.setting_button['state'] = 'normal'
        self.main.refresh_button['state'] = 'normal'


class DebugFrame(ActionFrame):
    def __init__(self, bg, *args, **kwargs):
        super().__init__(bg=bg, *args, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        # First row
        self.first_row = Frame(self, bg=bg)
        self.first_row.grid(row=0, column=0, padx=10, sticky='nsew')
        self.frame_label = Label(self.first_row, text='Debug Log', bg=bg, font=('Calibri', 12))
        self.frame_label.pack(side='top', anchor='w', pady=10)

        # Second row
        self.grid_rowconfigure(1, weight=1)
        self.second_row = Frame(self, bg='white', bd=0, highlightbackground='#f0f0f0', highlightcolor='#f0f0f0', highlightthickness=1)
        self.second_row.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        self.log_scrollbar = Scrollbar(self.second_row, orient='vertical')
        self.log_scrollbar.pack(side='right', anchor='w', fill='y')
        self.log_text_box = Text(self.second_row, relief='solid', bd=0, yscrollcommand=self.log_scrollbar.set, padx=5)
        self.log_text_box.pack(side='left', anchor='w', fill='both', expand=True)
        self.log_text_box.bind('<Key>', lambda key: 'break')
        self.log_scrollbar['command'] = self.log_text_box.yview

        # Third row
        self.third_row = Frame(self, height=50, bg=bg)
        self.third_row.grid(row=2, column=0, pady=10, sticky='nsew')

        self.debug_button = ttk.Button(self.third_row,  text='Debug', command=self.toggleDebug) 
        self.debug_button.pack(side='left', anchor='n', padx=10)

        self.clearlog_button = ttk.Button(self.third_row, text='Clear', command=self.clearLog)
        self.clearlog_button.pack(side='left', anchor='n', padx=10)

        self.reset_button = ttk.Button(self.third_row, text='Reset', command=lambda: self.main.remote.resetDevice())
        self.reset_button.pack(side='right', padx=10)
        
        self.baudrate = tk.IntVar(self, value=115200)
        self.baudrate_list = (300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 74880, 115200, 230400, 250000, 500000, 1000000, 2000000)
        self.baudrate_menu = ttk.Combobox(self.third_row, state='readonly', textvariable=self.baudrate, values=self.baudrate_list)
        self.baudrate_menu.pack(side='right', padx=10)
        self.baudrate_menu.bind('<<ComboboxSelected>>', lambda e: self.main.remote.updateBaudrate(self.baudrate.get()))

    def toggleDebug(self):
        debugger = self.main.remote
        if debugger.is_debugging:
            debugger.debugStop()
            self.debug_button['text'] = 'Debug'

        else:
            debugger.debugStart()
            self.debug_button['text'] = 'Stop'

    def clearLog(self):
        self.log_text_box.delete(1.0, 'end')

    def log(self, log):
        self.log_text_box.insert('end', log)
        self.log_text_box.see('end')


class CustomEntry(ttk.Entry):
    row = 0
    def __init__(self, master, bg, label, entry_prefix=None, *args, **kwargs):
        row = CustomEntry.row
        CustomEntry.row = CustomEntry.row + 1
        self.label = Label(master=master, text=label, bg=bg)
        self.label.grid(row=row, column=0, sticky='nse', padx=10, pady=10)

        if entry_prefix is None:
            super().__init__(master=master, *args, **kwargs)
            self.grid(row=row, column=1, sticky='nsew', padx=10, pady=10)

        else:
            self.entry_frame = Frame(master=master, bg=bg)
            self.entry_frame.grid(row=row, column=1, sticky='nsew', padx=10, pady=10)
            self.entry_prefix = ttk.Entry(self.entry_frame, textvariable=entry_prefix, state='readonly')
            self.entry_prefix.pack(side='left', anchor='w')
            Label(self.entry_frame, text='/', bg=bg).pack(side='left')
            super().__init__(master=self.entry_frame, *args, **kwargs)
            self.pack(side='left', expand=True, fill='x')


class SettingFrame(ActionFrame):
    def __init__(self, bg, *args, **kwargs):
        super().__init__(bg=bg, *args, **kwargs)
        self.mqtt_config_fp = os.path.join(os.getcwd(), 'MQTTConfig.cfg')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)


        # Setting frame
        self.setting_frame = Frame(self, bg=bg)
        self.setting_frame.grid(row=0, column=0, pady=20, sticky='nsew')
        self.setting_frame.grid_columnconfigure(1, weight=1)

        ## -> Host
        self.host = tk.StringVar(self, value='')
        self.host_entry = CustomEntry(master=self.setting_frame, bg=bg, label='Host', textvariable=self.host)

        ## -> Port
        self.port = tk.IntVar(self)
        self.port_entry = CustomEntry(master=self.setting_frame, bg=bg, label='Port', textvariable=self.port)

        ## -> Username
        self.username = tk.StringVar(self, value='')
        self.username_entry = CustomEntry(master=self.setting_frame, bg=bg, label='Username', textvariable=self.username)

        ## -> Password
        self.pw = tk.StringVar(self, value='')
        self.pw_entry = CustomEntry(master=self.setting_frame, bg=bg, label='Password', textvariable=self.pw, show='\u2022')

        ## -> Target device
        self.target_device = tk.StringVar(self, value='')
        self.tDevice_entry = CustomEntry(master=self.setting_frame, bg=bg, label='Target Device', textvariable=self.target_device)

        ## -> Rx topic
        self.rx_topic = tk.StringVar(self, value='')
        self.rx_entry = CustomEntry(master=self.setting_frame, bg=bg, label='Rx Topic', entry_prefix=self.target_device, textvariable=self.rx_topic)

        ## -> Tx topic
        self.tx_topic = tk.StringVar(self, value='')
        self.tx_entry = CustomEntry(master=self.setting_frame, bg=bg, label='Tx Topic', entry_prefix=self.target_device, textvariable=self.tx_topic)

        ## -> Device status topic
        self.status_topic = tk.StringVar(self, value='')
        self.status_entry = CustomEntry(master=self.setting_frame, bg=bg, label='Device Status Topic', entry_prefix=self.target_device, textvariable=self.status_topic)        

        self.readConfig()

        # Button frame
        self.button_frame = Frame(self, bg=bg)
        self.button_frame.grid(row=1, column=0, pady=20, sticky='nsew')

        ## Apply settings button
        self.apply_button = ttk.Button(self.button_frame, text='Apply', command=self.apply)
        self.apply_button.pack(side='right', padx=10)

    def saveConfig(self):
        cfg_key_list = ('host', 'port', 'username', 'target_device', 'rx_topic', 'tx_topic', 'device_status_topic')
        cfg_value_list = (
            self.host.get(), 
            self.port.get(), 
            self.username.get(), 
            self.target_device.get(), 
            self.rx_topic.get(), 
            self.tx_topic.get(),
            self.status_topic.get()
        )

        with open(self.mqtt_config_fp, 'w+') as f:
            f.write('\n'.join(['%s=%s' % (k, v) for k, v in zip(cfg_key_list, cfg_value_list)]))

    def readConfig(self):
        if os.path.isfile(self.mqtt_config_fp):
            cfg_key_list = ('host', 'port', 'username', 'target_device', 'rx_topic', 'tx_topic', 'device_status_topic')
            cfg_dict = {k: '' for k in cfg_key_list}
            with open(self.mqtt_config_fp, 'r+') as f:
                config_list = f.readlines()
                for cfg in config_list:
                    key, value = [el.strip() for el in cfg.split('=')]
                    if key in cfg_key_list:
                        cfg_dict[key] = value

                self.host.set(cfg_dict['host'])
                self.port.set(int(cfg_dict['port']) if cfg_dict['port'].isdigit() else '')
                self.username.set(cfg_dict['username'])
                self.target_device.set(cfg_dict['target_device'])
                self.rx_topic.set(cfg_dict['rx_topic'])
                self.tx_topic.set(cfg_dict['tx_topic'])
                self.status_topic.set(cfg_dict['device_status_topic'])

                main = self.main
                main.host = self.host.get()
                main.port = self.port.get()
                main.username = self.username.get()
                main.pw = self.pw.get()
                main.target_device = self.target_device.get()
                main.rx_topic = main.target_device + '/' + self.rx_topic.get()
                main.tx_topic = main.target_device + '/' + self.tx_topic.get()
                main.status_topic = main.target_device + '/' + self.status_topic.get()

    def apply(self):
        self.saveConfig()
        self.main.debug_frame.debug_button['text'] = 'Debug'
        remote = self.main.remote
        remote.host = self.host.get()
        remote.port = self.port.get()
        remote.username = self.username.get()
        remote.pw = self.pw.get()
        remote.target_device = self.target_device.get()
        remote.tx_topic = remote.target_device + '/' + self.tx_topic.get()
        remote.rx_topic = remote.target_device + '/' + self.rx_topic.get()
        remote.status_topic = remote.target_device + '/' + self.status_topic.get()
        remote._connect()


app = App(icon=APP_ICON, className=' Remote Arduino')
app.mainloop()
