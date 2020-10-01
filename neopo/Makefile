# Compile neopo.py to a neopo executable
neopo: neopo.c
	gcc -Os -I /usr/include/python3.8 -o neopo neopo.c -lpython3.8 -lpthread -lm -lutil -ldl
neopo.c : neopo.py
	cython -3 --embed -o neopo.c neopo.py
