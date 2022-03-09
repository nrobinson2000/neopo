from .particle import particle_env
import subprocess
import time
import re
import platform

# Based on
# https://github.com/pyserial/pyserial/blob/master/serial/serialposix.py

import os
import fcntl
import termios
import array

TCGETS2 = 0x802C542A
TCSETS2 = 0x402C542B
BAUDRATE_OFFSET = 9
BOTHER = 0o010000


# Needed on Linux since stty does not support arbitrary baudrates
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


PARTICLE_ENV = particle_env()
DFU_BAUD = 14400
LISTENING_BAUD = 28800
USB_EXPRESSION = "(?<=\[).{4}:.{4}(?=\])"
BAUD_TOOL = "stty"


def get_dfu_device():
    process = ["dfu-util", "-l"]
    r = subprocess.run(
        process,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        env=PARTICLE_ENV,
    )
    content = r.stdout.decode()
    group = re.search(USB_EXPRESSION, content)
    return group.group(0)


def serial_open(device):
    if platform.system() == "Linux":
        set_baudrate(device, LISTENING_BAUD)
    else:
        process = [BAUD_TOOL, "-f", device, str(LISTENING_BAUD)]
        subprocess.run(process, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)


def dfu_open(device):
    if platform.system() == "Linux":
        set_baudrate(device, DFU_BAUD)
    else:
        process = [BAUD_TOOL, "-f", device, str(DFU_BAUD)]
        subprocess.run(process, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)


def serial_reset(device):
    dfu_open(device)
    time.sleep(1)
    dfu_close()


def dfu_close():
    device = get_dfu_device()
    address = "0x080A0000:leave"
    process = f"dfu-util -d {device} -a0 -i0 -s {address} -D /dev/null".split()

    subprocess.run(
        process,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        env=PARTICLE_ENV,
    )
