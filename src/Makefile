CC = gcc
CFLAGS = -O3 -std=c17 -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wdouble-promotion -Wformat=2 -Werror -fopenmp
CPPFLAGS ?=
LDFLAGS ?= -fopenmp
LDLIBS ?= -lgmp -lcrypto
SOURCE_SHA := $(shell sha256sum a249107.c | cut -d' ' -f1)
MAKE_SHA := $(shell sha256sum Makefile | cut -d' ' -f1)
BIND = -DA249107_SOURCE_SHA='"$(SOURCE_SHA)"' -DA249107_MAKE_SHA='"$(MAKE_SHA)"'

.PHONY: all clean check
all: a249107

a249107: a249107.c Makefile
	$(CC) $(CPPFLAGS) $(BIND) $(CFLAGS) -o $@ a249107.c $(LDFLAGS) $(LDLIBS)

check: a249107
	python3 -B ../check/verify.py data
	python3 -B ../check/verify.py native

clean:
	rm -f a249107
