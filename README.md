# 游戏存档自动备份助手

一个用于管理游戏存档备份的桌面工具，当前代码已经按职责拆分为备份、配置、网络、进程、界面和通用工具模块，便于继续维护和打包。

## 功能简介

- 自动监控游戏进程，在退出后执行备份
- 支持手动备份、恢复和历史记录查看
- 支持网络同步配置
- 支持 Windows 打包为独立可执行文件

## 运行环境

- Python 3.8 及以上
- Windows

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动方式

开发环境请直接从新的入口文件启动：

```bash
python code/main.py
```

## 打包方式

使用项目根目录下的打包脚本：

```bash
python build_exe.py
```

打包输出位于 `dist/` 目录，程序运行依赖的 `Viewallprocesses.exe` 会一并复制到该目录。

## 项目结构

```text
Gamesaveassistant/
├── code/
│   ├── main.py                  # 客户端启动入口
│   ├── backup/                  # 备份、压缩、历史记录、监控逻辑
│   ├── config/                  # 本地配置与网络配置管理
│   ├── data/                    # 本地数据文件与日志目录
│   ├── network/                 # 网络同步客户端
│   ├── process/                 # 进程检测相关逻辑
│   ├── ui/                      # 图形界面
│   ├── utils/                   # 路径、日志等通用工具
│   └── Viewallprocesses.exe     # 进程查看工具
├── server/                      # 服务端代码与部署文件
├── build_exe.py                 # Windows 打包脚本
├── GamesaveAssistant.spec       # PyInstaller 配置
├── requirements.txt             # 项目依赖
└── README.md
```

## 服务端

如果需要使用同步服务端：

```bash
cd server
pip install -r requirements.txt
python server.py
```

也可以使用 `server/` 目录中的 Docker 相关文件进行部署。

## 说明

- 本地配置数据默认位于 `code/data/`
- 打包后的可执行文件运行时会在 exe 同级目录读取数据文件和 `Viewallprocesses.exe`
