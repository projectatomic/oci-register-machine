# This is the Makefile for oci-register-machine
# Authors: Sally O'Malley <somalley@redhat.com>
#
# Targets (see each target for more information):
#   all: Build code
#   build: Build code
#   install: Install docs, install binary to specified location
#   clean: Clean up.

.PHONY:  build install clean all docs dist

all: build docs

PREFIX ?= $(DESTDIR)/usr
HOOKSDIR=/usr/libexec/oci/hooks.d
HOOKSINSTALLDIR=$(DESTDIR)$(HOOKSDIR)
# need this substitution to get build ID note
GOBUILD=go build -a -ldflags "${LDFLAGS:-} -B 0x$(shell head -c20 /dev/urandom|od -An -tx1|tr -d ' \n')"

# Build code
#
# Example:
#   make build
oci-register-machine: oci-register-machine.go
	GOPATH=$$GOPATH:/usr/share/gocode $(GOBUILD) -o oci-register-machine

oci-register-machine.1: oci-register-machine.1.md
	go-md2man -in "oci-register-machine.1.md" -out "oci-register-machine.1"
	sed -i 's|$$HOOKSDIR|$(HOOKSDIR)|' oci-register-machine.1

docs: oci-register-machine.1
build: oci-register-machine

dist: oci-register-machine.spec 
	spectool -g oci-register-machine.spec

rpm: dist
	rpmbuild --define "_sourcedir `pwd`" --define "_specdir `pwd`" \
	--define "_rpmdir `pwd`" --define "_srcrpmdir `pwd`" -ba oci-register-machine.spec 

# Install code (change here to place anywhere you want)
#
# Example:
#   make install
install: oci-register-machine oci-register-machine.1
	install -d -m 755 $(HOOKSINSTALLDIR)
	install -m 755 oci-register-machine $(HOOKSINSTALLDIR)
	install -d -m 755 $(PREFIX)/share/man/man1
	install -m 644 oci-register-machine.1 $(PREFIX)/share/man/man1
	install -D -m 644 oci-register-machine.conf $(DESTDIR)/etc/oci-register-machine.conf
# Clean up
#
# Example:
#   make clean
clean:
	rm -f oci-register-machine *~
	rm -f oci-register-machine.1
	rm -f oci-register-machine-*.tar.gz
	rm -f oci-register-machine-*.rpm
