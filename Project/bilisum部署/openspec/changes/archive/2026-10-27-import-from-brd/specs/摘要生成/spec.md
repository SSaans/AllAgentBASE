# 规格变更：摘要生成

## Purpose

规定摘要的结构与颗粒度，让读的人三十秒能判断这个视频值不值得看。

## ADDED Requirements

### Requirement: 摘要分层

系统 SHALL 输出一句总述加若干条要点，要点可回溯到原文位置。

#### Scenario: 生成摘要

- **WHEN** 转写完成后生成摘要
- **THEN** 输出一句总述与要点列表，每条要点标注对应的原文时间

#### Scenario: 内容空泛

- **WHEN** 视频内容本身没有实质信息
- **THEN** 摘要 SHALL 如实说明，不硬凑要点
