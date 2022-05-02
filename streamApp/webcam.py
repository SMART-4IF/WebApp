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
from aiohttp import web
from av import VideoFrame

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from django.http import HttpResponse

from streamApp import media
from streamApp.media import mp_holistic

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

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track
        self.holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        self.prevTime = time.time()
        self.starttime1 = time.time()
        self.realFPS = 0
        self.prevGoodFrame = None
        self.frameCount = 0
        self.prevFrameCount = 0
        self.frameProcessedCount = 0

    async def recv(self):
        global infoColor
        # TODO: interface LSFIA
        frame = await self.track.recv()
        new_frame = frame
        self.frameCount = self.frameCount + 1
        self.frameProcessedCount = self.frameProcessedCount + 1

        timer = cv2.getTickCount()
        # perform edge detection
        try:
            img = frame.to_ndarray(format="bgr24")

            rows, cols, _ = img.shape
            h, w, _ = img.shape
            rows, cols, _ = img.shape

            y = h // 3
            x = w // 3

            image, results = media.mediapipe_detection(img, self.holistic)
            print(results)

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

                print(int(fps))
                print(str(int(self.realFPS)))

            delta = time.time() - self.prevTime
            if delta > 1:
                self.realFPS = (self.frameCount - self.prevFrameCount) / delta
                print(fps, self.realFPS, img.shape, timeVal)
                self.prevFrameCount = self.frameCount
                self.prevTime = time.time()
                if infoColor == infoColor1:
                    infoColor = infoColor2
                else:
                    infoColor = infoColor1

            try:
                media.draw_styled_landmarks(img,results)
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


async def offer(request):
    params = json.loads(request.body)
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.META['REMOTE_HOST'])

    # TODO: interface speeech to text IA
    recorder = MediaBlackhole()

    # if args.write_audio:
    #    recorder = MediaRecorder(args.write_audio)
    # else:
    #    recorder = MediaBlackhole()

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
            recorder.addTrack(track)
        elif track.kind == "video":
            local_video = VideoTransformTrack(
                track
            )
            pc.addTrack(local_video)

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            await recorder.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return HttpResponse(
        json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
        content_type="application/json",
    )
