# 视觉规范 Specification

## Purpose
规定版面上的 logo、字体与配色规则，让每天产出的图看起来像同一个品牌，而不是三张互不相干的图。

## Requirements

### Requirement: logo 位置与比例固定

系统 SHALL 在每张成品上按固定位置与比例放置 logo，不随画面内容随意挪动。

#### Scenario: 输出成品

- **WHEN** 渲染一张图
- **THEN** logo 出现在既定位置，尺寸比例符合基线，不拉伸变形

### Requirement: 只用可商用字体

系统 SHALL 只使用免费可商用的字库。

#### Scenario: 选用字体

- **WHEN** 模板需要一种新字体
- **THEN** 该字体 SHALL 有明确的可商用授权，授权说明随模板留档

#### Scenario: 授权不明

- **WHEN** 字体授权无法确认
- **THEN** 不得用于成品

### Requirement: 文字层级在缩略图下仍可读

系统 SHALL 让标题、副标题、正文的主次在缩小到社交平台缩略图尺寸时依然清晰。

#### Scenario: 缩略图检查

- **WHEN** 把成品缩小到手机信息流尺寸
- **THEN** 标题可读，正文不糊成一片，主次仍分得清
