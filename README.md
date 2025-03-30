# Voice Thought Recorder

A web application that allows you to record your thoughts and automatically transcribe them using OpenAI's Whisper API.

Currently labeled as Voice Input for AI tools.

## Features

- Record audio thoughts directly from your browser
- Automatic transcription using OpenAI's Whisper API
- Play back your recorded thoughts
- View transcriptions alongside recordings
- Copy transcriptions to clipboard
- Delete recordings and their transcriptions
- Real-time cost tracking and duration display
- Modern and responsive UI

## Cost Information

This application uses OpenAI's Whisper API for transcription, which has the following pricing:
- $0.006 per minute of audio
- Costs are calculated and displayed per recording
- Running total of all transcription costs is maintained
- Cost information persists across sessions

Example costs:
- 30-second recording: $0.003
- 1-minute recording: $0.006
- 5-minute recording: $0.030

## Setup

### Local Development

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```
   Note: The app will also check for an `.env` file if the environment variable is not set.

3. To run manually:
   ```bash
   python3 app.py
   ```

### Docker Setup

1. Build and run using Docker:
   ```bash
   # Build the Docker image
   docker build -t voice-app .
   
   # Run the container
   docker run -p 5001:5001 -e OPENAI_API_KEY=your_api_key_here voice-app
   ```

2. Or use Docker Compose:
   ```bash
   # Edit docker-compose.yml to add your OpenAI API key
   # Then run:
   docker-compose up -d
   ```

### Systemd Service (Local Setup)

1. To set up as an auto-starting service:
   ```bash
   # Create the systemd user directory
   mkdir -p ~/.config/systemd/user

   # Copy the service file
   cp voice-recorder.service ~/.config/systemd/user/

   # Reload systemd
   systemctl --user daemon-reload

   # Enable and start the service
   systemctl --user enable voice-recorder
   systemctl --user start voice-recorder
   ```

### AWS Fargate Deployment

For deploying to AWS Fargate, see the detailed instructions in [aws-fargate-deployment.md](aws-fargate-deployment.md).

### GitHub Actions CI/CD

This project includes GitHub Actions workflows for continuous integration and deployment to AWS:

1. Automated deployment to AWS when changes are pushed to the main branch
2. Secure authentication with AWS using OpenID Connect (OIDC)
3. Environment-specific deployments (dev, staging, prod)

For secure GitHub Actions setup with AWS OIDC authentication, see [aws-oidc-setup.md](aws-oidc-setup.md).

## Service Management

The application can run as a systemd user service, which means:
- Starts automatically when you log in
- Stops cleanly when you log out
- Runs under your user account (no root privileges needed)
- Automatically restarts if it crashes

### Service Commands

Check status:
```bash
systemctl --user status voice-recorder
```

Start the service:
```bash
systemctl --user start voice-recorder
```

Stop the service:
```bash
systemctl --user stop voice-recorder
```

Restart the service:
```bash
systemctl --user restart voice-recorder
```

View logs:
```bash
journalctl --user -u voice-recorder
```

Disable auto-start:
```bash
systemctl --user disable voice-recorder
```

## Usage

1. Open your browser and navigate to `http://localhost:5001`
2. Click the "Start Recording" button to begin recording your thought
3. Speak your thought clearly into your microphone
4. Click "Stop Recording" when you're finished
5. Wait for the transcription to complete
6. Your recorded thought will appear in the list with:
   - Audio playback controls
   - Transcription text
   - Copy button for the transcription
   - Delete button for the recording
   - Duration and cost information

## Requirements

- Python 3.7+ (for local development)
- Docker (for containerized deployment)
- OpenAI API key
- Modern web browser with microphone access
- Internet connection for transcription

## Files

- `app.py`: Main Flask application
- `templates/index.html`: Web interface
- `voice-recorder.service`: Systemd service configuration
- `recordings/`: Directory for audio files and cost tracking
- `requirements.txt`: Python dependencies
- `.env`: Optional file for API key (if not set in environment)
- `Dockerfile`: Container definition for Docker deployment
- `docker-compose.yml`: Docker Compose configuration for local container deployment
- `.dockerignore`: Files to exclude from Docker builds
- `aws-fargate-deployment.md`: Guide for AWS Fargate deployment

## Security Notes

- The service runs only under your user account (in local mode)
- No root privileges are required
- Audio files are stored locally in the `recordings` directory or in a Docker volume
- The OpenAI API key can be provided via environment variable or `.env` file
- For AWS deployment, use AWS Secrets Manager for the API key
- The `.dockerignore` file prevents sensitive files from being included in Docker images
- No personal information is included in the Docker image

## Troubleshooting

### Local Service
If the service fails to start:
1. Check the logs: `journalctl --user -u voice-recorder`
2. Verify the OpenAI API key is set
3. Ensure port 5001 is not in use
4. Check file permissions in the recordings directory

### Docker
If the Docker container fails to start:
1. Check Docker logs: `docker logs <container_id>`
2. Verify the environment variables are correctly set
3. Ensure port 5001 is not already in use on your host
4. Check if the Docker volume for recordings is properly mounted

### AWS Fargate
If the Fargate service fails to start:
1. Check the CloudWatch logs for the ECS task
2. Verify the task definition includes all required environment variables
3. Check that the security groups allow traffic on port 5001
4. Verify the EFS mount is correctly configured (if using persistent storage)
