#!/bin/bash
V=`npm run env | grep npm_package_version | cut -f 2 -d=`
# number of commits since last tag
#N=`git rev-list $(git describe --abbrev=0)..HEAD --count`
#branch
B=`git rev-parse --abbrev-ref HEAD`
#short git commit description
S=`git rev-parse --short HEAD`
#H=`git describe --always --long`
# compose a version compatible with git describe, but with newer version
H="$V-g$S-$B"
C=`git rev-parse --verify HEAD`
HAS_COMMIT=`cat src/version.py | grep $C`
if [ -z $HAS_COMMIT ]; then  # commit hash not in version.py -> new version
	echo "New version in src/version.py: $H"
VERSION_PY=$(cat <<EOF
__version__ = "$V"
__long_version__ = "$H"
__git_commit__ = "$C"
__git_branch__ = "$B"
EOF
)
	echo "$VERSION_PY" > src/version.py
else 
	echo "Version.py is up to date: $V"
fi
# check if current commit is pushed, if so add a new commit with this version information, else ammend the current commit
#if [ -z `git branch -r --contains $C` ] ; then
echo -n "Commit new version.py? (y/n) "
read add_commit
if [ $add_commit == 'y' ] ; then
	git add  src/version.py
	git commit -m "New release: version $V"
	echo "Added new version.py to commit" 
fi

if [ -z `git tag | grep $V` ] ; then 
	echo -n "There is no tag for version $V, create it (y/n)? "
        read create_tag
	if [ $create_tag == "y" ] ; then
		git tag $V -m 'New version'
		echo "New tag created"
	fi 
else 
	echo "Git tag $V already exists, no need to create new tag" 
	echo "If this version is not correct, change it in package.json"
fi
echo
echo -n "Satified with this release and push this release to repository (git push && git push --tags)? (y/n)"
read push
if [ "$push" == "y" ] ; then
	 git push && git push --tags
fi
