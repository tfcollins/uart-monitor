import subprocess
import time
import yaml
import os
import glob
import shutil


def read_yaml(filename):
    """Process yaml into config"""
    if not os.path.exists(filename):
        raise Exception("YAML config file not found")

    stream = open(filename, "r")
    configs = yaml.safe_load(stream)
    stream.close()
    return configs["uarts"]


class starter:
    def __init__(self):

        addresses = read_yaml("config.yaml")
        for address in addresses:
            if not os.path.exists(address):
                raise Exception(address + " not found")
        self.addresses = addresses
        self.gen_tmux_command()

    def gen_tmux_command(self):
        # Set first screen
        cmd = "tmux new-session -s smokemonitor {} ".format("bash")
        # Set next
        for _ in range(len(self.addresses) - 1):
            cmd += "\; split-window -v"
        # Set last
        cmd += "\; split-window -v {} \; select-layout even-vertical\; attach".format("python3 manager.py")
        p = subprocess.Popen(cmd, shell=True, executable="/bin/bash")
        # Pew pew
        (output, err) = p.communicate()

    def check_logs(self):
        for f in glob.glob("./uart*.log"):
            print("Logfile produced:", f)
        starting_name = "logs_"
        s = 0
        while True:
            dir = starting_name + str(s)
            if not os.path.exists(dir):
                os.mkdir(dir)
                for f in glob.glob("./uart*.log"):
                    print("Moving", f, "to", dir)
                    shutil.move(f, dir)
                break
            else:
                s += 1


if __name__ == "__main__":
    s = starter()
    s.check_logs()
