#! /bin/bash

ml Python 

version=$(grep ^__version__ setup.py | cut -d'"' -f2)

pandoc --columns=100 --output=README.rst --to rst README.md
git add README.rst
git commit -a -m "version ${version}"
git tag ${version} -m "tag for PyPI"
mybranch=$(git branch | sed -n '/\* /s///p')
echo "pushing to branch $mybranch ..."
git push --tags origin $mybranch
# python3 setup.py register -r pypitest
python3 setup.py sdist upload -r pypitest

echo "  Done! Occasionally you may want to remove older tags:"
echo "git tag 1.2.3 -d"
echo "git push origin :refs/tags/1.2.3"
