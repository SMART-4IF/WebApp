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

import threading
from threading import Thread

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
threads = {}

infoColor1 = (0, 255, 0)
infoColor2 = (0, 255, 255)
infoColor = infoColor1

mutex = threading.Lock()


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
        # print("recv")
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
                    mutex.acquire()
                    self.dc.send(str(structurePhrase))
                    mutex.release()
                    time.sleep(.1)
                except Exception as e1:
                    print(e1)
                self.last_word = ""
        return new_frame


kill_thread_b = False


async def runA(client, streaming_config, dc_audio, pc_id):
    while dc_audio.readyState != "open":
        time.sleep(.1)

    with MicrophoneStream(48000, 4800) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        while True:
            try:
                print("----------------started  -------------------" + pc_id)
                responses = client.streaming_recognize(streaming_config, requests)

                res = listen_print_loop(responses)
                if dc_audio.readyState == "open":
                    try:
                        mutex.acquire()
                        dc_audio.send(res)
                        mutex.release()
                        time.sleep(.1)
                    except Exception as e1:
                        print("Error")
                print("----------------ended-------------------" + pc_id)
            except:
                return


def runB(dc_audio, pc_id):
    global threads
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    rate = 48000
    chunk = int(rate / 10)
    language_code = "fr-FR"
    client = speech.SpeechClient()
    diarization_config = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=True,
        min_speaker_count=1,
        max_speaker_count=4,
    )
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=rate,
        language_code=language_code,
        diarization_config=diarization_config,
        # max_alternatives=1,
        enable_word_time_offsets=True
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )

    while True and not threads[pc_id][1]:
        loop.run_until_complete(runA(client=client, streaming_config=streaming_config, dc_audio=dc_audio, pc_id=pc_id))


async def offer(request):
    global threads
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
    dc_audio = pc.createDataChannel('audio')

    t2 = Thread(target=runB, args=[dc_audio, pc_id], daemon=True)

    threads[pc_id] = (t2, False)

    @dc_audio.on("open")
    def say_hello():
        print("dc audio is open")

    @dc.on("open")
    def say_hello():
        print("dc is open")

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
        print("Track %s received", track.kind)

        if track.kind == "audio":
            t2.start()
        elif track.kind == "video":
            local_video = VideoTransformTrack(
                track, dc
            )
            pc.addTrack(local_video)

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            print("ended")
            # await recorder.stop()

    @dc_audio.on("close")
    def close():
        global threads
        print("close_"+pc_id)
        if t2 is not None:
            threads[pc_id][0].join(1)
            threads[pc_id] = (None, True)

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
