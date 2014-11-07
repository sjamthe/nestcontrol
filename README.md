nestcontrol
===========

A nest thermostat controller written in Python.

Status
======

* Displays current temperature, humidity, setpoint, and mode
* Sets hvac mode - off, heat, cool, range (aka auto)
* Sets temperature set point (or high/low for range/auto mode)
* Caches user authentication token to ~/.cache/nestcontrol/token
* Dump full and basic status as json

Usage
=====

Usage examples:

```
$ ./nest.py -h
usage: nest.py [-h] -u USERNAME -p PASSWORD [-s SERIAL] [-f] [-j] [-d DEBUG]
               [command [command ...]]

Nest thermostat controller

positional arguments:
  command               commands - off, heat, cool, auto, or a set temperature
                        in Fahrenheit. For example, to turn hvac off, use the
                        command "off", or to turn on heat and set the
                        temperature, "heat 72", or to just set the temperature
                        "68". For auto, specify a temperature range (such as
                        "68-72"). Commands are executed in the order provided,
                        with set points first, and note: don't enter the
                        quotes.

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Nest username.
  -p PASSWORD, --password PASSWORD
                        Nest password.
  -s SERIAL, --serial SERIAL
                        Nest serial number (Default: first nest found).
  -f, --fulljson        Output entire status as json (Default: False).
  -j, --json            Output basic info as json (Default: False).
  -d DEBUG, --debug DEBUG
                        Debug level. Higher is more (Default: 0).

$ ./nest.py -u skipper@gilligan.isle -p minnow
Temp: 75.9°F, Humidity: 51%, Set: 72.0°F, Mode: off

$ ./nest.py -u skipper@gilligan.isle -p minnow 70 heat
Temp: 75.9°F, Humidity: 51%, Set: 70.0°F, Mode: heat

$ ./nest.py -u skipper@gilligan.isle -p minnow 65-77 auto
Temp: 75.9°F, Humidity: 51%, Set: 65.0°F - 77.0°F, Mode: range

$ ./nest.py -u skipper@gilligan.isle -p minnow 70 off
Temp: 75.9°F, Humidity: 51%, Set: 70.0°F, Mode: off
```

Commands are processed in order, though temperature set points or ranges are processed before commands. Hence the following command sequence:

```
$ ./nest.py [...] off 70
```

Will be processed as if the following was entered:

```
$ ./nest.py [...] 70 off
```

This is to make sure the requested temperature set point takes effect immediately.
Otherwise, imagine if the room was 70 degrees and the thermostat was completely
off with a set point of 74. If we provided the commands in the order of "heat 70",
we wouldn't want the heater to immediately turn on when the system is set to
heat (because the thermostat's current set point in 74). By adjusting the set
point first, we avoid that possibility.

Thanks
======

Much of this is possible due to [pynest](https://github.com/smbaker/pynest). That project, unfortunately, hasn't been
maintained in a couple of years and pull requests for additional features (such as turning hvac mode on/off) are likely
to never be merged. Instead of forking pynest, I chose to rewrite it from scratch a bit cleaner - more modular, better
functional composition, using requests instead of urllib, argparse instead of optparser, and following PEP8 guidelines.

License
=======

Licensed under GNU GPL 3.0. See the [LICENSE](https://github.com/scotte/nestcontrol/blob/master/LICENSE).
