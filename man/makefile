# Output format
OUTEXT=html

# Extension for groff files
SRCEXT=1

# Command to render groff file
GROFF_COMMAND=groff -m man -T

# Gather source and output files
SRC=$(shell find *.$(SRCEXT))
OUT=$(SRC:%.$(SRCEXT)=%.$(OUTEXT))

all: $(OUT)

# Compile groff
%.$(OUTEXT): %.$(SRCEXT)
	$(GROFF_COMMAND) $(OUTEXT) $^ > $@

clean:
	rm -f *.$(OUTEXT)
