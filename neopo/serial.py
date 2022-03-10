from .particle import particle_env
from .common import ProcessError, DependencyError, particle_cli, running_on_windows

import subprocess
import time
import re
from platform import system
from glob import glob

# set_baudrate Based on
# https://github.com/pyserial/pyserial/blob/master/serial/serialposix.py

# imports for set_baudrate
import os
import fcntl
import termios
import array

# constants for set_baudrate
TCGETS2 = 0x802C542A
TCSETS2 = 0x402C542B
BAUDRATE_OFFSET = 9
BOTHER = 0o010000

# Needed on Linux since stty does not support arbitrary baudrates there
def set_baudrate(port, baudrate):
    try:
        fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    except OSError:
        raise RuntimeError(f"Could not open port {port}")

    # right size is 44 on x86_64, allow for some growth
    buf = array.array('i', [0] * 64)
    try:
        # get serial_struct
        fcntl.ioctl(fd, TCGETS2, buf)
        # set custom speed
        buf[2] &= ~termios.CBAUD
        buf[2] |= BOTHER
        buf[BAUDRATE_OFFSET] = buf[BAUDRATE_OFFSET + 1] = baudrate

        # set serial_struct
        fcntl.ioctl(fd, TCSETS2, buf)

    except IOError:
        raise ValueError(f"Failed to set custom baud rate {baudrate}")
    finally:
        os.close(fd)


DFU_BAUD = 14400
LISTENING_BAUD = 28800
USB_EXPRESSION = "(?<=\[).{4}:.{4}(?=\])"
BAUD_TOOL = "stty"

# currently only supporting macOS and linux, we use this one-time check
# for efficient error checking
RUNTIME_PLATFORM = system()
PLATFORM_SUPPORTED = RUNTIME_PLATFORM != "Windows"


def throw_error_if_unsupported_platform():
    if not PLATFORM_SUPPORTED:
        raise DependencyError(
            "ERROR: Unsupported Platform - legacy commands requires Linux or macOS to run")


def get_particle_serial_ports():
    if RUNTIME_PLATFORM == "Linux":
        return glob('/dev/ttyACM*')
    elif RUNTIME_PLATFORM == "Darwin":
        return glob('/dev/cu.usbmodem*')
    else:
        # use particle serial list as fallback (though slower)
        # Find Particle deviceIDs connected via USB
        process = [particle_cli, "serial", "list"]
        particle = subprocess.run(process, stdout=subprocess.PIPE, env=particle_env(),
                                  shell=running_on_windows, check=True)
        return [line.decode("utf-8").split()[-1]
                for line in particle.stdout.splitlines()[1:]]


def get_dfu_device():
    process = ["dfu-util", "-l"]
    r = subprocess.run(
        process,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        env=particle_env()
    )
    content = r.stdout.decode()
    group = re.search(USB_EXPRESSION, content)
    return group.group(0) if group else None


def serial_open(device):
    throw_error_if_unsupported_platform()
    if RUNTIME_PLATFORM == "Linux":
        set_baudrate(device, LISTENING_BAUD)
    else:
        process = [BAUD_TOOL, "-f", device, str(LISTENING_BAUD)]
        subprocess.run(process, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)


def dfu_open(device):
    throw_error_if_unsupported_platform()
    if RUNTIME_PLATFORM == "Linux":
        set_baudrate(device, DFU_BAUD)
    else:
        process = [BAUD_TOOL, "-f", device, str(DFU_BAUD)]
        subprocess.run(process, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)


def serial_reset(port):
    throw_error_if_unsupported_platform()
    dfu_open(port)
    time.sleep(1)
    dfu_close()


def dfu_close():
    # don't need to worry about unsupported platform here since
    # this is only using dfu-util
    device = get_dfu_device()
    if device is None:
        raise ProcessError("No DFU device found to close")
    address = "0x080A0000:leave"
    process = f"dfu-util -d {device} -a0 -i0 -s {address} -D /dev/null".split()

    subprocess.run(
        process,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        env=particle_env()
    )
