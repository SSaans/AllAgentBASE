# 封装 Specification

## Purpose
规定统一包格式与清单文件的结构，让不同平台的表情包能用同一套方法读写。

## Requirements

### Requirement: 每个包带清单

系统 SHALL 为每个包生成清单文件，记录包名、表情列表与来源平台。

#### Scenario: 生成一个包

- **WHEN** 封装完成
- **THEN** 目录内有清单文件，能从中读出全部表情与来源

#### Scenario: 清单损坏

- **WHEN** 清单缺失或字段不全
- **THEN** 该包 SHALL 判为无效，不参与后续导入

### Requirement: 识别不靠扩展名

系统 SHALL 按文件头识别格式，不依赖扩展名判断。

#### Scenario: 扩展名写错

- **WHEN** 一个图片文件扩展名与实际格式不符
- **THEN** 系统仍能识别真实格式并正确处理
