import subprocess
import time
import yaml
import os
from curses import wrapper
import curses.textpad
import curses
import click


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
            name = "uart_d_" + str(i)
            screen_cmd = "'screen -S {} -L -Logfile {}.log {} 115200,-ixon,-ixoff,onlcr' Enter".format(
                name, name, address
            )
            self.logfiles.append(name + ".log")
            cmd = "tmux send-keys -t {} ".format(i)
            cmd = cmd + screen_cmd
            print("Starting session for:", address)
            time.sleep(1)
            p = subprocess.Popen(cmd, shell=True, executable="/bin/bash")
            # Pew pew
            (output, err) = p.communicate()
        time.sleep(1)

    def send_to_screens(self, cmd, reversed=False):

        r = range(len(self.addresses))
        if reversed:
            r = reversed(r)

        for i in r:
            cmd_to_session = "tmux send-keys -t {} '{}' Enter".format(i, cmd)
            p = subprocess.Popen(cmd_to_session, shell=True, executable="/bin/bash")
            (output, err) = p.communicate()

    def send_to_screen(self, cmd, index):
        cmd_to_session = "tmux send-keys -t {} '{}' Enter".format(index, cmd)
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
            name = "uart_d_" + str(i)
            cmd = "screen -S {} -X quit".format(name)
            p = subprocess.Popen(cmd, shell=True, executable="/bin/bash")
            (output, err) = p.communicate()
            del p

    def start_user_pane(self):
        # self.stdscr = curses.initscr()
        # self.stdscr.clear()
        # self.user_in()
        pass

    def print_user_message(self):
        message = [
            "//// Commands ////",
            "--Quit: q",
            "--Send uart command to all: s <command>",
            "--Send uart command to single board: b <index> <command>",
            "  index starts at 0",
            "",
            "---------------",
        ]
        for l in range(len(message)):
            click.echo(click.style(message[l], fg="green"))
        return len(message) + 4

    def process_user_input(self, data):
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
        click.clear()
        time.sleep(1)

        while 1:
            click.clear()
            self.print_user_message()
            c = click.prompt("\nUser input")
            out = c
            arguments = []
            # Process input
            (out, e, arguments) = self.process_user_input(out)
            click.echo("Got: Command: |" + out + "| With Args: " + "".join(arguments))
            time.sleep(1)
            if e > 0:
                click.echo("Unknown command. Command must be letter<space>arguments")
                time.sleep(2)
                continue

            if out == "q":
                click.echo("Quitting")
                click.echo("killing screens")
                time.sleep(2)
                self.kill_screen_sessions()
                click.echo("Sending exits")
                time.sleep(2)
                r = range(len(self.addresses))
                r = reversed(r)
                for i in r:
                    self.send_to_screen("exit", i)
                return
            elif out == "s":
                if isinstance(arguments, list):
                    arguments = " ".join(arguments)
                click.echo("Sending command to all with args: " + arguments)
                time.sleep(1)
                self.send_to_screens(arguments)
                pass
            elif out == "b":
                if isinstance(arguments, list):
                    arguments = " ".join(arguments)
                index = int(arguments.split(" ")[0])
                arguments = " ".join(arguments.split(" ")[1:])

                if index >= (len(self.addresses)):
                    click.echo("Not a valid screen index " + str(index))
                    time.sleep(2)
                else:
                    click.echo(
                        "Sending command to board "
                        + str(index)
                        + " with args: "
                        + arguments,
                    )
                    time.sleep(2)
                    self.send_to_screen(arguments, index)
            else:
                click.echo("Unknown command")
                time.sleep(2)


def enter_is_terminate(x):
    if x == 10:
        return 7
    else:
        return x


def app():
    m = manager()
    m.user_in()
    del m


if __name__ == "__main__":
    app()
