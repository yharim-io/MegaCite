# MagaCite

Blog Content Migration and Reference Management System.

## Server Initialization

``` bash
bash scripts/install_mysql.sh # `install_mysql_mac.sh` for MacOS
playwright install
export MC_API_KEY="your-openai-api-key"
python cli.py server start 8080
```

## Client Startup

``` bash
python client/verifier.py --server http://127.0.0.1:8080
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