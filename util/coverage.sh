#!/usr/bin/env bash
homedir="$(dirname "$(pwd)")"
testdir="${homedir}/test"
activate="${homedir}/venv3.6/bin/activate"
. $activate

cd $homedir
coverage run -m pytest
coverage html
