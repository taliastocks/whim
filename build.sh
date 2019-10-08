#!/bin/sh
python3 -m pex --disable-cache -v . --python=python3 --python-shebang='/usr/bin/env python3' -m whim -o whim
