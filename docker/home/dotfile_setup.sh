#!/bin/bash
cd ~
mkdir dev
cd dev
git clone git@github.com/imchipwood/dotfiles.git unix
cd unix
git checkout -t origin/rpi_teamcity
cd ~
rm .bashrc .profile .bash_aliases .gitconfig
ln -s ~/dev/unix/.bash_aliases .bash_aliases
ln -s ~/dev/unix/.bashrc .bashrc
ln -s ~/dev/unix/.profile .profile
ln -s ~/dev/unix/.gitconfig .gitconfig
exit 0
