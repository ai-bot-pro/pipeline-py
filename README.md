<div align="center">
    <img src="https://github.com/user-attachments/assets/37c0d68d-c6d1-4e3b-a01e-d231c8ff36b6" alt="">
</div>

# apipeline
[![PyPI](https://img.shields.io/pypi/v/apipeline)](https://pypi.org/project/apipeline/)
<a href="https://app.commanddash.io/agent/github_ai-bot-pro_pipeline-py"><img src="https://img.shields.io/badge/AI-Code%20Agent-EB9FDA"></a>

> python --version >=3.10 with [asyncio-task](https://docs.python.org/3.11/library/asyncio-task.html)

- [pipeline-go](https://github.com/weedge/pipeline-go)

## Installation
- local To install apipeline(pipeline-python):
```
git clone https://github.com/weedge/pipeline-py
# install
cd pipeline-py && pip install .
# develop install
cd pipeline-py && pip install -e .
```
- install pipeline-py from pypi:
```
pip install apipeline
```

## Design
see [docs/design.md](https://github.com/weedge/pipeline-py/tree/main/docs/design.md)

<img width="1426" height="472" alt="image" src="https://github.com/user-attachments/assets/7eaafdd2-0778-4fb7-8d21-14c4f188eb87" />

系统指令frame
- CancelFrame: 系统退出指令，用于系统接受退出信号，清理退出系统
- ErrorFrame: 系统运行时错误指令
- StopTaskFrame: 停止任务指令
- StartInterruptionFrame: 中断指令，对于异步processor进行中断，直接切断异步buffer重启queue_frame; 如果有些模型内化了终端指令，发送给底层模型触发模型中断操作，或者停止流式输出
- StopInterruptionFrame: 停止中断指令
- MetricsFrame: 系统监控指标 (processor 运行时长; first token/chunk/byte time)


控制指令frame
- StartFrame: 系统开始运行指令，会携带初始参数：是否中断，是否监控等参数
- EndFrame: 结束运行指令，
- SyncFrame: 并行同步pipeline需要用到，输出口等到SyncFrame才把buffer的结果输出
- SyncNotifyFrame: 用于事件通知，广播


数据frame （主要是多模态数据 用于chatbot）
- TextFrame: 文本
- AudioRawFrame: 原始音频信息帧
- ImageRawFrame: 原始图片信息帧

应用frame 主要是正对业务场景来定义，这里提供一个基类


序列化主要是 PB(需要定义IDL schema 数据规范) 和 JSON 

Processor 分为 
- 同步 异步 processor 主要处理系统和控制层面的frame
- 针对多模态数据聚合类的processor
- 过滤processor 根据定义的过滤handler进行过滤处理
- 日志processor 更具过滤条件打印日志，便于frame 追踪调试
- 输入输出processor 对输入输出的frame进行分类处理，对应子类，或者组合类直接实现对应类型frame的处理

Pipeline 分为 串行，并行，并行同步 

整体定义总括如图红字所示


### pipeline
<img width="1120" height="306" alt="image" src="https://github.com/user-attachments/assets/3fa65a61-ac65-42f4-a967-953822344b0a" />
<img width="1135" height="303" alt="image" src="https://github.com/user-attachments/assets/51185563-7372-4899-837c-60b2d1d14283" />
<img width="1134" height="497" alt="image" src="https://github.com/user-attachments/assets/10a1b1cf-27ac-4661-834f-1879f6ea4aad" />
<img width="1387" height="523" alt="image" src="https://github.com/user-attachments/assets/2f3915a4-4860-4cee-ad6e-312744a424d2" />



### pipeline task runner
<img width="1241" height="471" alt="image" src="https://github.com/user-attachments/assets/d1364317-84e9-4440-8053-0da062fc016c" />


## Examples
see [examples](https://github.com/weedge/pipeline-py/tree/main/examples)


## Acknowledge
1. borrowed a lot of code from [pipecat](https://github.com/pipecat-ai/pipecat.git)















