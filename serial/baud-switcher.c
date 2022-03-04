#include <asm/ioctls.h>
#include <asm/termbits.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, char *argv[]) {

  if (argc != 3) {
    printf("%s device rate\n\nSet baud rate for a serial device.\nFor "
           "instance:\n    %s /dev/ttyACM0 14400\n",
           argv[0], argv[0]);
    return -1;
  }

  int fd = open(argv[1], O_RDONLY);
  int rate = atoi(argv[2]);

  struct termios2 tio;
  ioctl(fd, TCGETS2, &tio);
  tio.c_cflag &= ~CBAUD;
  tio.c_cflag |= BOTHER;
  tio.c_ispeed = rate;
  tio.c_ospeed = rate;
  int r = ioctl(fd, TCSETS2, &tio);
  close(fd);

  if (r == 0) {
    printf("Set %s to %d successfully.\n", argv[1], rate);
  } else {
    perror("ioctl");
  }
}
