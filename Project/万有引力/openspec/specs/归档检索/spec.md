# 归档检索 Specification

## Purpose
规定如何从已归档的记录里快速定位到某段对话，避免在几个大文件里翻找。

## Requirements

### Requirement: 按会话与时间定位

系统 SHALL 支持给定会话标识与时间范围，返回该范围内的消息。

#### Scenario: 查某天的对话

- **WHEN** 指定会话与某一天
- **THEN** 系统返回当天该会话的全部消息，按时间排序

#### Scenario: 范围无记录

- **WHEN** 指定范围内没有任何消息
- **THEN** 系统 SHALL 明确回复无记录，不返回空白结果让人误以为出错

### Requirement: 关键词检索

系统 SHALL 支持按关键词在归档中检索，并给出命中上下文。

#### Scenario: 搜一个词

- **WHEN** 输入一个关键词
- **THEN** 系统返回命中的消息及其前后各若干条，便于判断语境
