# Bilibili Live Script

一个用于管理B站直播间连接的工具。

## 项目结构

```
bili-live-script/
├── main.py                  # 主入口文件
├── requirements.txt         # 依赖项
├── room_ids.json            # 房间ID配置
├── cookies.txt              # Cookie数据
├── config/                  # 配置文件目录
└── src/                     # 源代码
    ├── core/                # 核心功能模块
    │   ├── app.py           # 主应用类
    │   ├── room_manager.py  # 房间管理
    │   └── fleet_manager.py # 舰队管理
    ├── services/            # 服务模块
    │   ├── http_request_handler.py # HTTP请求处理
    │   └── config_manager.py       # 配置管理
    ├── config/              # 配置模块
    │   └── settings.py      # 全局配置
    └── utils/               # 工具模块
```

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python main.py
```

### 命令行参数

- `-d, --disconnect` - 只发送断开连接请求
- `-q, --quiet` - 发送退出请求到所有端口
- `-l, --login` - 发送登录请求（使用cookies.txt中的数据）
- `-c, --config CONFIG` - 配置文件路径，可以是：
  - 完整路径（例如：`/path/to/config.json`）
  - 相对路径（例如：`config/my-config.json`）
  - 文件名（例如：`my-config.json`）- 会在 `config/` 目录下查找
  - 不带参数 - 交互式选择配置文件
- `-t, --time SECONDS` - 在加载指定配置后等待指定秒数，然后重置为默认配置
- `-m, --message MESSAGE` - 发送自定义消息
- `-r, --room ROOM_ID` - 直接连接到指定的房间号
- `-f, --fleet FLEET_NUMS` - 指定要使用的舰队编号（如 "1,2,3"）。默认：使用所有舰队

### 示例

```bash
# 直接连接到房间号 12345（自动使用所有舰队）
python main.py -r 12345

# 直接连接到房间号 12345，并只使用特定的舰队
python main.py -r 12345 -f 1,3

# 断开所有连接
python main.py -d

# 登录并连接到房间
python main.py -l -r 12345

# 直接加载指定配置文件
python main.py -c config/my-settings.json

# 加载配置文件，等待 10 秒后重置为默认配置
python main.py -c config/my-settings.json -t 10

# 加载配置文件并同时连接到房间
python main.py -c config/my-settings.json -r 12345

# 组合多个操作：加载配置、等待时间、指定房间号、指定舰队
python main.py -c config/my-settings.json -t 10 -r 12345 -f 1,2 