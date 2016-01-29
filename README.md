## Systemd RegisterMachine

`Systemd-machined` is a virtual machine and container registration manager.  It is a tiny daemon that
tracks locally running virtual machines and containers and the processes belonging to them.


This project produces a golang binary that can be used with Docker (with minor code changes).
If you clone this branch and build/install `register-machine.go`, a binary will be placed in
`/usr/lib/docker/hooks.d` named `oci-register-machine`. You can change this location by
editing `HOOKSDIR` in the Makefile.


With minor changes to Docker code, this binary will be executed when starting and stopping Docker
containers via prestart and poststop hooks.  `RegisterMachine()` and `TerminateMachine()` are 
systemd-machined.service methods.
These and other methods are described here:
[systemd-machined freedesktop.org](http://www.freedesktop.org/wiki/Software/systemd/machined/)


Running Docker containers with this executable, RegisterMachine() is called
iust before a container is started and after it is provisioned.
All running containers' IDs will be listed when you run the command `machinectl` or `machinectl list`.
When containers are stopped/exited, TerminateMachine() is called, all container processes are terminated
and container ID is no longer listed in `machinectl` output.


This doc assumes you are running at least docker version 1.9 with the dockerhooks patch.
Also, place this project in your `GOPATH`.


To build, install, clean-up:

First, **clone** this branch in your `GOPATH`, then:

`make build`


`make install`


`make clean`
