# 中转站搭建 - 使用说明

> 基于 new-api 的本机 AI API 聚合面板

## 项目状态

✅ **Docker已安装，等待初始化完成**

### 当前情况
- Docker Desktop v4.91.0 已通过winget安装
- docker-compose.yml 配置已创建（端口3001，镜像v1.0.0-rc.38）
- Docker Desktop需要完成WSL2后端初始化

### 需要用户操作
1. 打开Docker Desktop（应该已自动启动）
2. 如果提示需要WSL2或重启，按提示操作  
3. 等待Docker Desktop状态栏显示绿色"Running"
4. 或者重启计算机完成初始化

### Docker就绪后立即执行
```bash
cd E:/new-api
docker compose up -d
# 然后访问 http://127.0.0.1:3001
```

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
