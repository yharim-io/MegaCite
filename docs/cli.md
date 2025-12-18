---
title: MegaCite CLI 方案
---

# MegaCite - 命令行(CLI) 方案

## 1. 服务器 CLI (mc-server)

### mc-server start `<port>`

- **Description**: 在后台启动 MegaCite 服务器进程并监听端口 `<port>`。
- **Params**:
    - `<port>`: 服务器监听的端口号。
        - **Option**: 1024-65535
- **Return**:
    - `{'Success': 'Server started on port <port>.'}`
    - `{'Error': 'Port <port> is already in use.'}`
    - `{'Error': 'Invalid port number.'}`

### mc-server stop `<port>`

- **Description**: 停止在端口 `<port>` 上运行的 MegaCite 服务器进程。
- **Params**:
    - `<port>`: 正在运行的服务器端口号。
        - **Option**: 1024-65535
- **Return**:
    - `{'Success': 'Server on port <port> stopped.'}`
    - `{'Error': 'Server is not running on port <port>.'}`
    - `{'Error': 'Invalid port number.'}`

### mc-server status `<port>`

- **Description**: 检查端口 `<port>` 上 MegaCite 服务器进程的状态。
- **Params**:
    - `<port>`: 正在运行的服务器端口号。
        - **Option**: 1024-65535
- **Return**:
    - `{'Success': 'Server is running. (PID: <pid>, Port: <port>)'}`
    - `{'Error': 'Server is not running on port <port>.'}`
    - `{'Error': 'Invalid port number.'}`

### mc-server list

- **Description**: 列出所有正在运行的 MegaCite 服务器端口。
- **Return**:
    - `{'Success': ['<port 1>', '<port 2>']}`

### mc-server logs `<port>` [`<lines>`]

- **Description**: 查看端口 `<port>` 服务器的日志，可选择显示最近 `<lines>` 行。
- **Params**:
    - `<port>`: 正在运行的服务器端口号。
        - **Option**: 1024-65535
    - `[<lines>]`: 指定要显示的最新日志行数。
        - **Default**: 20
- **Return**:
    - `{'Success': [{'timestamp': '<timestamp 1>', 'message': '<message 1>'}, {'timestamp': '<timestamp 2>', 'message': '<message 2>'}]}`
    - `{'Error': 'Server is not running on port <port>.'}`
    - `{'Error': 'Invalid port number.'}`

-----

## 服务器 CLI 示例

```bash
# 1. 启动服务器
$ mc-server start 8080
{'Success': 'Server started on port 8080.'}


# 2. 尝试在同一端口再次启动
$ mc-server start 8080
{'Error': 'Port 8080 is already in use.'}


# 3. 启动另一个服务器
$ mc-server start 9000
{'Success': 'Server started on port 9000.'}


# 4. 列出所有正在运行的服务器
$ mc-server list
{'Success': ['8080', '9000']}

# 5. 检查特定服务器的状态
$ mc-server status 8080
{'Success': 'Server is running. (PID: 12345, Port: 8080)'}


# 6. 查看日志 (JSON 格式)
$ mc-server logs 8080 2
{'Success': [
	{'Timestamp': '2025-11-03 18:00:01', 'message': 'Server log entry...'},
	{'Timestamp': '2025-11-03 18:00:05', 'message': 'Server log entry...'}
]}

# 7. 停止服务器
$ mc-server stop 8080
{'Success': 'Server on port 8080 stopped.'}


# 8. 再次检查状态
$ mc-server status 8080
{'Error': 'Server is not running on port 8080.'}
```

-----

## 2. 客户端 CLI (mc)

### mc connect `<address>`

- **Description**: 配置客户端以连接到地址 `<address>` 的 MegaCite 服务器。
- **Params**:
    - `<address>`: 服务器的地址和端口。
        - **Option**: ip:port
- **Return**:
    - `{'Success': 'Connected: <address>'}`
    - `{'Error': 'Invalid address Option.'}`

### mc register `<username>` `<password>`

- **Description**: 使用用户名 `<username>` 和密码 `<password>` 在服务器上注册一个新用户。
- **Params**:
    - `<username>`: 用户名。
        - **Option**: 3-20位, 仅限字母、数字、下划线。
    - `<password>`: 密码。
        - **Option**: 最少8位, 最多128位, 必须包含字母和数字。
- **Return**:
    - `{'Success': 'User <username> registered successfully.'}`
    - `{'Error': 'Invalid username or password.'}`
    - `{'Error': 'Username already exists.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`

### mc login `<username>` `<password>`

- **Description**: 使用用户名 `<username>` 和密码 `<password>` 登录到 MegaCite 服务器。
- **Params**:
    - `<username>`: 用户名。
        - **Option**: 3-20位, 仅限字母、数字、下划线。
    - `<password>`: 密码。
        - **Option**: 最少8位, 最多128位, 必须包含字母和数字。
- **Return**:
    - `{'Success': 'Login successful.'}`
    - `{'Error': 'Invalid username or password.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`

### mc logout

- **Description**: 清除本地保存的登录凭证, 退出登录。
- **Return**:
    - `{'Success': 'Logged out.'}`
    - `{'Error': 'Not logged in.'}`

### mc reset password `<old_password>` `<new_password>`

- **Description**: 使用旧密码 `<old_password>` 验证后修改为新密码 `<new_password>`。
- **Params**:
    - `<old_password>`: 用户的当前密码。
        - **Option**: 最少8位, 最多128位, 必须包含字母和数字。
    - `<new_password>`: 用户的新密码。
        - **Option**: 最少8位, 最多128位, 必须包含字母和数字。
- **Return**:
    - `{'Success': 'Password reset successfully.'}`
    - `{'Error': 'Incorrect old password.'}`
    - `{'Error': 'Invalid new password.'}`
    - `{'Error': 'Not logged in.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`

### mc auth add `<platform>`

- **Description**: 添加平台 `<platform>` 的外部认证。此命令会弹出浏览器，要求登录目标网站以完成认证。
- **Params**:
    - `<platform>`: 要认证的外部平台。
        - **Option**: `csdn`, `cnblogs`, `wordpress`, `jianshu` 等。
- **Return**:
    - `{'Success': 'Authentication for <platform> added successfully.'}`
    - `{'Error': 'Platform <platform> not supported.'}`
    - `{'Error': 'Authentication failed or was cancelled.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`
    - `{'Error': 'Not logged in.'}`

### mc auth list

- **Description**: 列出所有已在服务器上认证的外部平台。
- **Return**:
    - `{'Success': ['<Platform 1>', '<Platform 2>']}`
    - `{'Error': 'Not logged in.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`

### mc auth remove `<platform>`

- **Description**: 删除平台 `<platform>` 的已保存的外部认证信息。
- **Params**:
    - `<platform>`: 要删除认证的外部平台。
        - **Option**: `csdn`, `cnblogs`, `wordpress`, `jianshu` 等。
- **Return**:
    - `{'Success': 'Authentication for <platform> removed.'}`
    - `{'Error': 'Authentication for <platform> not found.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`
    - `{'Error': 'Not logged in.'}`

### mc post list [`<count>`]

- **Description**: 列出服务器上最新加入的 `<count>` 篇文章的内容 ID (CID)。
- **Params**:
    - `[<count>]`: 要显示的文章数量。
        - **Default**: 20
- **Return**:
    - `{'Success': ['<cid 1>', '<cid 2>']}`
    - `{'Error': 'No posts found.'}`
    - `{'Error': 'Not logged in.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`

### mc post create

- **Description**: 创建一篇新文章, 服务器将为其分配处一个唯一的 cid。服务器会自动使用当前时间填充 `date` 字段。
- **Return**:
    - `{'Success': '<cid>'}`
    - `{'Error': 'Post creation failed: Server error.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`
    - `{'Error': 'Not logged in.'}`

### mc post set `<cid>` `<field>` `<newvalue>`

- **Description**: 修改文章 `<cid>` 的字段 `<field>` 为新值 `<newvalue>`。
- **Params**:
    - `<cid>`: 要更新的文章的内容 ID。
    - `<field>`: 要修改的字段。
        - **Option**: `context`, `title`, `date`, `description`, `category`
    - `<newvalue>`: 字段的新值 (必须是字符串)。
        - **Option**: `date` 字段必须使用 `YYYY-MM-DD` 格式。
- **Return**:
    - `{'Success': 'Post <cid> updated.'}`
    - `{'Error': 'Post <cid> not found.'}`
    - `{'Error': 'Invalid field: <field>.'}`
    - `{'Error': 'Invalid date Option. Use YYYY-MM-DD.'}`
    - `{'Error': 'Post update failed: Server error.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`
    - `{'Error': 'Not logged in.'}`

### mc post get `<cid>` `<field>`

- **Description**: 查看文章 `<cid>` 的字段 `<field>` 的内容。
- **Params**:
    - `<cid>`: 要查看的文章的内容 ID。
    - `<field>`: 要查看的字段。
        - **Option**: `context`, `title`, `date`, `description`, `category`
- **Return**:
    - `{'Success': '<value>'}`
    - `{'Error': 'Post <cid> not found.'}`
    - `{'Error': 'Invalid field: <field>.'}`
    - `{'Error': 'Not logged in.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`

### mc post delete `<cid>`

- **Description**: 删除文章 `<cid>`。
- **Params**:
    - `<cid>`: 要删除的文章的内容 ID。
- **Return**:
    - `{'Success': 'Post <cid> deleted.'}`
    - `{'Error': 'Post <cid> not found.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`
    - `{'Error': 'Not logged in.'}`

### mc post migrate `<url>`

- **Description**: 从 URL `<url>` 迁移一篇文章。服务器将自动验证该文章是否属于已认证的用户。
- **Params**:
    - `<url>`: 要迁移的文章的完整 URL。
        - **Option**: http://... 或 https://...
- **Return**:
    - `{'Success': '<cid>'}`
    - `{'Error': 'Authentication for <platform> not found. Run 'mc auth add <platform>'}`
  - `{'Error': 'This article does not belong to the authenticated user.'}`
    - `{'Error': 'URL is invalid or unreachable.'}`
    - `{'Error': 'Server error.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`
    - `{'Error': 'Not logged in.'}`

### mc search `<keyword>`

- **Description**: 按关键字 `<keyword>` 模糊搜索文章。命中优先级: 标题 > description > 正文。
- **Params**:
    - `<keyword>`: 搜索关键字。
- **Return**:
    - `{'Success': ['<cid 1>', '<cid 2>']}`
    - `{'Error': 'No results found.'}`
    - `{'Error': 'Not logged in.'}`
    - `{'Error': 'Connection failed: Server unreachable.'}`

-----

## 客户端 CLI 示例

```bash
# 1. 连接服务器 (假设服务器在 114.114.114.114:8080 运行)
$ mc connect 114.114.114.114:8080
{'Success': 'Server address saved: 114.114.114.114:8080'}


# 2. 注册新用户 (用户名太短)
$ mc register my PaSswoRd123
{'Error': 'Invalid username or password.'}


# 3. 注册成功
$ mc register my_user PaSswoRd123
{'Success': 'User my_user registered successfully.'}


# 4. 登录
$ mc login my_user PaSswoRd123
{'Success': 'Login successful.'}


# 5. 添加 CSDN 认证 (将打开浏览器)
$ mc auth add csdn
{'Success': 'Authentication for csdn added successfully.'}


# 6. 创建一篇新文章 (假设返回 cid: aK8sLd9zP)
$ mc post create
{'Success': 'aK8sLd9zP'}

# 7. 为文章 aK8sLd9zP 添加标题
$ mc post set aK8sLd9zP title "My First Post"
{'Success': 'Post aK8sLd9zP updated.'}

# 8. 为文章 aK8sLd9zP 添加正文
$ mc post set aK8sLd9zP context "Hello world, this is the content."
{'Success': 'Post aK8sLd9zP updated.'}

# 9. 从 CSDN 迁移文章 (假设返回 cid: qP1oXb4rT)
$ mc post migrate https://blog.csdn.net/my_user/article/details/12345678
{'Success': 'qP1oXb4rT'}


# 10. 查看文章 aK8sLd9zP 的标题
$ mc post get aK8sLd9zP title
{'Success': 'My First Post'}

# 11. 搜索文章
$ mc search "First Post"
{'Success': ['aK8sLd9zP']}

# 12. 列出所有文章
$ mc post list
{'Success': ['aK8sLd9zP', 'qP1oXb4rT']}

# 13. 删除文章 aK8sLd9zP
$ mc post delete aK8sLd9zP
{'Success': 'Post aK8sLd9zP deleted.'}


# 14. 修改密码
$ mc reset password PaSswoRd123 NewS3curePass!
{'Success': 'Password reset successfully.'}

# 15. 退出登录
$ mc logout
{'Success': 'Logged out.'}


# 16. 尝试在未登录时操作
$ mc post list
{'Error': 'Not logged in.'}
```