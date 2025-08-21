import unittest

from apipeline.frames.data_frames import AudioRawFrame, TextFrame, ImageRawFrame
from apipeline.serializers.protobuf import ProtobufFrameSerializer


"""
python -m unittest tests.serializer.test_protobuf_serializer.TestProtobufFrameSerializer.test_text
python -m unittest tests.serializer.test_protobuf_serializer.TestProtobufFrameSerializer.test_audio
python -m unittest tests.serializer.test_protobuf_serializer.TestProtobufFrameSerializer.test_image
"""


class TestProtobufFrameSerializer(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.serializer = ProtobufFrameSerializer()

    @unittest.skip("FIXED")
    async def test_skip(self):
        pass

    async def test_text(self):
        text_frame = TextFrame(text="hello world")
        frame = self.serializer.deserialize(self.serializer.serialize(text_frame))
        print(frame)
        self.assertEqual(frame, text_frame)

    async def test_audio(self):
        audio_frame = AudioRawFrame(audio=b"1234567890")
        frame = self.serializer.deserialize(self.serializer.serialize(audio_frame))
        print(frame)
        self.assertEqual(frame, audio_frame)

    async def test_image(self):
        image_frame = ImageRawFrame(
            image=b"1234567890",
            size=(1280, 720),
            format="JPEG",
            mode="RGB",
        )
        frame = self.serializer.deserialize(self.serializer.serialize(image_frame))
        print(frame)
        self.assertEqual(frame, image_frame)
