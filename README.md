<div align="center">
    <img src="https://github.com/user-attachments/assets/37c0d68d-c6d1-4e3b-a01e-d231c8ff36b6" alt="">
</div>

# apipeline
[![PyPI](https://img.shields.io/pypi/v/apipeline)](https://pypi.org/project/apipeline/)

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
- InterruptionTaskFrame: 终端任务指令，source 收到InterruptionTaskFrame 发送InterruptionFrame，用于语音文本流中断
- StartInterruptionFrame/InterruptionFrame: 中断指令，对于异步processor进行中断，直接切断异步buffer重启queue_frame; 如果有些模型内化了终端指令，发送给底层模型触发模型中断操作，或者停止流式输出
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

应用frame 主要是针对业务场景来定义，这里提供一个基类(结构)


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

- 串行同步处理：由同步 processor组成，upstream/downstream frame按链式顺序执行，每个pipeline有头和尾，分别是Source和Sinker, 用于和其他pipeline 的输入/输出 进行组装；

<img width="1166" height="313" alt="image" src="https://github.com/user-attachments/assets/d7640a07-338d-4e5e-a12d-ba8d6c5ea3bc" />

- 串行异步处理(包含同步processor)：由异步/同步 processor组成，异步processor在同步processor的基础上加入了upstream/downstream 异步队列buffer，以及对应异步处理upstream/downstream frame handler 按链式顺序执行；(如果不不需要等待下一步processor的结果，可以使用异步方式处理，直接将frame通过queue_frame的方式写入队列buffer中, 由异步processor中的handler来异步处理调用process_frame)

<img width="1156" height="302" alt="image" src="https://github.com/user-attachments/assets/2356f97c-d968-43be-84d0-0b1358e745c9" />

- 并行异步处理：由多个串行的pipeline并行执行，彼此之间不需要同步；

  (注意：这里的并行指的流程上的并行，真正任务在运行时是并发工作)

<img width="1169" height="512" alt="image" src="https://github.com/user-attachments/assets/bd0bba96-4302-4335-8408-980dd0964e65" />

- 并行同步处理：由多个串行的pipeline并行执行，处理的upstream/downstream frame在出口处需要同步；同步实现使用up/down queue来缓存对应frame, 直到处理SyncFrame时，将queue中缓存的frame写入upstream/downstream；图中展示了整体流程

<img width="1445" height="544" alt="image" src="https://github.com/user-attachments/assets/ef0c9f67-b362-4e73-865b-3d6ef03b03a9" />



### pipeline task runner

由多个pipeline (比如有以上三种类型的pipeline：串行pipeline, 并行pipeline, 并行同步pipeline)组装成一个DAG processor； pipeline Task 中定义了一个Source processor 来对接组装好的DAG processor,  在程序启动运行时，通过runner发送控制/系统(StartFrame / MetricsFrame)指令；比如在实时聊天场景中，用户发起会话连接， 启动运行 pipeline Task时，会根据PipelineParams初始参数初始化StartFrame进行启动(也会根据是否监控来发送MetricsFrame进行监控信息收集)，DAG中的processor收到StartFrame之后，开始执行对应的启动流程(如果有对MetricsFrame进行处理，将processor中的监控信息写入MetricsFrame中进行收集)；如果会话结束，发起EndFrame; 如果结束这个任务(或者遇到系统错误需要结束时)，发起StopTaskFrame; 如果触发系统进程退出信号，发送CancelFrame, 进行清场，退出。

<img width="1241" height="471" alt="image" src="https://github.com/user-attachments/assets/d1364317-84e9-4440-8053-0da062fc016c" />


## Examples
see [examples](https://github.com/weedge/pipeline-py/tree/main/examples)


## Acknowledge
1. borrowed a lot of code from [pipecat](https://github.com/pipecat-ai/pipecat.git)





## License
- The code is released under the BSD 3-Clause License.
- The documents are licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-nd/4.0/">Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License</a>.
<a rel="license" href="http://creativecommons.org/licenses/by-nc-nd/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-nd/4.0/88x31.png" /></a>












