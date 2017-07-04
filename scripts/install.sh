#!/bin/bash

sudo apt-get install python3-dev python3-pip -y
sudo apt-get install libmysqlclient-dev -y
sudo wget -q https://bootstrap.pypa.io/ez_setup.py -O - | sudo python3

## install pyhton env.

wget -q https://pypi.python.org/packages/5f/ad/1fde06877a8d7d5c9b60eff7de2d452f639916ae1d48f0b8f97bf97e570a/distribute-0.7.3.zip -O -
unzip -o distribute-0.7.3.zip
cd distribute-0.7.3 && sudo python setup.py install
cd -

## install python mysql driver

curl -L https://github.com/PyMySQL/PyMySQL/tarball/pymysql-0.6 | tar xz
cd PyMySQL-PyMySQL-7c86923/ && sudo python3 setup.py install
cd -

## install python MysQLdb for python3

git clone https://github.com/davispuh/MySQL-for-Python-3.git
cd MySQL-for-Python-3/ && sudo python3 setup.py install
cd -

## the plugin

pip3 install PyYaml 
pip3 install colorama

