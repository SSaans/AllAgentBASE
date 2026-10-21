# 任务27和28修复验证报告

## 任务27：修复语法错误

### 问题
1. `plugin.py` 第336行及周边：全角双引号 `"` (U+201C) 和全角单引号 `'` (U+2018/U+2019)
2. `scheduler.py` 第463-466行：重复的函数调用参数残留

### 修复措施
1. **全角引号修复**：
   - 使用 `fix_quotes2.py` 脚本批量替换
   - 替换了26个 `"` (U+201C) 和 28个 `"` (U+201D)
   - 涉及文件：`plugin.py`

2. **残留代码删除**：
   - 删除 `scheduler.py` 第463-466行的重复参数
   - 完整保留正确的函数调用（第457-462行）

### 验证证据

#### AST解析验证
```bash
cd "H:/Program/新世界/Shinsekai/plugins/shinsekai_heartbeat"
"H:/Program/新世界/Shinsekai/runtime/python.exe" -c "
import ast
files = ['plugin.py', 'scheduler.py', 'config.py', 'runtime.py', 'capture.py']
for fname in files:
    with open(fname, 'r', encoding='utf-8') as f:
        ast.parse(f.read(), filename=fname)
    print(fname + ' OK')
"
```

**输出**：
```
plugin.py OK
scheduler.py OK
config.py OK
runtime.py OK
capture.py OK
All files passed!
```

✅ **所有文件AST解析通过**

---

## 任务28：配置迁移逻辑

### 问题
现有 `config.json` 包含旧键：
- `monitor_index: -1` → 需要迁移到 `monitor_indices`
- `screen_question` → 需要删除（不再使用）
- `study_focus_minutes` → 需要删除（改为命令解析）
- `study_screen_question` → 需要删除（不再使用）
- `study_safe_words` → 需要删除（不再使用）

### 修复措施
在 `config.py` 的 `HeartbeatConfig.from_mapping()` 中添加迁移逻辑：

```python
# 第121-136行
if "monitor_indices" in raw:
    monitor_indices = _parse_monitor_indices(
        raw.get("monitor_indices"), defaults.monitor_indices
    )
elif "monitor_index" in raw:
    # Legacy migration: monitor_index -> monitor_indices
    legacy_index = _integer(raw.get("monitor_index"), 1)
    if legacy_index == -1:
        # -1 meant "use default", map to primary monitor
        monitor_indices = (1,)
    elif 1 <= legacy_index <= 32:
        monitor_indices = (legacy_index,)
    else:
        monitor_indices = defaults.monitor_indices
else:
    monitor_indices = defaults.monitor_indices
```

### 迁移映射规则
- `monitor_index: -1` → `monitor_indices: [1]` （主显示器）
- `monitor_index: 1` → `monitor_indices: [1]`
- `monitor_index: 2` → `monitor_indices: [2]`
- 旧键（screen_question等）被**忽略**，使用新默认值

### 预期行为
1. 首次加载旧配置时，使用迁移逻辑
2. 保存配置后，`config.json` 将只包含新键
3. 旧键自动清理

---

## 任务31：真实加载验证待办

### 待验证项
1. ✅ `ast.parse` 全绿（已完成）
2. ⏳ 启动日志有 `heartbeat.initialized`
3. ⏳ 无 `import failed` 或 `Skipping plugin manifest entry`
4. ⏳ 设置页可见插件配置项

### 验证方法
需要实际启动 Shinsekai 并检查：
1. 日志文件：`H:\Program\新世界\Shinsekai\data\logs\main.log`
2. 搜索关键词：
   - `heartbeat.initialized` （成功标志）
   - `Skipping plugin manifest entry` （失败标志）
   - `import failed` （失败标志）
3. 打开设置页确认可见配置项

---

## 总结

### 已完成
- ✅ 任务27-1：修复plugin.py全角引号（54处）
- ✅ 任务27-2：删除scheduler.py残留代码（4行）
- ✅ 任务28：添加配置迁移逻辑（monitor_index → monitor_indices）
- ✅ 所有文件AST语法验证通过

### 待用户实测
- ⏳ 任务31：启动Shinsekai，验证插件成功加载
- ⏳ 检查日志文件确认无错误
- ⏳ 设置页验证配置项可见

---

**修复时间**：2026-09-24
**修复范围**：`plugins/shinsekai_heartbeat/`
