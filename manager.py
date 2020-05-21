import subprocess
import time
import yaml
import os
from curses import wrapper
import curses.textpad
import curses

def read_yaml(filename):
    """Process yaml into config"""
    if not os.path.exists(filename):
        raise Exception("YAML config file not found")

    stream = open(filename, "r")
    configs = yaml.safe_load(stream)
    stream.close()
    return configs["uarts"]


class manager:
    def __init__(self):
        addresses = read_yaml("config.yaml")
        for address in addresses:
            if not os.path.exists(address):
                raise Exception(address + " not found")
        self.addresses = addresses
        self.start_screens()

    def start_screens(self):
        self.logfiles = []
        for i, address in enumerate(self.addresses):
            name = "uart_d_"+str(i)
            screen_cmd = "'screen -S {} -L -Logfile {}.log {} 115200' Enter".format(name, name, address)
            self.logfiles.append(name+".log")
            cmd = "tmux send-keys -t {} ".format(i)
            cmd = cmd + screen_cmd
            print("Starting session for:",address)
            time.sleep(1)
            p = subprocess.Popen(cmd, shell=True, executable="/bin/bash")
            # Pew pew
            (output, err) = p.communicate()
        time.sleep(1)

    def send_to_screens(self,cmd, reversed=False):

        r = range(len(self.addresses))
        if reversed:
            r = reversed(r)

        for i in r:
            cmd_to_session = "tmux send-keys -t {} '{}' Enter".format(i,cmd)
            p = subprocess.Popen(cmd_to_session, shell=True, executable="/bin/bash")
            (output, err) = p.communicate()


    def send_to_screen(self,cmd,index):
        cmd_to_session = "tmux send-keys -t {} '{}' Enter".format(index,cmd)
        p = subprocess.Popen(cmd_to_session, shell=True, executable="/bin/bash")
        (output, err) = p.communicate()

    #####################################################
    #
    # def label_each_pane(self):
    #     for i in range(len(self.addresses)):
    #         name = self.addresses[i]
    #         cmd = "printf '\033]2;"+name+"\033\\"
    #         self.send_to_screen(cmd,i)
    #         cmd = 'tmux set -g pane-border-format "#'+str(i)+' #T"'
    #         p = subprocess.Popen(cmd, shell=True, executable="/bin/bash")
    #         (output, err) = p.communicate()




    def kill_screen_sessions(self):
        for i in range(len(self.addresses)):
            name = "uart_d_"+str(i)
            cmd = "screen -S {} -X quit".format(name)
            p = subprocess.Popen(cmd, shell=True, executable="/bin/bash")
            (output, err) = p.communicate()
            del p


    def start_user_pane(self):
        # self.stdscr = curses.initscr()
        # self.stdscr.clear()
        # self.user_in()
        pass

    def print_user_message(self, win):
        message = [
            "//// Commands ////",
            "--Quit: q",
            "--Send uart command to all: s <command>",
            "--Send uart command to single board: b <index> <command>",
            "  index starts at 0"
        ]
        for l in range(len(message)):
            win.addstr(l + 1, 1, message[l])
        win.refresh()
        return len(message)+4

    def process_user_input(self, data,l):
        data = data.split("\n")
        v = 0
        for line in data:
            v += 1
            if "User input" in line:
                break
        data = "\n".join(data[v-1:])
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

    def user_in(self,stdscr):
        # self.label_each_pane()

        self.stdscr = stdscr
        uwin = self.stdscr
        tb = curses.textpad.Textbox(uwin)

        while 1:
            uwin.clear()
            l = self.print_user_message(self.stdscr)
            uwin.addstr(l, 1, "User input: ")
            text = tb.edit(enter_is_terminate)
            file = open("gather.txt", "w")
            file.write(str(text))
            file.close()
            # Process input
            (out, e, arguments) = self.process_user_input(text,l)
            uwin.addstr(l+3, 0, "Got: |" + out + "|" + "".join(arguments))
            if e > 0:
                uwin.addstr(
                    l+4, 0, "Unknown command. Command must be letter<space>arguments"
                )
                uwin.refresh()
                time.sleep(2)
                continue

            uwin.refresh()
            if out == "q":
                uwin.clear()
                uwin.refresh()
                uwin.addstr(0, 0, "Quitting")
                uwin.refresh()
                uwin.addstr(1, 0, "killing screens")
                uwin.refresh()
                time.sleep(1)
                self.kill_screen_sessions()
                time.sleep(1)
                uwin.addstr(2, 0, "Sending exits")
                uwin.refresh()
                time.sleep(1)
                r = range(len(self.addresses))
                r = reversed(r)
                for i in r:
                    self.send_to_screen("exit",i)
                return
            elif out == "s":
                if isinstance(arguments, list):
                    arguments = " ".join(arguments)
                uwin.addstr(l+4, 0, "Sending command to all with args: " + arguments)
                uwin.refresh()
                time.sleep(1)
                self.send_to_screens(arguments)
                pass
            elif out == "b":
                if isinstance(arguments, list):
                    arguments = " ".join(arguments)
                index = int(arguments.split(" ")[0])
                arguments = " ".join(arguments.split(" ")[1:])

                if index>=(len(self.addresses)):
                    uwin.addstr(l+4, 0, "Not a valid screen index "+str(index))
                    uwin.refresh()
                    time.sleep(2)
                else:
                    uwin.addstr(l+4, 0, "Sending command to board "+str(index)+" with args: " + arguments)
                    uwin.refresh()
                    time.sleep(2)
                    self.send_to_screen(arguments,index)
            else:
                uwin.addstr(l+4, 0, "Unknown command")
                uwin.refresh()
                time.sleep(2)


def enter_is_terminate(x):
    if x == 10:
        return 7
    else:
        return x

def app(stdscr):
    m = manager()
    m.user_in(stdscr)
    del m


if __name__ == "__main__":
    wrapper(app)
