// +build linux

package main

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"log/syslog"
	"os"
	"strings"

	"github.com/godbus/dbus"
	"gopkg.in/yaml.v1"
)

var conn *dbus.Conn

type State struct {
	Version    string `json:"version"`
	ID         string `json:"id"`
	Status     string `json:"status"`
	Pid        int    `json:"pid"`
	Root       string `json:"root"`
	Bundle     string `json:"bundle"`
	BundlePath string `json:"bundlePath"`
}

type Process struct {
	Env []string `json:"env"`
}

type Config struct {
	Process *Process `json:"process"`
}

func Validate(id string) (string, error) {
	for len(id) < 32 {
		id += "0"
	}
	return hex.EncodeToString([]byte(id)), nil
}

// RegisterMachine with systemd on the host system
func RegisterMachine(name string, id string, pid int, root_directory string) error {
	var (
		av  []byte
		err error
	)
	if conn == nil {
		conn, err = dbus.SystemBus()
		if err != nil {
			return err
		}
	}

	av, err = hex.DecodeString(id[0:32])
	if err != nil {
		return err
	}
	obj := conn.Object("org.freedesktop.machine1", "/org/freedesktop/machine1")
	service := os.Getenv("container")
	if service == "" {
		service = "runc"
	}
	if len(name) > 32 {
		name = name[0:32]
	}

	return obj.Call("org.freedesktop.machine1.Manager.RegisterMachine", 0, name, av, service, "container", uint32(pid), root_directory).Err
}

// TerminateMachine registered with systemd on the host system
func TerminateMachine(name string) error {
	var err error
	if conn == nil {
		conn, err = dbus.SystemBus()
		if err != nil {
			return err
		}
	}
	if len(name) > 32 {
		name = name[0:32]
	}

	obj := conn.Object("org.freedesktop.machine1", "/org/freedesktop/machine1")
	return obj.Call("org.freedesktop.machine1.Manager.TerminateMachine", 0, name).Err
}

const CONFIG = "/etc/oci-register-machine.conf"

var settings struct {
	Disabled bool `yaml:"disabled"`
}

func main() {
	var state State

	logwriter, err := syslog.New(syslog.LOG_NOTICE, "oci-register-machine")
	if err == nil {
		log.SetOutput(logwriter)
	}
	// then config file settings

	data, err := ioutil.ReadFile(CONFIG)
	if err != nil {
		if !os.IsNotExist(err) {
			log.Fatalf("RegisterMachine Failed to read %s %m", CONFIG)
		}
	} else {
		if err := yaml.Unmarshal(data, &settings); err != nil {
			log.Fatalf("RegisterMachine Failed to parse %s %m", CONFIG)
		}
		if settings.Disabled {
			return
		}
	}

	if err := json.NewDecoder(os.Stdin).Decode(&state); err != nil {
		log.Fatalf("RegisterMachine Failed %m")
	}

	log.Printf("Register machine: %s %s %d %s", state.ID, state.Status, state.Pid, state.Root)
	passId := state.ID
	// If id is shorter than 32, then read container_uuid from the container process environment variables
	if len(passId) < 32 && state.Pid > 0 {
		var config Config
		var bundle string
		if state.Bundle != "" {
			bundle = state.Bundle
		} else {
			bundle = state.BundlePath
		}
		configFile := fmt.Sprintf("%s/config.json", bundle)
		data, err := ioutil.ReadFile(configFile)
		if err != nil {
			log.Fatalf("RegisterMachine Failed to read %s %m", configFile)
		}
		if err := yaml.Unmarshal(data, &config); err != nil {
			log.Fatalf("RegisterMachine Failed to parse %s %m", configFile)
		}
		for _, env := range config.Process.Env {
			const PREFIX = "container_uuid="
			if strings.HasPrefix(env, PREFIX) {
				passId = strings.Replace(env[len(PREFIX):], "-", "", -1)
				break
			}
		}
	}
	// ensure id is a hex string at least 32 chars
	passId, err = Validate(passId)
	if err != nil {
		log.Fatalf("RegisterMachine Failed %m")
	}

	switch state.Status {
	case "created":
		{
			if err = RegisterMachine(state.ID, passId, int(state.Pid), state.Root); err != nil {
				log.Fatalf("Register machine failed: %m")
			}
			return
		}
	case "stopped":
		{
			if err := TerminateMachine(state.ID); err != nil {
				if !strings.Contains(err.Error(), "No machine") {
					log.Fatalf("TerminateMachine failed: %m")
				}
			}
			return
		}
	}
	log.Printf("Does not support the %q status must be created|stopped", state.Status)
}
