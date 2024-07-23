

- 每个processor只负责对应的frame数据
- 每个processor会启动一个异步队列和异步协程进行消费，提供外部接口queue_frame输入frame数据
- 异步协程获取到输入的数据后，根据上游还是下游方向通过push_frame进行下一步的处理输出

- pipeline输入frame请使用PipelineTask.queue_frame进行输入，不要直接使用自定义的输入queue进行输入
- pipeline输出frame请实现OutputProcessor中的sink方法，如果直接从sink队列中获取，可以使用OutputFrameProcessor这个类，通过callback获取数据进行处理

## 场景：
- 在多模态场景中，处理文本(富文本)，图片，音频，视频等实时在线内容的时候，会出现在同一时刻展现多个多模态数据，这个时候，在进行数据pipeline操作（对应的processor）时，需要对数据进行异步处理，这里用的异步队列任务方式处理，当需要同步时，设置同步事件。
- 如果是大数据处理，离线处理的情况，可以加速数据的处理，可能需要保留中间数据过程，数据格式一般是序列化列式存储，方便批量加载处理，常见的库[Apache Arrow](https://arrow.apache.org/)列格式，以及绿厂的[cudf](https://github.com/rapidsai/cudf)使用gpu加速处理， 这些操作processor作为todo事项以后实现
