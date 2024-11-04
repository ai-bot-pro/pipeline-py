import logging
import dataclasses

import apipeline.frames.protobufs.data_frames_pb2 as frame_protos

from apipeline.frames.data_frames import AudioRawFrame, Frame, TextFrame, ImageRawFrame
from .base_serializer import FrameSerializer


class ProtobufFrameSerializer(FrameSerializer):
    SERIALIZABLE_TYPES = {
        TextFrame: "text",
        AudioRawFrame: "audio",
        ImageRawFrame: "image",
    }

    SERIALIZABLE_FIELDS = {v: k for k, v in SERIALIZABLE_TYPES.items()}

    def __init__(self):
        pass

    def serialize(self, frame: Frame) -> str | bytes | None:
        proto_frame = frame_protos.Frame()
        if type(frame) not in self.SERIALIZABLE_TYPES:
            logging.warning(f"Frame type {type(frame)} is not serializable")
            return None

        # ignoring linter errors; we check that type(frame) is in this dict above
        proto_optional_name = self.SERIALIZABLE_TYPES[type(frame)]
        for field in dataclasses.fields(frame):
            value = getattr(frame, field.name)
            if not value:
                continue

            if (type(frame) == ImageRawFrame and field.name == "size" \
                and type(value)==tuple and len(value)==2):
                setattr(getattr(proto_frame, proto_optional_name), field.name, f"{value[0]}x{value[1]}")
            else:
                setattr(getattr(proto_frame, proto_optional_name), field.name, value)

        result = proto_frame.SerializeToString()
        return result

    def deserialize(self, data: str | bytes) -> Frame | None:
        """Returns a Frame object from a Frame protobuf. Used to convert frames
        passed over the wire as protobufs to Frame objects used in pipelines
        and frame processors.

        >>> serializer = ProtobufFrameSerializer()
        >>> serializer.deserialize(
        ...     serializer.serialize(OutputAudioFrame(data=b'1234567890')))
        InputAudioFrame(data=b'1234567890')

        >>> serializer.deserialize(
        ...     serializer.serialize(TextFrame(text='hello world')))
        TextFrame(text='hello world')

        """

        proto = frame_protos.Frame.FromString(data)
        which = proto.WhichOneof("frame")
        if which not in self.SERIALIZABLE_FIELDS:
            logging.error("Unable to deserialize a valid frame")
            return None

        args = getattr(proto, which)
        args_dict = {}
        for field in proto.DESCRIPTOR.fields_by_name[which].message_type.fields:
            args_dict[field.name] = getattr(args, field.name)

        # Remove id name
        if "id" in args_dict:
            del args_dict["id"]
        if "name" in args_dict:
            del args_dict["name"]

        # Create the instance
        class_name = self.SERIALIZABLE_FIELDS[which]
        if class_name == ImageRawFrame:
            size = args_dict["size"].split("x") if "size" in args_dict else []
            args_dict["size"] = (int(size[0]), int(size[1]))
        instance = class_name(**args_dict)

        # Set Frame id name
        if hasattr(args, "id"):
            setattr(instance, "id", getattr(args, "id"))
        if hasattr(args, "name"):
            setattr(instance, "name", getattr(args, "name"))

        return instance
