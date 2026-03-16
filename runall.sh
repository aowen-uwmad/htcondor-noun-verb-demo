#!/bin/bash

RED=$(tput setaf 1)
BLUE=$(tput setaf 4)
RC=$(tput sgr0)

header () {
  echo -e "${RED} === ${1} === ${RC}"
  echo ""
}

command () {
  echo -e "${BLUE}\$ ${1} ${RC}"
  bash -c "${1}"
  echo ""
}

header "HTCONDOR"
command "htcondor --help"

header "HTCONDOR JOBS"
command "htcondor jobs --help"
for verb in submit status report interact hold release remove edit help ; do 
  command "htcondor jobs ${verb} --help"
done

header "HTCONDOR POOL"
command "htcondor pool --help"
command "htcondor pool status --help"
