- 每个processor只负责对应的frame数据

  Each processor is only responsible for the corresponding frame data
  
- 每个processor会启动一个异步队列和异步协程进行消费，提供外部接口queue_frame输入frame数据

  Each processor will start an asynchronous queue and asynchronous coroutine for consumption, and provide the external interface queue_frame to input frame data.
  
- 异步协程获取到输入的数据后，根据上游还是下游方向通过push_frame进行下一步的处理输出

  After the asynchronous coroutine obtains the input data, it performs the next step of processing and output through push_frame according to the upstream or downstream direction.
  
- pipeline输入frame请使用PipelineTask.queue_frame进行输入，不要直接使用自定义的输入queue进行输入

  Please use PipelineTask.queue_frame for pipeline input frame. Do not directly use a custom input queue for input.
  
- pipeline输出frame请实现OutputProcessor中的sink方法，如果直接从sink队列中获取，可以使用OutputFrameProcessor这个类，通过callback获取数据进行处理

  For the pipeline output frame, please implement the sink method in OutputProcessor. If you obtain it directly from the sink queue, you can use the OutputFrameProcessor class to obtain the data through callback for processing.

## 场景： Scenes:

- 在多模态场景中，处理文本(富文本)，图片，音频，视频等实时在线内容的时候，会出现在同一时刻展现多个多模态数据，这个时候，在进行数据pipeline操作（对应的processor）时，需要对数据进行异步处理，这里用的异步队列任务方式处理，当需要同步时，设置同步事件。

  In a multi-modal scenario, when processing real-time online content such as text (rich text), pictures, audio, and video, multiple multi-modal data will be displayed at the same time. At this time, during the data pipeline operation (corresponding processor), the data needs to be processed asynchronously. The asynchronous queue task method is used here. When synchronization is required, synchronization events are set.
  
- 如果是大数据处理，离线处理的情况，可以加速数据的处理，可能需要保留中间数据过程，数据格式一般是序列化列式存储，方便批量加载处理，常见的库[Apache Arrow](https://arrow.apache.org/)列格式，以及绿厂的[cudf](https://github.com/rapidsai/cudf)使用gpu加速处理("绿箭")， 这些操作processor作为todo事项以后实现

  If it is big data processing, offline processing can speed up the data processing, and the intermediate data process may need to be retained. The data format is generally serialized column storage, which facilitates batch loading processing. The common library Apache Arrow column format, and Green Factory cudf uses gpu accelerated processing, and these operations processor will be implemented as todo items later.
