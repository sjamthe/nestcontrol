nestcontrol
===========

A nest thermostat controller written in Python.

Thanks
======

Much of this is possible due to [pynest](https://github.com/smbaker/pynest). That project, unfortunately, hasn't been
maintained in a couple of years and pull requests for additional features (such as turning hvac mode on/off) are likely
to never be merged. Instead of forking pynest, I chose to rewrite it from scratch a bit cleaner - more modular, better
functional compisition, using requests instead of urllib2, argparse instead of optparser, and following PEP8 guidelines.

License
=======

Licensed under GNU GPL 3.0. See the [LICENSE](https://github.com/scotte/nestcontrol/blob/master/LICENSE).
