#!/bin/bash
wget -q --show-progress https://www.python.org/ftp/python/3.7.9/Python-3.7.9.tar.xz
tar -xf Python-3.7.9.tar.xz
rm Python-3.7.9.tar.xz
cd Python-3.7.9
./configure
make
make install
cd ..
rm -rf Python-3.7.9
exit 0
