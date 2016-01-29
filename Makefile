# This is the Makefile for oci-register-machine
# Authors: Sally O'Malley <somalley@redhat.com>
#
# Targets (see each target for more information):
#   all: Build code
#   build: Build code
#   install: Install docs, install binary to specified location
#   clean: Clean up.

.PHONY:  build install clean all docs

all: build docs

PREFIX ?= $(DESTDIR)/usr
HOOKSDIR=/usr/lib/docker/hooks.d
HOOKSINSTALLDIR=$(DESTDIR)$(HOOKSDIR)
# need this substitution to get build ID note
GOBUILD=go build -a -ldflags "-B 0x$(shell head -c20 /dev/urandom|od -An -tx1|tr -d ' \n')" 

# Build code
#
# Example:
#   make build
oci-register-machine: oci-register-machine.go
	$(GOBUILD) -o oci-register-machine

oci-register-machine.1.gz: oci-register-machine.1.md

	go-md2man -in "oci-register-machine.1.md" -out "oci-register-machine.1"
	sed -i 's|$$HOOKSDIR|$(HOOKSDIR)|' oci-register-machine.1
	gzip -f oci-register-machine.1

docs: oci-register-machine.1.gz
build: oci-register-machine

# Install code (change here to place anywhere you want)
#
# Example:
#   make install
install: oci-register-machine oci-register-machine.1.gz
	install -d -m 755 $(HOOKSINSTALLDIR)
	install -m 755 oci-register-machine $(HOOKSINSTALLDIR)
	install -d -m 755 $(PREFIX)/share/man/man1
	install -m 644 oci-register-machine.1.gz $(PREFIX)/share/man/man1
# Clean up
#
# Example:
#   make clean
clean:
	rm oci-register-machine
	rm oci-register-machine.1.gz
