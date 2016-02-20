## Judge-sender ##

```
root@ubuntu:/home/judgesister# tree -L 1
.
├── Judge-MySQL
├── JudgeNode
├── Judge-receiver
├── Judge-sender
├── Judge-template
├── README.md
├── source
├── submission
└── testdata
```

### 準備工作 ###

1. open the `judge_server.py`.
2. make sure MySQL host, user, password, dbname correct.
3. check judge-machine user login with ssh, ex. login maplewing@140.112.30.245 without password.

#### How to Make Login without Password ####

```
$ ssh-keygen -t rsa
$ scp id_rsa.pub server_hostname:~/.ssh/
$ ssh server_hostname
$ cat .ssh/id_rsa.pub >> .ssh/authorized_keys
```

### Run ###

```
$ cd judge-sender
$ ./start
```

### Exception ###

* If judge-sender stop, maybe happened file not found or testdata setting error. Make sure the setting correct and restart the judge-sender. 
* If the accident need to solve as soon as possible, remove the submission id from mysql database and ban the right of problem submit ability.
