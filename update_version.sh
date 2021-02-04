#!/bin/bash
V=`git describe`
H=`git describe --always --long`
echo $H
VERSION_PY=$(cat <<EOF
__version__ = "$V"
__long_version__ = "$H"
EOF
)
echo "$VERSION_PY" > src/version.py
