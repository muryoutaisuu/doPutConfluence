#!/bin/bash
#set -x

INPUTSDIR="${HOME}/path/to/directory/with/files/to/upload/"
PUTCONFLUENCE="${HOME}/bin/putConfluence.py"
PUTCONFLUENCECONF="${HOME}/etc/putConfluence.conf"
INPUTSTOCONFLUENCE="${HOME}/bin/inputsToConfluence.sh"


# check for the files
test -d ${INPUTSDIR} || exit 1
test -x ${INPUTSTOCONFLUENCE} || exit 1
test -x ${PUTCONFLUENCE} || exit 1
test -r ${PUTCONFLUENCECONF} || exit 1

# set correct environment
export PATH="/bin:$PATH"

# change into correct directory
pushd ${INPUTSDIR} > /dev/null

# make shure, git repo is udpated
git pull -q > /dev/null

# get files
INPUTFILES=($(find . -type f))
count=1

# loop through files
for file in ${INPUTFILES[@]} ; do
  test "$1" != "-c" && echo "$(date --rfc-3339=seconds) ${count}/${#INPUTFILES[*]} working on file=\"${file}\""
  ${INPUTSTOCONFLUENCE} ${file} | ${PUTCONFLUENCE} -q -c ${PUTCONFLUENCECONF} put -p "Konfigurierte Logfiles Linux" SPLUNK $(basename ${file})
  if [ "$?" -ne "0" ] ; then
    echo "$(date --rfc-3339=seconds) ${count}/${#INPUTFILES[*]} encountered error on file=${file}"
  fi
  let count=count+1
done

# change back to original directory
popd > /dev/null

exit 0
