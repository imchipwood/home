#!/usr/bin/env bash
homedir="$(dirname "$(pwd)")"
testdir="${homedir}/test"
reportdir="${homedir}/reports"
activate="${homedir}/venv3.6/bin/activate"
. $activate

cd $homedir
rm -rf $reportdir
mkdir $reportdir
coverage run -m pytest
coverage html
