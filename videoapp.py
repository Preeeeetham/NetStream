# NetStream - Host & Client Video Chat Application
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from flask_cors import CORS
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*", ping_timeout=30, ping_interval=5)

static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(static_folder, exist_ok=True)

connected_users = []
host_id = None
user_roles = {} 
connection_timestamps = {} 

HTML = '''
<html>
  <head>
    <title>NetStream - Host & Client Video Chat</title>
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap" rel="stylesheet">
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      body {
        background-color: #141414;
        font-family: 'Bebas Neue', sans-serif;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 2rem;
      }
      .container {
        max-width: 1200px;
        width: 100%;
        text-align: center;
        position: relative;
      }
      h1 {
        color: #E50914;
        font-size: 3.5rem;
        margin-bottom: 2rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        animation: glow 2s ease-in-out infinite alternate;
      }
      .video-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
        margin-bottom: 20px;
      }
      .video-box {
        position: relative;
        width: 100%;
        aspect-ratio: 16/9;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 0 20px rgba(229, 9, 20, 0.3);
        animation: fadeIn 1s ease-in;
      }
      .video-feed {
        width: 100%;
        height: 100%;
        object-fit: cover;
        background-color: #2a2a2a;
      }
      .video-label {
        position: absolute;
        bottom: 10px;
        left: 10px;
        color: white;
        background-color: rgba(0,0,0,0.7);
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 1.2rem;
      }
      .role-indicator {
        position: absolute;
        top: 10px;
        right: 10px;
        color: white;
        background-color: #E50914;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 1rem;
      }
      .controls {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-top: 20px;
      }
      .controls button {
        background-color: #E50914;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 1rem;
        transition: background-color 0.3s;
      }
      .controls button:hover {
        background-color: #ff0f1f;
      }
      .chat-container {
        width: 100%;
        max-width: 800px;
        margin-top: 20px;
      }
      #chat-messages {
        width: 100%;
        height: 200px;
        overflow-y: auto;
        background-color: #2a2a2a;
        color: white;
        padding: 10px;
        border-radius: 8px;
      }
      #chat-input {
        width: 100%;
        padding: 10px;
        margin-top: 10px;
        border-radius: 5px;
        border: none;
      }
      #status {
        color: #E50914;
        margin-top: 1rem;
        font-size: 1.2rem;
      }
      @keyframes glow {
        from { text-shadow: 0 0 5px #E50914, 0 0 10px #E50914; }
        to { text-shadow: 0 0 10px #E50914, 0 0 20px #E50914; }
      }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .transcription-container {
        width: 100%;
        max-width: 800px;
        margin-top: 20px;
        background-color: #2a2a2a;
        border-radius: 8px;
        padding: 15px;
        color: white;
      }

      .transcription-box {
        width: 100%;
        height: 100px;
        overflow-y: auto;
        background-color: rgba(0, 0, 0, 0.3);
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 10px;
      }

      .transcription-controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .transcription-status {
        font-size: 0.9rem;
        color: #E50914;
      }

      .transcription-toggle {
        background-color: #E50914;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s;
      }

      .transcription-toggle:hover {
        background-color: #ff0f1f;
      }

      .transcription-entry {
        margin-bottom: 8px;
        padding: 4px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }

      .transcription-speaker {
        font-weight: bold;
        color: #E50914;
      }
      
      /* New styles for connection status */
      .connection-status {
        background-color: rgba(0,0,0,0.7);
        color: #E50914;
        padding: 5px 10px;
        border-radius: 4px;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 1.2rem;
        display: none;
      }
      
      .reconnect-button {
        background-color: #E50914;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 10px;
        display: block;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>NetStream Live</h1>
      <div class="video-container">
        <div class="video-box" id="localVideoBox">
          <video id="localVideo" class="video-feed" autoplay playsinline muted></video>
          <div class="video-label">You</div>
          <div class="role-indicator" id="localRole">Connecting...</div>
          <div class="connection-status" id="localConnectionStatus">Initializing...</div>
        </div>
        <div class="video-box" id="remoteVideoBox">
          <video id="remoteVideo" class="video-feed" autoplay playsinline></video>
          <div class="video-label">Remote User</div>
          <div class="role-indicator" id="remoteRole">Waiting...</div>
          <div class="connection-status" id="remoteConnectionStatus">Waiting for connection...</div>
        </div>
      </div>
      <div class="controls">
        <button id="muteAudio">Mute Audio</button>
        <button id="muteVideo">Mute Video</button>
        <button id="shareScreen">Share Screen</button>
        <button id="reconnectButton" class="reconnect-button" style="display: none">Reconnect</button>
      </div>
      <div class="transcription-container">
        <h3>Live Transcription</h3>
        <div class="transcription-box" id="transcriptionBox"></div>
        <div class="transcription-controls">
          <div class="transcription-status" id="transcriptionStatus">Transcription: Off</div>
          <button class="transcription-toggle" id="toggleTranscription">Start Transcription</button>
        </div>
      </div>
      <div class="chat-container">
        <div id="chat-messages"></div>
        <input type="text" id="chat-input" placeholder="Type a message...">
      </div>
      <div id="status"></div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
      // Improved socket connection with automatic reconnect
      const socket = io(window.location.origin, { 
        transports: ['websocket'], 
        upgrade: false,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000
      });
      
      let localStream;
      let screenStream;
      let peerConnection = null;
      let isHost = false;
      let isConnected = false;
      let connectionAttempts = 0;
      let maxConnectionAttempts = 5;
      let isReconnecting = false;
      
      // Enhanced ICE server configuration with additional STUN/TURN servers
      const configuration = {
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' },
          { urls: 'stun:stun2.l.google.com:19302' },
          { urls: 'stun:stun3.l.google.com:19302' },
          { urls: 'stun:stun4.l.google.com:19302' },
          // Free TURN servers (add your own TURN server for production)
          { 
            urls: 'turn:openrelay.metered.ca:80',
            username: 'openrelayproject',
            credential: 'openrelayproject'
          },
          {
            urls: 'turn:openrelay.metered.ca:443',
            username: 'openrelayproject',
            credential: 'openrelayproject'
          }
        ],
        iceCandidatePoolSize: 10,
        // Optimize for audio/video
        iceTransportPolicy: 'all',
        rtcpMuxPolicy: 'require',
        bundlePolicy: 'max-bundle'
      };

      // Connection timeout handler
      let connectionTimeoutId;
      
      function setupConnectionTimeout() {
        clearTimeout(connectionTimeoutId);
        connectionTimeoutId = setTimeout(() => {
          if (!isConnected && peerConnection) {
            console.warn('Connection timeout - attempting reconnect');
            resetConnection();
            socket.emit('connection-failed', { reason: 'timeout' });
            showConnectionStatus('Connection timeout. Trying again...', true);
          }
        }, 30000); // 30 second timeout
      }
      
      function showConnectionStatus(message, isError = false) {
        const statusElem = document.getElementById('status');
        statusElem.textContent = message;
        
        if (isError) {
          statusElem.style.color = '#ff3860';
          document.getElementById('reconnectButton').style.display = 'inline-block';
        } else {
          statusElem.style.color = '#E50914';
          document.getElementById('reconnectButton').style.display = 'none';
        }
      }

      async function init() {
        try {
          // Request with constraints for better initial quality
          localStream = await navigator.mediaDevices.getUserMedia({ 
            video: {
              width: { ideal: 1280 },
              height: { ideal: 720 },
              frameRate: { ideal: 30, max: 30 }
            }, 
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true
            } 
          });
          
          document.getElementById('localVideo').srcObject = localStream;
          showConnectionStatus('Camera and microphone initialized');
          
          // Signal to server we're ready
          setTimeout(() => {
            socket.emit('ready-for-connection');
          }, 1000);
        } catch (e) {
          console.error('Error accessing media devices:', e);
          showConnectionStatus('Camera/Mic access denied. Please check permissions.', true);
        }
      }

      // Improved WebRTC connection handling for proper video feed display
      async function initiateOffer() {
        if (!isHost) return;
        
        const pc = createPeerConnection();
        if (!pc) return;
        
        try {
          showConnectionStatus('Creating connection offer...');
          
          // Important: add all tracks before creating the offer
          if (pc.getSenders().length === 0) {
            localStream.getTracks().forEach(track => {
              pc.addTrack(track, localStream);
            });
          }
          
          // Wait for ICE gathering to start before creating offer
          await new Promise(resolve => setTimeout(resolve, 500));
          
          const offer = await pc.createOffer({
            offerToReceiveAudio: true,
            offerToReceiveVideo: true,
            iceRestart: connectionAttempts > 1
          });
          
          await pc.setLocalDescription(offer);
          
          // Wait a bit for initial ICE candidates before sending offer
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          socket.emit('offer', { offer: pc.localDescription });
          console.log('Offer sent to client');
        } catch (e) {
          console.error('Error creating offer:', e);
          showConnectionStatus('Failed to create offer. Retrying...', true);
          
          if (connectionAttempts < maxConnectionAttempts) {
            setTimeout(initiateOffer, 2000);
          }
        }
      }
      
      // Fix for createPeerConnection to ensure tracks are properly handled
      function createPeerConnection() {
        try {
          if (peerConnection) {
            resetConnection();
          }
          
          connectionAttempts++;
          console.log(`Creating peer connection (attempt ${connectionAttempts}/${maxConnectionAttempts})`);
          
          peerConnection = new RTCPeerConnection(configuration);
          
          // Local tracks will be added either here or in initiateOffer
          
          // Fix: Be more explicit about how remote tracks are added
          peerConnection.ontrack = event => {
            console.log('Remote track received:', event.track.kind);
            const remoteVideo = document.getElementById('remoteVideo');
            
            // Use the first stream from the first track
            if (event.streams && event.streams[0]) {
              remoteVideo.srcObject = event.streams[0];
              console.log('Remote video stream assigned');
            } else {
              // Fallback if no stream in the event (shouldn't happen but just in case)
              if (!remoteVideo.srcObject) {
                const newStream = new MediaStream();
                newStream.addTrack(event.track);
                remoteVideo.srcObject = newStream;
                console.log('Created new MediaStream for remote track');
              } else {
                // Add track to existing stream
                const existingStream = remoteVideo.srcObject;
                if (existingStream instanceof MediaStream) {
                  existingStream.addTrack(event.track);
                  console.log('Added track to existing remote MediaStream');
                }
              }
            }
            
            // Hide the connection status overlay
            document.getElementById('remoteConnectionStatus').style.display = 'none';
            
            // Make sure video autoplay works even if browser blocks it
            remoteVideo.play().catch(e => {
              console.warn('Remote video autoplay was prevented:', e);
              // Add a play button if autoplay is blocked
              const playButton = document.createElement('button');
              playButton.textContent = 'Play Video';
              playButton.style.position = 'absolute';
              playButton.style.zIndex = '100';
              playButton.style.top = '50%';
              playButton.style.left = '50%';
              playButton.style.transform = 'translate(-50%, -50%)';
              playButton.onclick = () => {
                remoteVideo.play();
                playButton.remove();
              };
              document.getElementById('remoteVideoBox').appendChild(playButton);
            });
          };

          // Handle ICE candidates
          peerConnection.onicecandidate = event => {
            if (event.candidate) {
              console.log('Sending ICE candidate:', event.candidate.candidate.substr(0, 50) + '...');
              socket.emit('candidate', { candidate: event.candidate });
            } else {
              console.log('All ICE candidates gathered');
            }
          };
          
          // Additional ICE gathering state tracking
          peerConnection.onicegatheringstatechange = () => {
            console.log('ICE gathering state:', peerConnection.iceGatheringState);
          };
          
          // Connection state monitoring with more detailed logging
          peerConnection.oniceconnectionstatechange = () => {
            console.log('ICE Connection State:', peerConnection.iceConnectionState);
            
            document.getElementById('status').textContent = 
              `Connection state: ${peerConnection.iceConnectionState}`;
              
            switch(peerConnection.iceConnectionState) {
              case 'checking':
                showConnectionStatus('Establishing connection...');
                break;
              case 'connected':
              case 'completed':
                isConnected = true;
                clearTimeout(connectionTimeoutId);
                showConnectionStatus(isHost ? 'Connected to client' : 'Connected to host');
                document.getElementById('remoteConnectionStatus').style.display = 'none';
                connectionAttempts = 0;
                break;
              case 'failed':
                if (connectionAttempts < maxConnectionAttempts) {
                  console.warn('Connection failed, retrying...');
                  resetConnection();
                  if (isHost) {
                    initiateOffer();
                  } else {
                    socket.emit('connection-failed', { reason: 'ice-failed' });
                  }
                } else {
                  showConnectionStatus('Connection failed after multiple attempts. Try reloading the page.', true);
                }
                break;
              case 'disconnected':
                showConnectionStatus('Connection interrupted. Trying to reconnect...', true);
                // Try to recover automatically
                setTimeout(() => {
                  if (peerConnection.iceConnectionState === 'disconnected') {
                    resetConnection();
                    if (isHost) {
                      initiateOffer();
                    }
                  }
                }, 2000);
                break;
            }
          };
          
          // Also monitor signaling state
          peerConnection.onsignalingstatechange = () => {
            console.log('Signaling State:', peerConnection.signalingState);
          };
          
          // Set up audio output (to avoid echo)
          const remoteVideo = document.getElementById('remoteVideo');
          if (typeof remoteVideo.setSinkId === 'function') {
            remoteVideo.setSinkId('default')
              .then(() => console.log('Audio output set to default speaker'))
              .catch(e => console.error('Error setting audio output:', e));
          }
          
          setupConnectionTimeout();
          return peerConnection;
          
        } catch (e) {
          console.error('Error creating peer connection:', e);
          showConnectionStatus('Failed to create connection. Please reload the page.', true);
          return null;
        }
      }
      
      function resetConnection() {
        isConnected = false;
        if (peerConnection) {
          peerConnection.onicecandidate = null;
          peerConnection.ontrack = null;
          peerConnection.oniceconnectionstatechange = null;
          peerConnection.close();
          peerConnection = null;
        }
        document.getElementById('remoteVideo').srcObject = null;
        document.getElementById('remoteConnectionStatus').style.display = 'block';
        document.getElementById('remoteConnectionStatus').textContent = 'Reconnecting...';
      }
      
      // Fix for handling offer responses in the client
      socket.on('offer', async (data) => {
        if (!isHost) {
          showConnectionStatus('Received connection offer from host...');
          const pc = createPeerConnection();
          if (!pc) return;
          
          try {
            // Add all local tracks before processing the offer
            localStream.getTracks().forEach(track => {
              pc.addTrack(track, localStream);
            });
            
            const offerDesc = new RTCSessionDescription(data.offer);
            await pc.setRemoteDescription(offerDesc);
            console.log('Remote description set based on offer');
            
            // Create answer
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            
            // Wait a bit for ICE candidates before sending answer
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Send answer with current local description (which may have ICE candidates)
            socket.emit('answer', { answer: pc.localDescription });
            console.log('Answer sent to host');
          } catch (e) {
            console.error('Error handling offer:', e);
            showConnectionStatus('Failed to process connection offer', true);
            
            if (connectionAttempts < maxConnectionAttempts) {
              socket.emit('connection-failed', { reason: 'offer-error' });
            }
          }
        }
      });

      socket.on('answer', async (data) => {
        if (isHost && peerConnection) {
          try {
            showConnectionStatus('Received answer from client...');
            const answerDesc = new RTCSessionDescription(data.answer);
            await peerConnection.setRemoteDescription(answerDesc);
            console.log('Remote description set based on answer');
          } catch (e) {
            console.error('Error handling answer:', e);
            showConnectionStatus('Failed to process connection answer', true);
            
            if (connectionAttempts < maxConnectionAttempts) {
              resetConnection();
              setTimeout(initiateOffer, 2000);
            }
          }
        }
      });

      socket.on('candidate', async (data) => {
        try {
          if (peerConnection && peerConnection.remoteDescription) {
            const candidate = new RTCIceCandidate(data.candidate);
            await peerConnection.addIceCandidate(candidate);
            console.log('Added ICE candidate');
          } else {
            // Queue candidates if remote description not set yet
            console.log('Queueing ICE candidate until remote description is set');
            setTimeout(() => {
              if (peerConnection && peerConnection.remoteDescription) {
                peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate))
                  .catch(e => console.error('Error adding queued ICE candidate:', e));
              }
            }, 1000);
          }
        } catch (e) {
          console.error('Error handling ICE candidate:', e);
        }
      });

      // Socket event handlers
      socket.on('connect', () => {
        showConnectionStatus('Connected to server');
      });
      
      socket.on('disconnect', () => {
        showConnectionStatus('Disconnected from server. Please wait...', true);
      });
      
      socket.on('reconnect', (attemptNumber) => {
        showConnectionStatus(`Reconnected to server after ${attemptNumber} attempts`);
        // Re-establish WebRTC connection if needed
        if (isHost && !isConnected) {
          socket.emit('ready-for-connection');
        }
      });

      socket.on('role-assigned', (data) => {
        isHost = data.isHost;
        document.getElementById('localRole').textContent = isHost ? 'Host' : 'Client';
        document.getElementById('remoteRole').textContent = isHost ? 'Client' : 'Host';
        showConnectionStatus(isHost ? 'You are the host' : 'You are the client');
        
        // If host, wait for client connection notification
        // If client, wait for initiate-connection event
      });
      
      socket.on('host-changed', (data) => {
        if (data.newHost) {
          isHost = true;
          document.getElementById('localRole').textContent = 'Host';
          document.getElementById('remoteRole').textContent = 'Client';
          showConnectionStatus('You have been promoted to host');
          // Wait for new client to connect
        }
      });
      
      socket.on('initiate-connection', (data) => {
        // Client receives this event when host is ready
        if (!isHost) {
          showConnectionStatus('Host is ready, establishing connection...');
          // Client waits for offer from host
        }
      });

      socket.on('user-connected', async (data) => {
        if (isHost) {
          showConnectionStatus('Client connected, establishing video call...');
          initiateOffer();
        }
      });

      socket.on('user-disconnected', (data) => {
        document.getElementById('remoteVideo').srcObject = null;
        document.getElementById('remoteConnectionStatus').style.display = 'block';
        document.getElementById('remoteConnectionStatus').textContent = 'Remote user disconnected';
        document.getElementById('remoteRole').textContent = 'Waiting...';
        showConnectionStatus('Remote user disconnected. Waiting for new connection...');
        
        if (peerConnection) {
          resetConnection();
        }
      });
      
      socket.on('try-reconnect', () => {
        showConnectionStatus('Server suggests reconnecting...', true);
        resetConnection();
        
        setTimeout(() => {
          socket.emit('ready-for-connection');
          if (isHost) {
            initiateOffer();
          }
        }, 2000);
      });
      
      socket.on('heartbeat-response', (data) => {
        // Connection is alive
      });
      
      // Send heartbeat periodically
      setInterval(() => {
        if (socket.connected) {
          socket.emit('heartbeat');
        }
      }, 30000);

      // Reconnect button
      document.getElementById('reconnectButton').addEventListener('click', () => {
        showConnectionStatus('Reconnecting...');
        resetConnection();
        socket.emit('ready-for-connection');
        if (isHost) {
          setTimeout(initiateOffer, 1000);
        }
      });

      // Controls
      document.getElementById('muteAudio').addEventListener('click', () => {
        localStream.getAudioTracks().forEach(track => {
          track.enabled = !track.enabled;
        });
        document.getElementById('muteAudio').textContent = 
          localStream.getAudioTracks()[0].enabled ? 'Mute Audio' : 'Unmute Audio';
      });

      document.getElementById('muteVideo').addEventListener('click', () => {
        localStream.getVideoTracks().forEach(track => {
          track.enabled = !track.enabled;
        });
        document.getElementById('muteVideo').textContent = 
          localStream.getVideoTracks()[0].enabled ? 'Mute Video' : 'Unmute Video';
      });

      document.getElementById('shareScreen').addEventListener('click', async () => {
        try {
          if (screenStream) {
            // Toggle back to camera
            const cameraTrack = localStream.getVideoTracks()[0];
            
            if (peerConnection) {
              const sender = peerConnection.getSenders().find(s => s.track && s.track.kind === 'video');
              if (sender) {
                await sender.replaceTrack(cameraTrack);
              }
            }
            
            screenStream.getTracks().forEach(track => track.stop());
            screenStream = null;
            document.getElementById('localVideo').srcObject = localStream;
            document.getElementById('shareScreen').textContent = 'Share Screen';
            
          } else {
            // Switch to screen sharing
            screenStream = await navigator.mediaDevices.getDisplayMedia({ 
              video: { 
                cursor: 'always',
                displaySurface: 'monitor'
              },
              audio: false
            });
            
            const screenTrack = screenStream.getVideoTracks()[0];
            
            if (peerConnection) {
              const sender = peerConnection.getSenders().find(s => s.track && s.track.kind === 'video');
              if (sender) {
                await sender.replaceTrack(screenTrack);
              }
            }
            
            document.getElementById('localVideo').srcObject = screenStream;
            document.getElementById('shareScreen').textContent = 'Show Camera';
            
            screenTrack.onended = () => {
              // Handle when user stops sharing via browser UI
              document.getElementById('shareScreen').click();
            };
          }
        } catch (e) {
          console.error('Error sharing screen:', e);
          showConnectionStatus('Failed to share screen: ' + e.message, true);
        }
      });

      // Chat functionality
      const chatInput = document.getElementById('chat-input');
      chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && chatInput.value.trim()) {
          socket.emit('chat-message', chatInput.value);
          
          // Add local message immediately for better UX
          const chatMessages = document.getElementById('chat-messages');
          const messageElem = document.createElement('div');
          messageElem.textContent = `You: ${chatInput.value}`;
          messageElem.style.color = '#E50914';
          chatMessages.appendChild(messageElem);
          chatMessages.scrollTop = chatMessages.scrollHeight;
          
          chatInput.value = '';
        }
      });

      socket.on('chat-message', (data) => {
        const chatMessages = document.getElementById('chat-messages');
        const messageElem = document.createElement('div');
        messageElem.textContent = data;
        chatMessages.appendChild(messageElem);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      });

      // Speech Recognition Setup
      let recognition = null;
      let isTranscribing = false;

      function setupSpeechRecognition() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
          alert('Your browser does not support speech recognition. Please use Chrome or Edge.');
          return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
          document.getElementById('transcriptionStatus').textContent = 'Transcription: Active';
          document.getElementById('toggleTranscription').textContent = 'Stop Transcription';
        };

        recognition.onend = () => {
          if (isTranscribing) {
            // Auto-restart if still transcribing
            try {
              recognition.start();
            } catch (e) {
              console.error('Error restarting speech recognition:', e);
              isTranscribing = false;
              document.getElementById('transcriptionStatus').textContent = 'Transcription Error: ' + e.message;
              document.getElementById('toggleTranscription').textContent = 'Start Transcription';
            }
          }
        };

        recognition.onerror = (event) => {
          console.error('Speech recognition error:', event.error);
          document.getElementById('transcriptionStatus').textContent = 'Transcription Error: ' + event.error;
        };

        recognition.onresult = (event) => {
          let interimTranscript = '';
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              finalTranscript += transcript;
            } else {
              interimTranscript += transcript;
            }
          }

          if (finalTranscript) {
            addTranscriptionEntry(finalTranscript, isHost ? 'Host' : 'Client');
            socket.emit('transcription', { text: finalTranscript });
          }
        };
      }

      function addTranscriptionEntry(text, speaker) {
        const transcriptionBox = document.getElementById('transcriptionBox');
        const entry = document.createElement('div');
        entry.className = 'transcription-entry';
        entry.innerHTML = `<span class="transcription-speaker">${speaker}:</span> ${text}`;
        transcriptionBox.appendChild(entry);
        transcriptionBox.scrollTop = transcriptionBox.scrollHeight;
      }

      document.getElementById('toggleTranscription').addEventListener('click', () => {
        if (!recognition) {
          setupSpeechRecognition();
        }

        if (!isTranscribing) {
          try {
            recognition.start();
            isTranscribing = true;
          } catch (e) {
            console.error('Error starting speech recognition:', e);
            document.getElementById('transcriptionStatus').textContent = 'Transcription Error: ' + e.message;
          }
        } else {
          recognition.stop();
          isTranscribing = false;
          document.getElementById('transcriptionStatus').textContent = 'Transcription: Off';
          document.getElementById('toggleTranscription').textContent = 'Start Transcription';
        }
      });

      socket.on('transcription', (data) => {
        if (data.sender !== socket.id) {
          addTranscriptionEntry(data.text, isHost ? 'Client' : 'Host');
        }
      });
      
      // Start the application
      init();
    </script>
  </body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@socketio.on('connect')
def handle_connect():
    global host_id
    user_id = request.sid
    logger.info(f"New connection: {user_id}")
    
    connection_timestamps[user_id] = time.time()
    
    if not connected_users: 
        host_id = user_id
        connected_users.append(user_id)
        user_roles[user_id] = 'host'
        logger.info(f"User {user_id} assigned as host")
        socketio.emit('role-assigned', {'isHost': True}, to=user_id)
    elif len(connected_users) < 2:  
        connected_users.append(user_id)
        user_roles[user_id] = 'client'
        logger.info(f"User {user_id} assigned as client")
        socketio.emit('role-assigned', {'isHost': False}, to=user_id)
        socketio.emit('user-connected', {'userId': user_id}, to=host_id)
    else:
        logger.warning(f"Room full, rejecting user {user_id}")
        socketio.emit('error', {'message': 'Room is full'}, to=user_id)
        return False

@socketio.on('disconnect')
def handle_disconnect():
    global host_id
    user_id = request.sid
    logger.info(f"User disconnected: {user_id}")
    
    if user_id in connection_timestamps:
        del connection_timestamps[user_id]
    
    if user_id in connected_users:
        connected_users.remove(user_id)
        
        if user_id == host_id:
            old_host = host_id
            host_id = None
            logger.info(f"Host {old_host} disconnected")
            
            if connected_users:
                new_host = connected_users[0]
                host_id = new_host
                user_roles[new_host] = 'host'
                logger.info(f"Promoting client {new_host} to host")
                socketio.emit('role-assigned', {'isHost': True}, to=new_host)
                socketio.emit('host-changed', {'newHost': True}, to=new_host)
        else:
            logger.info(f"Client {user_id} disconnected")
        
        if connected_users:
            socketio.emit('user-disconnected', {'userId': user_id}, room=connected_users)

@socketio.on('ready-for-connection')
def handle_ready(data):
    """New event to ensure both sides are ready before attempting connection"""
    user_id = request.sid
    logger.info(f"User {user_id} ready for connection")
    
    if user_id == host_id and len(connected_users) > 1:
        client_id = [uid for uid in connected_users if uid != host_id][0]
        socketio.emit('initiate-connection', {'hostId': host_id}, to=client_id)

@socketio.on('offer')
def handle_offer(data):
    try:
        if host_id and len(connected_users) > 1:
            client_id = [uid for uid in connected_users if uid != host_id][0]
            logger.info(f"Forwarding offer from host to client {client_id}")
            socketio.emit('offer', {'offer': data['offer']}, to=client_id)
        else:
            logger.warning("Cannot forward offer: not enough users or no host")
    except Exception as e:
        logger.error(f"Error handling offer: {e}")

@socketio.on('answer')
def handle_answer(data):
    try:
        if host_id:
            logger.info(f"Forwarding answer to host {host_id}")
            socketio.emit('answer', {'answer': data['answer']}, to=host_id)
        else:
            logger.warning("Cannot forward answer: no host available")
    except Exception as e:
        logger.error(f"Error handling answer: {e}")

@socketio.on('candidate')
def handle_candidate(data):
    try:
        sender_id = request.sid
        if sender_id == host_id:
            if len(connected_users) > 1:
                target_id = [uid for uid in connected_users if uid != host_id][0]
                logger.info(f"Forwarding ICE candidate from host to client {target_id}")
                socketio.emit('candidate', {'candidate': data['candidate']}, to=target_id)
            else:
                logger.warning("Cannot forward ICE candidate: no client connected")
        else:
            logger.info(f"Forwarding ICE candidate from client to host {host_id}")
            socketio.emit('candidate', {'candidate': data['candidate']}, to=host_id)
    except Exception as e:
        logger.error(f"Error handling ICE candidate: {e}")

@socketio.on('connection-failed')
def handle_connection_failed(data):
    """Handle notification that WebRTC connection failed"""
    user_id = request.sid
    logger.warning(f"Connection failed for user {user_id}: {data.get('reason', 'Unknown reason')}")
    socketio.emit('try-reconnect', room=user_id)

@socketio.on('chat-message')
def handle_chat_message(message):
    sender = request.sid
    sender_type = 'Host' if sender == host_id else 'Client'
    logger.info(f"Chat message from {sender_type}: {message[:20]}...")
    socketio.emit('chat-message', f"{sender_type}: {message}", to=connected_users)

@socketio.on('transcription')
def handle_transcription(data):
    sender = request.sid
    socketio.emit('transcription', {
        'text': data['text'],
        'sender': sender
    }, to=connected_users)
@socketio.on('heartbeat')
def handle_heartbeat():
    user_id = request.sid
    logger.debug(f"Heartbeat from {user_id}")
    socketio.emit('heartbeat-response', {'status': 'ok'}, to=user_id)

if __name__ == '__main__':
    port = 8080
    print('NetStream Video Chat Server')
    print('---------------------------')
    print(f'Local access: http://localhost:{port}')
    print('For external access through ngrok, run:')
    print(f'ngrok http {port}')
    print('Then share the ngrok URL with others')
    
    try:
        http_server = WSGIServer(('0.0.0.0', port), app, handler_class=WebSocketHandler)
        logger.info(f'Server running on http://0.0.0.0:{port}')
        http_server.serve_forever()
    except OSError as e:
        logger.error(f'Server error: {e}')
        print(f'Server error: {e}')