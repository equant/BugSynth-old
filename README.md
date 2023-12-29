# Credit

A lot of the code in this repo is from the SquishBox/[FluidSynth](http://www.fluidsynth.org) project.


# Stuff

```bash

sudo systemctl stop bugsynth.service

```
sudo vim /etc/systemd/system/bugsynth.service

`sudo vim /etc/udev/rules.d/98-midi.rules`

```
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1235", ATTRS{idProduct}=="0123", RUN+="/home/equant/BugSynth/midi_connect.sh"
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1c75", ATTRS{idProduct}=="0218", RUN+="/home/equant/BugSynth/midi_connect.sh"
```
