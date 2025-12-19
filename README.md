# MagaCite

Blog Content Migration and Reference Management System.

## Server Initialization

If you are using conda on the server, please create a new conda environment and enter it; if you do not have conda on your server, please ignore this sentence.

``` bash
git clone https://github.com/yharim-io/MegaCite.git
cd MegaCite
pip install -r requirements.txt
bash scripts/install_mysql.sh # `install_mysql_mac.sh` for MacOS
playwright install
export MC_API_KEY="your-openai-api-key"
export SMTP_SERVER="your-smtp-server"
export SMTP_PORT="your-smtp-port"
export SMTP_USER="your-email-address"
export SMTP_PASSWORD="your-email-password-or-token"
```

Then change the `SERVER_CONFIG` under `core/config.py`:

``` python
SERVER_CONFIG = {
    "host": "your ip addr",
    "port": 8080
}
```

Finally:

``` bash
python cli.py server start 8080
```

## Permission Resolve

Sometimes you will encounter this error

``` bash
$ python cli.py server start 8080
[-] Database connection failed: (1698, "Access denied for user 'root'@'localhost'")
```

The main reason is that the default MySQL installation on Ubuntu enables the auth_socket plugin for the root user.

Resolve it using the following script:

``` bash
sudo mysql -u root
USE mysql;
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '114514';
FLUSH PRIVILEGES;
EXIT;
```

Now try restarting the server; it should be able to connect to the database normally.

``` bash
python cli.py server start 8080
```

## Migration Test

### cnblogs

- 授权：https://www.cnblogs.com/yharimium/p/19338315
- 未授权：https://www.cnblogs.com/wang_yb/p/19336637

### csdn

- 授权：https://blog.csdn.net/Yharimium/article/details/155826111
- 未授权：https://blog.csdn.net/qq_43012298/article/details/139270957

### 简书

- 授权：https://www.jianshu.com/p/62361a7f52b3
- 未授权：https://www.jianshu.com/p/fd3067c20a32

### 稀土掘金

- 授权：https://juejin.cn/post/7582438310103466030
- 未授权：https://juejin.cn/post/7580616979472809990

### 语雀

- 授权：https://www.yuque.com/yharim-vfti3/ti9p8n/mxfagzycmiar9vfx
- 未授权：https://www.yuque.com/1874w/elog-docs/bry3d3lwe206xuor