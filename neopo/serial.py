import subprocess
import time
import re

from .particle import particle_env

PARTICLE_ENV = particle_env()
DFU_BAUD = 14400
LISTENING_BAUD = 28800
BAUD_TOOL = "baud-switcher"
USB_EXPRESSION = "(?<=\[).{4}:.{4}(?=\])"


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
    process = [BAUD_TOOL, device, str(LISTENING_BAUD)]
    subprocess.run(process, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def dfu_open(device):
    process = [BAUD_TOOL, device, str(DFU_BAUD)]
    subprocess.run(process, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def serial_reset(device):
    dfu_open(device)
    time.sleep(1)
    dfu_close()


def dfu_close():
    device = get_dfu_device()
    address = "0x080A0000:leave"

    process = [
        "dfu-util",
        "-d",
        device,
        "-a",
        "0",
        "-i",
        "0",
        "-s",
        address,
        "-D",
        "/dev/null",
    ]

    subprocess.run(
        process,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        env=PARTICLE_ENV,
    )


# neopo serial open
# neopo serial close


# neopo dfu open
# neopo dfu close
