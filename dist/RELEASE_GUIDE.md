# Release 创建指南

## 📦 已准备好的文件

以下文件已准备好，可以直接用于 Release：

### 主要文件
- **GamesaveAssistant.exe** (271KB) - 独立可执行文件
- **GamesaveAssistant_v1.5.tar.gz** (148KB) - 完整发布包

### 发布包内容
压缩包包含：
```
GamesaveAssistant_v1.5/
├── GamesaveAssistant.exe    # 主程序
├── data/                    # 默认配置目录
├── README.md                # 使用文档
```

---

## 🚀 在 GitHub 上创建 Release

### 方法 1：网页操作（推荐）

1. **访问 Releases 页面**
   ```
   https://github.com/lovefan-fan/Gamesaveassistant/releases
   ```

2. **点击 "Draft a new release"**

3. **填写信息**
   - **Tag version**: `v1.5`
   - **Release title**: `v1.5 - 网络同步功能和Docker部署`
   - **Description**: 复制下方的描述内容

4. **上传文件**
   - 点击 "Attach binaries by dropping them here or selecting them"
   - 选择 `GamesaveAssistant_v1.5.tar.gz`
   - 或者选择 `GamesaveAssistant.exe`

5. **点击 "Publish release"**

---

### Release 描述内容（复制粘贴）

```markdown
## 🎉 v1.5 版本发布 - 网络同步功能

### ✨ 新增功能

**网络同步系统**
- ✅ 多设备配置同步（拉取/推送/双向同步）
- ✅ 版本控制，防止配置冲突
- ✅ 自动机器ID识别
- ✅ 用户ID区分不同用户

**服务器端**
- ✅ Flask RESTful API
- ✅ Docker 多阶段构建（镜像仅 80MB）
- ✅ 一键部署（docker-compose）
- ✅ Windows 批处理脚本

**客户端界面**
- ✅ 网络设置面板（修复窗口高度）
- ✅ 同步管理面板
- ✅ 测试连接功能

### 📦 下载文件

- `GamesaveAssistant_v1.5.tar.gz` - 完整发布包（推荐）
- `GamesaveAssistant.exe` - 独立可执行文件（271KB）

### 🐳 Docker 部署

```bash
cd server
cp .env.example .env
# 编辑 .env 修改 ADMIN_PASSWORD
docker-compose up -d
```

### 🔧 客户端使用

1. 运行 `GamesaveAssistant.exe`
2. 点击 **【网络设置】**
3. 配置服务器地址和用户ID
4. 点击 **【测试连接】**
5. 点击 **【保存配置】**
6. 使用 **【同步管理】** 进行配置同步

### ⚠️ 安全提醒

**首次部署必须修改默认密码！**
编辑 `server/.env`：
```env
ADMIN_PASSWORD=your_secure_password
```

### 📋 完整功能

- ✅ 自动监控游戏关闭并备份
- ✅ 多设备网络同步
- ✅ 版本控制防冲突
- ✅ Docker 一键部署
- ✅ 支持多用户/多团队

### 🔗 相关链接

- **完整文档**: [README.md](https://github.com/lovefan-fan/Gamesaveassistant/blob/main/README.md)
- **服务器文档**: [server/README.md](https://github.com/lovefan-fan/Gamesaveassistant/blob/main/server/README.md)
- **API 文档**: 见 README.md 的 API 章节

### 📊 变更统计

- **20个文件** 新增/修改
- **1966行代码** 新增
- **提交**: [a1a0dd7](https://github.com/lovefan-fan/Gamesaveassistant/commit/a1a0dd7)

---

**祝使用愉快！** 🎮✨
```

---

## 📝 提交历史

当前版本基于以下提交：
- `a1a0dd7` - fix: 修复网络设置窗口高度问题，添加打包文件
- `b2c92ad` - feat: 新增网络同步功能和Docker部署支持

---

## 🎯 快速检查清单

- [ ] 已创建 v1.5 标签
- [ ] 已推送标签到远程
- [ ] 已准备 Release 描述
- [ ] 已上传打包文件
- [ ] 已发布 Release

---

## 💡 提示

如果 GitHub CLI (gh) 已安装，可以使用命令行创建 Release：

```bash
gh release create v1.5 \
  --title "v1.5 - 网络同步功能和Docker部署" \
  --notes-file RELEASE_GUIDE.md \
  dist/GamesaveAssistant_v1.5.tar.gz \
  dist/GamesaveAssistant.exe
```
