#!/bin/bash
V=`npm run env | grep npm_package_version | cut -f 2 -d=`
# number of commits since last tag
N=`git rev-list $(git describe --abbrev=0)..HEAD --count`
#short git commit description
S=`git rev-parse --short HEAD`
#H=`git describe --always --long`
# compose a version compatible with git describe, but with newer version
H="$V-$N-g$S"
C=`git rev-parse --verify HEAD`
echo $H
VERSION_PY=$(cat <<EOF
__version__ = "$V"
__long_version__ = "$H"
__git_commit__ = "$C"
EOF
)
echo "$VERSION_PY" > src/version.py
