# 中转站搭建 - 使用说明

> 基于 new-api 的本机 AI API 聚合面板

## 项目状态

⚠️ **阻塞中** - 无法获取 new-api Windows 二进制包

### 当前问题
- GitHub 访问受限，无法下载 new-api 的 Windows amd64 版本
- 尝试的下载地址均返回 404 Not Found
- 本机未安装 Docker Desktop，无法使用容器方案

### 需要用户协助
请提供以下之一：
1. **手动下载** new-api Windows 版本到本机：
   - 访问：https://github.com/Calcium-Ion/new-api/releases
   - 下载适用于 Windows amd64 的版本（可能是 .exe 或 .zip）
   - 放置到：`E:\new-api\` 目录

2. **提供可用的下载镜像地址**

3. **或安装 Docker Desktop** 使用容器方案

## 已完成工作

### 阶段 0：环境确认 ✅
- [x] 环境复核：3000端口被占用，使用3001端口
- [x] 发行包信息：确认 Docker 镜像为 v1.0.0-rc.38

## 技术方案

### 目标架构
```
客户端 → 127.0.0.1:3001 → new-api面板 → 多个上游中转站 → AI模型
```

### 关键参数
- **端口**：3001（3000已被占用）
- **访问地址**：http://127.0.0.1:3001
- **客户端 Base URL**：http://127.0.0.1:3001/v1
- **数据目录**：E:\new-api\data（仓库外）
- **使用模式**：自用模式

### 仍需提供
- P1：上游中转站的站点地址和 API Key
- P2：该站支持的模型名列表

## 下一步

一旦获得 new-api 程序：
1. 启动并初始化面板
2. 配置上游渠道（需 P1/P2）
3. 创建令牌
4. 接入客户端（Cherry Studio / Claude Code）
5. 验收测试

## 相关文档
- `BRD.md` - 完整需求文档
- `Task.md` - 任务清单
- `CHANGELOG.md` - 变更日志
