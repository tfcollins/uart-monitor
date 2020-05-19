from curses import wrapper
import curses.textpad
import curses
import time
import uart
import yaml
import os


def read_yaml(filename):
    """Process yaml into config"""
    if not os.path.exists(filename):
        raise Exception("YAML config file not found")

    stream = open(filename, "r")
    configs = yaml.safe_load(stream)
    stream.close()
    return configs["uarts"]


class monitor:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.stdscr.clear()

        addresses = read_yaml("config.yaml")

        readers = len(addresses)
        (self.windows, max_lines, width) = self.setup_windows(readers + 1)
        self.refresh_all()

        # Setup uart
        self.uarts = []
        for i in range(readers):
            self.windows[i].addstr(0, 2, "Monitoring: " + addresses[i])
            self.uarts.append(
                uart.uart(
                    window=self.windows[i],
                    max_lines=max_lines - 2,
                    address=addresses[i],
                )
            )
            self.uarts[i].start_log()

        self.windows[-1].addstr(0, 2, "User Input")
        # Split user window
        corner = readers * max_lines + max_lines // 2
        begin_x = 1
        win = curses.newwin(max_lines // 2, width, corner, begin_x)
        # win.box()
        self.windows.append(win)
        self.refresh_all()

    def __del__(self):
        # Cleanup UART
        for uart in self.uarts:
            uart.listen_thread_run = False
            uart.stop_log()

    def setup_windows(self, num_windows):
        height, width = self.stdscr.getmaxyx()
        windows = []
        height_win = height // num_windows
        corner = 0
        begin_x = 0
        height = 10
        for n in range(num_windows):
            win = curses.newwin(height_win, width, corner, begin_x)
            win.box()
            windows.append(win)
            corner = corner + height_win

        return windows, height_win, width

    def refresh_all(self):
        for win in self.windows:
            win.refresh()

    def write_to_all(self, string, y=0, x=0, add_box=False):
        for win in self.windows:
            if add_box:
                win.box()
            win.addstr(y, x, string)

    def write_to_all_uart(self, msg):
        for uart in self.uarts:
            uart._write_data(msg)

    def print_user_message(self, win):
        message = [
            "//// Commands ////",
            "--Quit: q",
            "--Send uart command: s <command>",
        ]
        for l in range(len(message)):
            win.addstr(l + 1, 1, message[l])
        win.refresh()

    def process_user_input(self, data):
        data = data.replace("User input: ", "")
        data = data.replace("\n", "")
        data = data.strip()
        e = 0
        arguments = []
        if len(data) > 1:
            if data[1] != " ":
                e = 1
        elif len(data) == 2:
            e = 1
        arguments = data.split(" ")
        data = arguments[0]
        arguments = arguments[1:]
        return data, e, arguments

    def user_in(self):
        self.print_user_message(self.windows[-2])

        uwin = self.windows[-1]
        tb = curses.textpad.Textbox(uwin)
        while 1:
            uwin.clear()
            uwin.addstr(1, 1, "User input: ")
            text = tb.edit(enter_is_terminate)
            file = open("gather.txt", "w")
            file.write(str(text))
            file.close()
            # Process input
            (out, e, arguments) = self.process_user_input(text)
            if e > 0:
                uwin.addstr(
                    3, 0, "Unknown command. Command must be letter<space>arguments"
                )
                uwin.refresh()
                time.sleep(3)
                continue

            uwin.addstr(3, 0, "Got: |" + out + "|" + "".join(arguments))
            uwin.refresh()
            if out == "q":
                uwin.addstr(4, 0, "Quitting")
                uwin.refresh()
                time.sleep(3)
                return
            elif out == "s":
                if isinstance(arguments, list):
                    arguments = " ".join(arguments)
                uwin.addstr(4, 0, "Sending command with args:" + arguments)
                uwin.refresh()
                time.sleep(3)
                self.write_to_all_uart(arguments)
                pass
            else:
                uwin.addstr(4, 0, "Unknown command")
                uwin.refresh()
                time.sleep(3)


def enter_is_terminate(x):
    if x == 10:
        return 7
    else:
        return x


def app(stdscr):
    m = monitor(stdscr)
    m.user_in()
    del m


wrapper(app)
