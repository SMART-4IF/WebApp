/**
 *  SOURCE : https://dev.to/whitphx/python-webrtc-basics-with-aiortc-48id
 */

// peer connection
var pc = null;

// data channel
var dc = null, dcInterval = null;

const constraints = {
    'video': true,
    'audio': true,
};

function createPeerConnection() {
    var config = {
        sdpSemantics: 'unified-plan'
    };

    config.iceServers = [{urls: ['stun:stun.l.google.com:19302']}];


    pc = new RTCPeerConnection(config);

    // register some listeners to help debugging
    pc.addEventListener('icegatheringstatechange', function () {
        console.log(pc.iceGatheringState);
    }, false);


    pc.addEventListener('iceconnectionstatechange', function () {
        console.log(pc.iceConnectionState);
    }, false);

    pc.addEventListener('signalingstatechange', function () {
        console.log(pc.signalingState);
    }, false);


    // connect audio / video
    pc.addEventListener('track', function (evt) {
        console.log(evt)
        console.log(document.getElementById('video'))
        console.log(evt.streams[0])
        document.getElementById('video').srcObject = evt.streams[0];
    });

    return pc;
}

function negotiate() {
    return pc.createOffer().then(function (offer) {
        return pc.setLocalDescription(offer);
    }).then(function () {
        // wait for ICE gathering to complete
        return new Promise(function (resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }

                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function () {
        var offer = pc.localDescription;
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type
            }),
            headers: {
                'Content-Type': 'application/json',
                 'X-CSRFToken': csrftoken
            },
            method: 'POST'
        });
    }).then(function (response) {
        return response.json();
    }).then(function (answer) {
        console.log(answer)

        return pc.setRemoteDescription(answer);
    }).catch(function (e) {
        alert(e);
    });
}

pc = createPeerConnection();

var time_start = null;

function current_stamp() {
    if (time_start === null) {
        time_start = new Date().getTime();
        return 0;
    } else {
        return new Date().getTime() - time_start;
    }
}

navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
    stream.getTracks().forEach(function (track) {
        pc.addTrack(track, stream);
    });
    return negotiate();
}, function (err) {
    alert('Could not acquire media: ' + err);
});




function stop() {
    document.getElementById('stop').style.display = 'none';

    // close data channel
    if (dc) {
        dc.close();
    }

    // close transceivers
    if (pc.getTransceivers) {
        pc.getTransceivers().forEach(function (transceiver) {
            if (transceiver.stop) {
                transceiver.stop();
            }
        });
    }

    // close local audio / video
    pc.getSenders().forEach(function (sender) {
        sender.track.stop();
    });

    // close peer connection
    setTimeout(function () {
        pc.close();
    }, 500);
}