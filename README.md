# NetStream

A real-time video chat application with screen sharing and live transcription capabilities built using WebRTC, Flask, and Socket.IO.

## Features

- 🎥 Real-time video and audio streaming
- 🖥️ Screen sharing functionality
- 💬 Text chat between participants
- 🗣️ Live speech-to-text transcription
- 🔄 Automatic connection recovery
- 👥 Host/Client role management
- 📱 Responsive design

## Technology Stack

- **Frontend**: HTML5, JavaScript, WebRTC API
- **Backend**: Python, Flask
- **WebSocket**: Socket.IO
- **Server**: Gevent WSGI Server
- **Additional APIs**: Web Speech API for transcription

## Prerequisites

- Python 3.7+
- Modern web browser (Chrome/Edge recommended for full feature support)

## Installation

1. Clone the repository:
```sh
git clone https://github.com/Preeeeetham/NetStream.git
cd NetStream
```

2. Install required Python packages:
```sh
pip install flask flask-socketio flask-cors gevent gevent-websocket
```

## Usage

1. Start the server:
```sh
python videoapp.py
```

2. Access the application:
   - Local access: http://localhost:8080
   - For external access, use ngrok:
     ```sh
     ngrok http 8080
     ```

3. Share the URL with another user to start video chat

## Features Guide

### Video Controls
- Toggle audio mute
- Toggle video mute
- Switch between camera and screen sharing

### Chat Features
- Real-time text chat
- Live speech transcription (Chrome/Edge only)

### Connection Management
- Automatic host/client role assignment
- Automatic reconnection on connection loss
- ICE server fallback options

## Development

The application uses a single-page architecture with the following components:
- WebRTC for peer-to-peer connections
- Socket.IO for signaling
- Web Speech API for transcription
- Responsive UI with modern CSS

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Acknowledgments

- Built with Flask and Socket.IO
- Uses WebRTC for peer-to-peer communication
- Implements Web Speech API for transcription