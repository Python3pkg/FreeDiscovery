#!/bin/bash
# This script is meant to be called in the "deploy" step defined in 
# circle.yml. See https://circleci.com/docs/ for more details.
# The behavior of the script is controlled by environment variable defined
# in the circle.yml in the top level folder of the project.


if [ -z $CIRCLE_PROJECT_USERNAME ];
then USERNAME="FreeDiscovery";
else USERNAME=$CIRCLE_PROJECT_USERNAME;
fi

DOC_REPO="freediscovery.github.io"

if [ "$CIRCLE_BRANCH" = "master" ]
then
	dir=dev
else
	# Strip off .X
	dir="${CIRCLE_BRANCH::-2}"
fi

MSG="Pushing the docs to $dir/ for branch: $CIRCLE_BRANCH, commit $CIRCLE_SHA1"

cd $HOME
if [ ! -d $DOC_REPO ];
then git clone "git@github.com:scikit-learn/"$DOC_REPO".git";
fi
cd $DOC_REPO
git checkout $CIRCLE_BRANCH
git reset --hard origin/$CIRCLE_BRANCH
git rm -rf $dir/ && rm -rf $dir/
cp -R $HOME/scikit-learn/doc/_build/html $dir
git config --global push.default matching
git add -f $dir/
git commit -m "$MSG" $dir
git push

echo $MSG 