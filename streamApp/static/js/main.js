console.log("hello world")

var mapPeers = {};

var username = document.querySelector('#username')
var labelname = document.querySelector('#label-username')
var join = document.querySelector('#btn-join')

var user;

var webSocket;

const uuid = JSON.parse(document.getElementById('room_uuid').textContent);
var password = document.querySelector('#password')

function webSocketOnMessage(event) {
    var parsedData = JSON.parse(event.data);
    var peerUsername = parsedData['peer'];
    var action = parsedData['action'];

    if (user === peerUsername) {
        return;
    }

    var receiver_channel_name = parsedData['message']['receiver_channel_name']

    if (action === 'new-peer') {
        createOfferer(peerUsername, receiver_channel_name);

        return;
    }

    if (action === 'new-offer') {
        var offer = parsedData['message']['sdp'];

        createAnswerer(offer, peerUsername, receiver_channel_name);

        return;
    }

    if (action === 'new-answer') {
        var answer = parsedData['message']['sdp'];

        var peer = mapPeers[peerUsername];
        peer[0].setRemoteDescription(answer);

        return;
    }
}

join.addEventListener('click', () => {
    user = username.value;

    console.log('username =>', user)

    if (user !== "") {
        if (password) {

            var data = JSON.stringify({
                "value": password.value
            });

            var xhr = new XMLHttpRequest();

            xhr.addEventListener("readystatechange", function () {
                if (this.readyState === 4) {
                    console.log(this.responseText);
                    if (JSON.parse(this.response).result === 1) {
                        username.value = '';
                        username.disabled = true;
                        username.style.visibility = 'hidden'

                        join.disabled = true;
                        join.style.visibility = 'hidden'

                        labelname.innerHTML = user

                        var loc = window.location;
                        var wsStart = 'ws://';

                        if (loc.protocol === 'https:') {
                            wsStart = 'wss://';
                        }

                        var endPoint = wsStart + loc.host + loc.pathname;

                        console.log('endPoint : ', endPoint);

                        webSocket = new WebSocket(endPoint);

                        webSocket.addEventListener('open', (e) => {
                            console.log("Connection Opened !")

                            sendSignal('new-peer', {});
                        })
                        webSocket.addEventListener('message', webSocketOnMessage)
                        webSocket.addEventListener('close', (e) => {
                            console.log("Connection Closed !")
                        })
                        webSocket.addEventListener('error', (e) => {
                            console.log("Error Occurred !")
                        })

                        document.getElementById('modal').setAttribute("x-data", "{ open: false }")
                    } else {
                        document.getElementById('error').innerHTML = "Une erreur c'est produite, mauvais mot de passe"
                    }
                }
            });

            xhr.open("POST", "http://localhost:8000/api/access_check/" + uuid);
            xhr.setRequestHeader("Content-Type", "application/json");

            xhr.send(data);
        } else {
            username.value = '';
            username.disabled = true;
            username.style.visibility = 'hidden'

            join.disabled = true;
            join.style.visibility = 'hidden'

            labelname.innerHTML = user

            var loc = window.location;
            var wsStart = 'ws://';

            if (loc.protocol === 'https:') {
                wsStart = 'wss://';
            }

            var endPoint = wsStart + loc.host + loc.pathname;

            console.log('endPoint : ', endPoint);

            webSocket = new WebSocket(endPoint);

            webSocket.addEventListener('open', (e) => {
                console.log("Connection Opened !")

                sendSignal('new-peer', {});
            })
            webSocket.addEventListener('message', webSocketOnMessage)
            webSocket.addEventListener('close', (e) => {
                console.log("Connection Closed !")
            })
            webSocket.addEventListener('error', (e) => {
                console.log("Error Occurred !")
            })

            document.getElementById('modal').setAttribute("x-data", "{ open: false }")
        }
    } else {
        document.getElementById('error').innerHTML = "Une erreur c'est produite, le nom ne peut pas être vide"
    }
})

var localStream = new MediaStream();

const constraints = {
    'video': true,
    'audio': true,
};

const localVideo = document.querySelector('#local-video');

const btnToggleAudio = document.querySelector('#btn-toggle-audio');
const btnToggleVideo = document.querySelector('#btn-toggle-video');

var userMedia = navigator.mediaDevices.getUserMedia(constraints)
    .then(stream => {
        localStream = stream;
        localVideo.srcObject = localStream;
        localVideo.muted = true;

        var audioTracks = stream.getAudioTracks();
        var videoTracks = stream.getVideoTracks();

        audioTracks[0].enabled = true;
        videoTracks[0].enabled = true;

        btnToggleAudio.addEventListener('click', () => {
            audioTracks[0].enabled = !audioTracks[0].enabled

            if (audioTracks[0].enabled) {
                btnToggleAudio.innerHTML = 'Audio Mute';
            } else {
                btnToggleAudio.innerHTML = 'Audio unMute'
            }
        })

        btnToggleVideo.addEventListener('click', () => {
            videoTracks[0].enabled = !videoTracks[0].enabled

            if (videoTracks[0].enabled) {
                btnToggleVideo.innerHTML = 'Video Off';
            } else {
                btnToggleVideo.innerHTML = 'Video On'
            }
        })
    })
    .catch(error => {
        console.log('Error accessing media devices')
    })

/************************************/

/*//TODO: server side peerconnection
function activateServerSideConnection() {
    console.log("goo");
    const configuration = {'iceServers': [{'urls': 'stun:stun.l.google.com:19302'}]}
    var pc = new RTCPeerConnection(configuration)

    pc.addEventListener('icegatheringstatechange', function (e) {
        console.log(pc.iceGatheringState)
    }, false);

    pc.addEventListener('iceconnectionstatechange', function (e) {
        console.log(pc.iceConnectionState)
    }, false);

    pc.addEventListener('signalingstatechange', function (e) {
        console.log(pc.signalingState)
    }, false);

    var time_start = null;

    function current_stamp() {
        if (time_start === null) {
            time_start = new Date().getTime();
            return 0;
        } else {
            return new Date().getTime() - time_start;
        }
    }

    navigator.mediaDevices.getUserMedia(constraints)
        .then(stream => {
            stream.getTracks().forEach(function(track) {
                pc.addTrack(track, stream);
            });
        }).catch(error => {
        console.log('Error accessing media devices')
    })

    console.log("negotiate")
    return pc.createOffer().then(function (offer) {
        console.log("negotiate2")
        return pc.setLocalDescription(offer);
    }).then(function () {
        console.log("negotiate4")
        var offer = pc.localDescription;
        console.log("offfer")
        console.log(offer)
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        console.log(csrftoken)
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            method: 'POST'
        });
    }).then(function (response) {
        console.log("negotiate5")
        return response.json();
    }).then(function (answer) {
        console.log(answer)
        return pc.setRemoteDescription(new RTCSessionDescription({ type: answer.type, sdp:answer.sdp }))
        //return pc.setRemoteDescription(answer);

    }).catch(function (e) {
        console.log(e);
    });



}


activateServerSideConnection().then(r => console.log(r))*/

/************************************/

var btnSendMsg = document.querySelector('#btn-send');

btnSendMsg.addEventListener('click', sendMessageOnClick);

var messageList = document.querySelector('#message-list');
var messageInput = document.querySelector('#msg');

function sendMessageOnClick(event) {
    var message = messageInput.value;

    var li = document.createElement('li');
    li.appendChild(document.createTextNode('Me: ' + message));
    messageList.appendChild(li);

    var dataChannels = getDataChannels();

    message = user + ': ' + message

    for (index in dataChannels) {
        dataChannels[index].send(message);
    }

    messageInput.value = '';
}


function sendSignal(action, message) {
    var jsonStr = JSON.stringify({
        'peer': user,
        'action': action,
        'message': message,
    })

    webSocket.send(jsonStr)
}

function createOfferer(peerUsername, receiver_channel_name) {
    const configuration = {'iceServers': [{'urls': 'stun:stun.l.google.com:19302'}]}
    var peer = new RTCPeerConnection(configuration)

    addLocalTracks(peer);

    var dc = peer.createDataChannel('channel');
    dc.addEventListener('open', () => {
        console.log('Connection opened!')
    });
    dc.addEventListener('message', dcOnMessage);

    var remoteVideo = createVideo(peerUsername);
    setOnTrack(peer, remoteVideo);

    mapPeers[peerUsername] = [peer, dc];

    peer.addEventListener('iceconnectionstatechange', () => {
        var iceconnectionstate = peer.iceConnectionState;

        if (iceconnectionstate === 'failed' || iceconnectionstate === 'disconnected' || iceconnectionstate === 'closed') {
            delete mapPeers[peerUsername];

            if (iceconnectionstate !== 'closed') {
                peer.close();
            }

            removeVideo(remoteVideo);
        }
    });

    peer.addEventListener('icecandidate', (event) => {
        if (event.candidate) {
            console.log('New ice candidate ', JSON.stringify(peer.localDescription));

            return;
        }

        sendSignal('new-offer', {
            'sdp': peer.localDescription,
            'receiver_channel_name': receiver_channel_name
        });
    });

    peer.createOffer()
        .then(o => peer.setLocalDescription(o))
        .then(() => {
            console.log("Local Description set successfully")
        })
}

function createAnswerer(offer, peerUsername, receiver_channel_name) {
    const configuration = {'iceServers': [{'urls': 'stun:stun.l.google.com:19302'}]}
    var peer = new RTCPeerConnection(configuration)

    addLocalTracks(peer);

    var remoteVideo = createVideo(peerUsername);
    setOnTrack(peer, remoteVideo);

    peer.addEventListener('datachannel', e => {
        peer.dc = e.channel;
        peer.dc.addEventListener('open', () => {
            console.log('Connection opened!')
        });
        peer.dc.addEventListener('message', dcOnMessage)

        mapPeers[peerUsername] = [peer, peer.dc];
    });

    peer.addEventListener('iceconnectionstatechange', () => {
        var iceconnectionstate = peer.iceConnectionState;

        if (iceconnectionstate === 'failed' || iceconnectionstate === 'disconnected' || iceconnectionstate === 'closed') {
            delete mapPeers[peerUsername];

            if (iceconnectionstate !== 'closed') {
                peer.close();
            }

            removeVideo(remoteVideo);
        }
    });

    peer.addEventListener('icecandidate', (event) => {
        if (event.candidate) {
            console.log('New ice candidate ', JSON.stringify(peer.localDescription));

            return;
        }

        sendSignal('new-answer', {
            'sdp': peer.localDescription,
            'receiver_channel_name': receiver_channel_name
        });
    });

    peer.setRemoteDescription(offer)
        .then(() => {
            console.log('Remote description set successfully for %s.', peerUsername);

            return peer.createAnswer();
        })
        .then(a => {
            console.log('Answer created')

            peer.setLocalDescription(a);
        })

}

function addLocalTracks(peer) {
    localStream.getTracks().forEach(track => {
        peer.addTrack(track, localStream);
    })

    return;
}

function dcOnMessage(event) {
    var message = event.data;

    var li = document.createElement('li');
    li.appendChild(document.createTextNode(message));
    messageList.appendChild(li);
}

function createVideo(peerUsername) {
    var videoContainer = document.querySelector('#video-container');

    var remoteVideo = document.createElement('video');

    remoteVideo.id = peerUsername + '-video';
    remoteVideo.autoplay = true;
    remoteVideo.playsInline = true;

    var videoWrapper = document.createElement('div');

    videoContainer.appendChild(videoWrapper);

    videoWrapper.appendChild(remoteVideo);

    return remoteVideo;
}

function setOnTrack(peer, remoteVideo) {
    var remoteStream = new MediaStream();

    remoteVideo.srcObject = remoteStream;

    peer.addEventListener('track', async (event) => {
        remoteStream.addTrack(event.track, remoteStream);
    })

}

function removeVideo(video) {
    var videoWrapper = video.parentNode;

    videoWrapper.parentNode.removeChild(videoWrapper);
}


function getDataChannels() {
    var dataChannels = [];
    for (peerUsername in mapPeers) {
        var dataChannel = mapPeers[peerUsername][1];
        dataChannels.push(dataChannel);
    }

    return dataChannels;
}