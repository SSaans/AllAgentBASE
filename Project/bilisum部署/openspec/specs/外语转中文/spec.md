# 外语转中文 Specification

## Purpose
规定外语视频的转写与翻译顺序，避免直接翻译导致时间轴错位。

## Requirements

### Requirement: 先转写原文再翻译

系统 SHALL 先得到原文转写，再把原文译成中文，保持时间戳对齐。

#### Scenario: 日语视频

- **WHEN** 输入一个日语视频
- **THEN** 输出中文转写，时间戳与原文一致

#### Scenario: 专有名词

- **WHEN** 原文含人名、作品名等专有名词
- **THEN** 译文 SHALL 保留原文或给出通用译名，不臆造新译
