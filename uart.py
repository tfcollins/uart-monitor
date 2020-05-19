import os
import threading
import time
import glob

import serial


LINUX_SERIAL_FOLDER = "/dev/serial"


class uart:
    def __init__(
        self, window, max_lines, address=None, baudrate=115200, logfilename="uart.log",
    ):
        self.window = window
        self.current_lines = []
        self.max_lines = max_lines
        self.com = []  # Preset incase __del__ is called before set
        self.address = address
        self.baudrate = baudrate
        self.listen_thread_run = False
        self.logfilename = logfilename
        self.thread = None
        self.print_to_console = False
        self.max_read_time = 30
        self.printed_lines = 0
        if not self.address:
            raise Exception(
                "UART address must be defined (under uart-config in yaml is one option)"
            )
        self.com = serial.Serial(self.address, self.baudrate, timeout=0.5)
        self.com.reset_input_buffer()

    def __del__(self):
        # logging.info("Closing UART")
        if self.com:
            self.com.close()

    def set_title(self):
        self.window.addstr(0, 2, self.address)

    def print_new_line(self, lines):

        if not isinstance(lines, list):
            lines = [lines]

        for line in lines:

            if len(self.current_lines) >= self.max_lines:
                self.current_lines = self.current_lines[1:]
                self.current_lines.append(line)
            else:
                self.current_lines.append(line)
            # Updates all lines
            self.window.clear()
            self.window.box()
            self.set_title()
            if len(self.current_lines) > 0:
                line_num = 1
                for cline in self.current_lines:
                    if isinstance(cline, str):
                        # cline = str(len(cline))
                        # cline = cline.replace("\n","")
                        self.window.addstr(line_num, 1, cline)
                        line_num = line_num + 1
                        # self.printed_lines = self.printed_lines + 1
            self.window.refresh()

    def start_log(self, logappend=False):
        """ Trigger monitoring with UART interface """
        self.listen_thread_run = True
        # logging.info("UART console saving to file: " + self.logfilename)
        self.thread = threading.Thread(target=self._listen, args=(logappend,))
        self.thread.start()

    def stop_log(self):
        """ Stop monitoring with UART interface """
        self.listen_thread_run = False
        # logging.info("Waiting for UART reading thread")
        self.thread.join()
        # logging.info("UART reading thread joined")

    def _listen(self, logappend=False):
        ws = "w"
        # if logappend:
        ws = "a"
        count = 0
        while self.listen_thread_run:
            data = self._read_until_stop()
            # data = self._read_until_done(done_string="\n")
            if data:
                for d in data:
                    file = open(self.logfilename, ws)
                    file.writelines(d + str(count) + "\n")
                    count = count + 1
                    self.print_new_line(data)
                    file.close()
            else:
                time.sleep(1)
        # logging.info("UART listening thread closing")

    def _read_until_stop(self):
        buffer = []
        while self.com.in_waiting > 0:
            try:
                data = self.com.readline()
                data = str(data[:-1].decode("ASCII"))
            except Exception as ex:
                # logging.warning("Exception occurred during data decode")
                # logging.warning(str(ex))
                continue
            # if self.print_to_console:
            #     print(data)
            buffer.append(data)
        return buffer

    def _write_data(self, data):
        data = data + "\n"
        bdata = data.encode()
        # logging.info("--------Sending Data-----------")
        # logging.info(bdata)
        # logging.info("-------------------------------")
        self.com.write(bdata)
        time.sleep(1)

    def _read_for_time(self, period):
        data = []
        for k in range(period):
            data.append(self._read_until_stop())
            time.sleep(1)
        return data

    def _read_until_done(self, done_string="done"):
        data = []
        for k in range(self.max_read_time):
            data = self._read_until_stop()
            if isinstance(data, list):
                for d in data:
                    if done_string in d:
                        # logging.info("done found in data")
                        return
            elif done_string in data:
                # logging.info("done found in data")
                return
            time.sleep(1)

    def _check_for_string_console(self, console_out, string):
        for d in console_out:
            if not isinstance(d, list):
                d = [d]
            if isinstance(d, list):
                for c in d:
                    c = c.replace("\r", "")
                    if string in c:
                        return True
        return False


if __name__ == "__main__":

    # import pathlib

    # p = pathlib.Path(__file__).parent.absolute()
    # p = os.path.split(p)
    # p = os.path.join(p[0], "resources", "nebula-zed.yaml")

    # u = uart(yamlfilename=p)
    # u.start_log()
    # time.sleep(10)
    # u.stop_log()
    # u = []
    pass
