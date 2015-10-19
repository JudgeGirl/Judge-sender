## Python3 MySQLdb Error ##

from [here](http://stackoverflow.com/questions/12031151/how-to-install-mysqldb-with-python-3-2)

1. Execute the following command to upgrade setuptools for your local python3:
```
$ python distribute_setup.py
```

2. Download and install the pymysql driver:
```
$ curl -L https://github.com/PyMySQL/PyMySQL/tarball/pymysql-0.6 | tar xz
$ cd PyMySQL-PyMySQL-7c86923/
$ sudo python3 setup.py install
```

3. Download and install MySQLdb driver for python3
```
$ git clone https://github.com/davispuh/MySQL-for-Python-3.git
$ cd MySQL-for-Python-3/
$ python3 setup.py install
```

4. To check open python interpreter via python.exe command and execute:
```
import pymysql
import MySQLdb
```

If everything went ok - then both lines should not fail.

### Other Detail ###

If any step happened error, maybe install `sudo apt-get install python3-dev`.
