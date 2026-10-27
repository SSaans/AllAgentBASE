# 安全审查 Specification

## Purpose
规定外部技能装进仓库前的安全检查项，避免把带脚本、带外联的包引进来。

## Requirements

### Requirement: 装前扫描

系统 SHALL 在入库前检查包内文件，识别脚本、网络请求与凭据索取行为。

#### Scenario: 包内带外联脚本

- **WHEN** 扫描发现包内文件会向外部地址发请求
- **THEN** 该包 SHALL 不予入库，除非有明确说明且用户同意

#### Scenario: 纯文本包

- **WHEN** 包内只有说明文档与参考资料
- **THEN** 判定为低风险，可入库并记录扫描结论

### Requirement: 许可证要能追溯

系统 SHALL 记录每个外部技能的上游地址与许可证，无法追溯的不入库。

#### Scenario: 上游没有许可证

- **WHEN** 包内无 LICENSE 且上游未声明
- **THEN** 仅可留档自用，标注「不外发、不收费分发」
