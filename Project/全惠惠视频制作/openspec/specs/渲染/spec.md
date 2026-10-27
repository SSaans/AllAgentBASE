# 渲染 Specification

## Purpose
规定画面怎么生成、成片要达到什么规格，保证同样的输入能出同样的片子，中文与 logo 不出错。

## Requirements

### Requirement: 代码逐帧渲染

系统 SHALL 用代码逐帧渲染画面，不使用视频生成模型。

#### Scenario: 生成画面

- **WHEN** 按分镜渲染
- **THEN** 每一帧由程序绘制，同样的输入重复渲染结果一致

#### Scenario: 画面里有中文

- **WHEN** 镜头需要出现中文
- **THEN** 文字由渲染层写入，字库为可商用字体

### Requirement: 成片可复现

系统 SHALL 保留渲染脚本、素材与参数，使同一条片子能在日后原样重出。

#### Scenario: 需要改一个镜头

- **WHEN** 客户要求调整某一处
- **THEN** 改参数重渲染，不需要重剪整条片子

### Requirement: 交付规格固定

系统 SHALL 按既定分辨率、帧率与封装格式输出成片。

#### Scenario: 交付成片

- **WHEN** 渲染完成
- **THEN** 输出文件符合约定的分辨率与帧率，可直接投放
