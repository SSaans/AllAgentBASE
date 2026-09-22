# shinsekai 专注监督改造验收报告

> 📅 验收日期：2026-09-22
> 👤 验收人：测试 Agent
> 📋 验收任务：任务 20-24 代码验收 + 任务 25 功能验收

---

## 一、代码验收结果（已完成）

### 1.1 文件结构验证 ✅

**新增文件**:
- `plugins/shinsekai_heartbeat/capture.py` (142 行) - 截图模块

**删除文件**:
- `plugins/shinsekai_heartbeat/vision.py` ✅
- `plugins/shinsekai_heartbeat/tests/test_vision.py` ✅

**修改文件**:
- `config.py` - 移除 4 个旧字段，新增 monitor_indices
- `plugin.py` - 更新设置页 schema
- `runtime.py` - 重写 detect_study_command()
- `scheduler.py` - 使用 capture.capture_screens()
- `requirements.txt` - 添加 mss>=9.0.0, Pillow>=10.0.0

### 1.2 Moondream 残留检查 ✅

**检查命令**: `grep -ri "moondream" . --include="*.py"`
**结果**: 无残留（Python 代码中已完全删除）
**备注**: 文档中的 Moondream 引用为历史记录，属正常

### 1.3 设置页字段变更验证 ✅

**已删除的 4 个字段** (按 BRD F6 要求):
- `monitor_index` (单数形式，旧字段)
- `screen_question`
- `study_screen_question`
- `study_focus_minutes`
- `study_safe_words`

**新增字段**:
- `monitor_indices` (配置中，tuple[int, ...])
- `monitor_indices_text` (设置页中，逗号分隔字符串)

**验证方法**: `grep -E "(旧字段名)" config.py` 无结果

### 1.4 依赖声明检查 ✅

**requirements.txt 内容**:
```
# Screen capture dependencies
mss>=9.0.0
Pillow>=10.0.0
```

### 1.5 核心功能代码审查 ✅

#### 任务 20+23: 截图能力搬运 + 多显示器
- `capture.py` 实现完整:
  - `configure_capture()` - 配置数据目录
  - `capture_screens(monitor_indices)` - 支持多显示器
  - `cleanup_old_screenshots(retention_days)` - 自动清理
  - 单次加锁 `_capture_lock` 防重入 ✅
  - 仅清理 `heartbeat-screen-*` 前缀 ✅
  - 附件协议: `{"kind":"image","mimeType":"image/png",...}` ✅

#### 任务 21: 专注命令解析
- `runtime.py` 中 `detect_study_command()`:
  - 正则提取时长: `r"(?:专注|学习)(?:(\d+)(?:分钟?|min|分))?"`
  - 提取目标: `(?:做|学|写|看|复习)?(.+?)`
  - 未写时长默认 None (scheduler 中默认 30)
  - 时长范围钳位: 1-240 分钟 ✅
  - 兼容旧口令: "我要学习请监督我" ✅

#### 任务 22: 弃用 Moondream
- `vision.py` 已删除 ✅
- `scheduler.py` 中:
  - 移除 `screen_reader` / `study_screen_reader` 参数
  - `_tick_study()` 改为 `capture.capture_screens()` ✅
  - `tick()` 识屏模式改为截图 + 主模型判断 ✅

#### 任务 24: 设置页清理与提示词重写
- 提示词改为中文 ✅
- 设置页新增 `monitor_indices_text` 字段 ✅
- 中英文 i18n 同步 ✅

---

## 二、功能验收结果（需用户实测）

### 2.1 验收范围

按 BRD「迭代需求：专注监督改造」验收标准:

#### 功能验收项（需实际运行测试）
- [ ] 专注命令解析（带时长）: "我现在开始专注30分钟，做数学作业"
- [ ] 专注命令解析（不带时长）: "我现在开始专注" → 默认 30 分钟
- [ ] 专注期间识屏: 每「检查间隔」分钟截图 + 主模型判断
- [ ] 分心提醒: 切到游戏/娱乐视频 → 开口提醒
- [ ] 保持安静: 认真学习 → 不说话
- [ ] 到时提醒: 30 分钟后提醒休息并自动结束
- [ ] 多显示器截图: 设置 `1,2` → 两张截图一起发
- [ ] 单显示器截图: 设置 `1` → 只截主屏
- [ ] 心跳自带截图: 禁用外部识屏插件后仍能截图
- [ ] 设置页: 4 个旧字段已删除，monitor_indices_text 已添加

#### 五场景验收（BRD「验收边界」）
- [ ] 场景 1 - 未启动: 无心跳调度、无 TTS、无截图
- [ ] 场景 2 - 仅设置页: 不得继续心跳调度与自言自语
- [ ] 场景 3 - 使用中: 空闲触发、识屏 50/自言自语 25/提问 25
- [ ] 场景 4 - 退出: 调度停止、TTS 退出、历史落盘
- [ ] 场景 5 - 再启动: 单实例、历史恢复、空闲计时重新起算

### 2.2 验收阻塞点

**代码验收已完成，但功能验收需要以下实际运行环境**:

1. **启动 Shinsekai 程序** - 需要用户手动启动 `H:\Program\新世界\Shinsekai\shinsekai.exe`
2. **观察日志输出** - 查看 `logs/main.log` 中的心跳触发、截图生成、专注命令识别
3. **交互测试** - 向桌宠发送专注命令，观察识别和回复
4. **多显示器环境** - 测试多显示器截图需要实际多屏设备
5. **模型识屏验证** - 确认截图作为附件发送给主模型，且模型基于图片内容回复
6. **语音和 UI 验证** - TTS 语音播报、界面展示、历史保存

### 2.3 风险提示（BRD R2/R3）

⚠️ **R2 - 多附件未实测**: 多显示器截图会产生多个附件，需验证在「模型、历史保存、UI」三处的表现
⚠️ **R3 - 插件更新覆盖**: 心跳插件是市场插件，本地改动会被插件更新覆盖，需版本控制或 fork

---

## 三、验收结论

### 3.1 代码层面验收结论：✅ **通过**

**已验证项**:
1. ✅ 截图能力已搬进心跳插件（capture.py）
2. ✅ 多显示器支持已实现（monitor_indices 参数）
3. ✅ Moondream 已完全删除（vision.py + Python 代码无残留）
4. ✅ 专注命令解析已实现（时长提取 + 目标提取 + 默认 30 分钟）
5. ✅ 设置页字段已更新（4 项删除，monitor_indices_text 新增）
6. ✅ 依赖已声明（mss + Pillow）
7. ✅ scheduler 已改用 capture.capture_screens()
8. ✅ 提示词已改中文

**代码质量**:
- 文件结构清晰，模块职责明确
- 错误处理完善（截图失败回退到非屏幕模式）
- 线程安全（_capture_lock 防重入）
- 日志完整（event 标记便于追踪）

### 3.2 功能层面验收结论：⚠️ **需用户实测**

**原因**: 端到端功能验收需要实际运行环境:
- 启动桌宠程序
- 观察心跳触发、截图生成
- 测试专注命令解析和识别
- 验证多显示器截图
- 确认模型识屏效果
- 观察 TTS 语音和 UI 表现
- 验证五场景行为（启动/退出/设置页等）

**建议测试步骤**:
1. 启动 Shinsekai (`shinsekai.exe`)
2. 打开日志监控: `tail -f "H:/Program/新世界/Shinsekai/logs/main.log"`
3. 测试专注命令: "我现在开始专注30分钟，做测试任务"
4. 观察心跳日志: `heartbeat.capture.success` / `heartbeat.emitted`
5. 测试多显示器: 设置页改为 `1,2`，观察是否生成两张截图
6. 验证识屏: 切换不同屏幕内容，观察桌宠回复是否基于截图
7. 测试五场景: 启动/退出/设置页/再启动，观察进程和日志

---

## 四、下一步建议

### 给用户
1. **安装依赖**: `pip install mss>=9.0.0 Pillow>=10.0.0`（如果 Shinsekai 环境尚未安装）
2. **启动测试**: 运行 shinsekai.exe，按上述步骤测试
3. **报告结果**: 测试后反馈功能是否正常、有无报错

### 给开发 Agent
如果用户测试发现问题:
- 提供详细日志片段（`logs/main.log` 中的相关事件）
- 截图文件路径和大小
- 实际回复内容 vs 期望行为

### 验收办结条件
- 用户完成上述功能测试
- 所有功能验收项通过
- 五场景验收通过
- 无阻塞性 Bug

---

## 附录：文件清单

**运行目录**: `H:\Program\新世界\Shinsekai\plugins\shinsekai_heartbeat\`

**改动文件**:
- capture.py (新建，142 行)
- config.py (修改，移除 4 字段 + 新增 monitor_indices)
- plugin.py (修改，设置页 schema)
- runtime.py (修改，detect_study_command 重写)
- scheduler.py (修改，使用 capture 模块)
- requirements.txt (修改，添加依赖)
- README.md (修改，同步文档)
- vision.py (删除)
- tests/test_vision.py (删除)

**本仓库文档**:
- BRD.md (需求和验收标准)
- Task.md (任务清单)
- CHANGELOG.md (变更记录)
- 本报告 (TESTING_REPORT_20260922.md)
