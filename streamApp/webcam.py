import argparse
import asyncio
import json
import logging
import os
import ssl
import traceback
import uuid
import time

import cv2
from av import VideoFrame

from google.cloud import speech

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from django.http import HttpResponse

from streamApp import media
from streamApp.media import mp_holistic

from streamApp.Grammar.traitementGrammaire import StructurePhrase
from streamApp.streamRecog import MicrophoneStream, listen_print_loop, get_speaker

logger = logging.getLogger("pc")
pcs = set()

infoColor1 = (0, 255, 0)
infoColor2 = (0, 255, 255)
infoColor = infoColor1


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, dc):
        super().__init__()  # don't forget this!
        self.track = track
        self.dc = dc
        self.holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        self.prevTime = time.time()
        self.starttime1 = time.time()
        self.skipFrames = True
        self.realFPS = 0
        self.prevGoodFrame = None
        self.frameCount = 0
        self.prevFrameCount = 0
        self.frameProcessedCount = 0

        self.last_word = "stop"

    async def recv(self):
        global infoColor
        # TODO: interface LSFIA
        frame = await self.track.recv()
        new_frame = frame
        self.frameCount = self.frameCount + 1
        self.frameProcessedCount = self.frameProcessedCount + 1

        timer = cv2.getTickCount()
        # perform edge detection

        if self.skipFrames:
            while not self.track._queue.empty():
                frame = await self.track.recv()
                self.frameCount = self.frameCount + 1

        self.frameProcessedCount = self.frameProcessedCount + 1

        timer = cv2.getTickCount()

        try:
            img = frame.to_ndarray(format="bgr24")

            rows, cols, _ = img.shape
            h, w, _ = img.shape
            rows, cols, _ = img.shape

            y = h // 3
            x = w // 3

            image, results = media.mediapipe_detection(img, self.holistic)
            # (results)

            timeVal = str(timer)
            y1 = y

            if True:
                cv2.putText(img, "Alg: " + "mediapipe", (10, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                            infoColor, 2)
                cv2.putText(img, "ImagSize: " + str(w) + "x" + str(h), (10, y1 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                            infoColor, 2)
                cv2.putText(img, "FramCnt: " + str(self.frameCount), (10, y1 + 75), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                            infoColor, 2)
                cv2.putText(img, "FramProcCnt: " + str(self.frameProcessedCount), (10, y1 + 100),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.75, infoColor, 2)

                # Calculate Frames per second (FPS)
                fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)

                cv2.putText(img, "ProcFPS : " + str(int(fps)), (10, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.75, infoColor, 2)
                cv2.putText(img, "RealFPS : " + str(int(self.realFPS)), (10, y1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                            infoColor, 2)
                cv2.putText(img, "Race AI with us at OSSDC.org - Open Source Self Driving Initiative ", (10, h - 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, infoColor, 2)

                #         img = cv2.resize(img,(cols//3, rows//3))

                # print(int(fps))
                # print(str(int(self.realFPS)))

            delta = time.time() - self.prevTime
            if delta > 1:
                self.realFPS = (self.frameCount - self.prevFrameCount) / delta
                # print(fps, self.realFPS, img.shape, timeVal)
                self.prevFrameCount = self.frameCount
                self.prevTime = time.time()
                if infoColor == infoColor1:
                    infoColor = infoColor2
                else:
                    infoColor = infoColor1

            try:
                media.draw_styled_landmarks(img, results)
                new_frame = VideoFrame.from_ndarray(img, format="bgr24")
                self.prevGoodFrame = new_frame
            except Exception as e:
                if self.prevGoodFrame is not None:
                    new_frame = self.prevGoodFrame
                pass
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base

        except Exception as e1:
            track = traceback.format_exc()
            print(track)
            print("RaceOSSDC", e1)
            pass

        if self.last_word == "stop":
            phraseInitiale = ["lui", "manger", "lentement", "lui"]
            structurePhrase = StructurePhrase()
            structurePhrase = structurePhrase.traduire(phraseInitiale)
            # debug
            if self.dc.readyState == "open":
                print(str(structurePhrase))
                try:
                    self.dc.send(str(structurePhrase))
                except Exception as e1:
                    print(e1)
            self.last_word = ""
        return new_frame

        """
        img = frame.to_ndarray(format="bgr24")
        img = cv2.cvtColor(cv2.Canny(img, 100, 200), cv2.COLOR_GRAY2BGR)

        # rebuild a VideoFrame, preserving timing information
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame
        """


class AudioTransformTrack(MediaStreamTrack):
    """
       An audio stream track that transforms frames from an another track.
    """

    kind = "audio"

    def __init__(self, track, dc):
        super().__init__()  # don't forget this!
        self.track = track
        self.dc = dc
        self.rate = 48000
        self.chunk = int(self.rate/10)
        self.language_code = "fr-FR"
        self.client = speech.SpeechClient()
        self.diarization_config = speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=1,
            max_speaker_count=2,
        )
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code= self.language_code,
            diarization_config= self.diarization_config,
            enable_word_time_offsets=True
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config,
            interim_results=True
        )

    async def recv(self):
        frame = await self.track.recv()
        print("RECV AUDIO")
        print(self.dc.readyState)
        if self.dc.readyState == "open":
            try:
                self.dc.send("Here SOB")
                self.dc.close()
            except Exception as e:
                print(e)
        print("Here")
        with MicrophoneStream(self.rate, self.chunk) as stream:
            audio_generator = stream.generator()

            requests = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator
            )

            try:
                responses = self.client.streaming_recognize(self.streaming_config, requests)
                # Now, put the transcription responses to use.
                self.send_responses(responses)
                # listen_print_loop(responses)
            except:
                return

        return frame

    def send_responses(self, responses):
        num_chars_printed = 0
        speaker_tag = -1
        for response in responses:

            if not response.results:
                continue

            # The `results` list is consecutive. For streaming, we only care about
            # the first result being considered, since once it's `is_final`, it
            # moves on to considering the next utterance.

            # Display the transcription of the top alternative.
            result = response.results[0]

            if not result.alternatives:
                continue

            alternative = result.alternatives[0]
            transcript = get_speaker(alternative) + alternative.transcript

            # transcript = get_transcript(result.alternatives[0], None)

            # Display interim results, but with a carriage return at the end of the
            # line, so subsequent lines will overwrite them.
            #
            # If the previous result was longer than this one, we need to print
            # some extra spaces to overwrite the previous result

            overwrite_chars = " " * (num_chars_printed - len(transcript))
            if not result.is_final:
                if self.dc.readyState == "open":
                    try:
                        # print("Here SOB")
                        self.dc.send(str(transcript))  # + "\r"
                        self.dc._RTCDataChannel__transport._data_channel_flush()
                        self.dc._RTCDataChannel__transport._transmit()
                        # self.dc.send(str(transcript + overwrite_chars + "\r"))  # + "\r"
                    except Exception as e1:
                        print(e1)
                # sys.stdout.flush()
                num_chars_printed = len(transcript)
            else:
                self.dc.send(transcript + overwrite_chars)
                num_chars_printed = 0


async def offer(request):
    params = json.loads(request.body)
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.META['REMOTE_HOST'])

    # TODO: interface speech to text IA
    # recorder = MediaBlackhole()

    # if args.write_audio:
    #    recorder = MediaRecorder(args.write_audio)
    # else:
    #    recorder = MediaBlackhole()

    dc = pc.createDataChannel('chat')

    @dc.on("open")
    def say_hello():
        print("dc is open")
        if dc.readyState == "open":
            dc.send("hello")
            for i in range(0, 15):
                dc.send("BYE")

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        log_info("ICE connection state is %s", pc.iceConnectionState)
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        log_info("Track %s received", track.kind)

        if track.kind == "audio":
            # recorder.addTrack(track)
            local_audio = AudioTransformTrack(track, dc)
            pc.addTrack(local_audio)
        elif track.kind == "video":
            local_video = VideoTransformTrack(
                track, dc
            )
            pc.addTrack(local_video)

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            # await recorder.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    # await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return HttpResponse(
        json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
        content_type="application/json",
    )
