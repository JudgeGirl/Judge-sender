## Judge-sender ##

配置目錄如下

```
root@ubuntu:/home/judgesister# tree -L 1
.
├── Judge-MySQL
├── JudgeNode
├── Judge-receiver
├── Judge-sender <<<<<<<<< 
├── Judge-template
├── README.md
├── source
├── submission
└── testdata
```

### 準備工作 ###

1. 確定資料庫帳號允許登入
2. 沙盒使用帳號允許免密碼登入
3. 安裝 python3 模組
	* `pip3 install PyYaml`
	* `MySQLdb` 參閱 `install_tutorial` 下的說明

#### 建立遠端免密碼登入 ####

```
$ ssh-keygen -t rsa
$ scp id_rsa.pub server_hostname:~/.ssh/
$ ssh server_hostname
$ cat .ssh/id_rsa.pub >> .ssh/authorized_keys
```

### 運行 ###

```
$ cd judge-sender
$ ./start
```

### 例外處理 ###

* 如果 Judge-sender 停止，大部份都是發生測資檔案找不到。
* 如果進入無限迴圈，建議先把要測試提交資訊從 MySQL 移除。
* 如果遠端連線很慢，請在 `/etc/ssh/sshd_config` 加入一行 `UseDNS no`，隨後執行 `sudo service ssh restart` 讓設定生效。
