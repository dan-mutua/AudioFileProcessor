# FastAPI Audio File Processor

This project is a FastAPI application that processes audio files. Users can upload audio files, which are then processed by a background worker using RabbitMQ and Redis for job queuing and status tracking. The application supports WebSocket connections to notify clients about the job status updates in real-time.

## Features

- Upload audio files for processing
- Background job processing using RabbitMQ
- Real-time job status updates via WebSocket
- Job status tracking using Redis

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/your-username/fastapi-audio-file-processor.git
    cd fastapi-audio-file-processor
    ```

2. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Start RabbitMQ and Redis:
    ```sh
    # For RabbitMQ
    sudo service rabbitmq-server start
    
    # For Redis
    sudo service redis-server start
    ```

4. Run the FastAPI application:
    ```sh
    uvicorn main:app --reload
    ```

5. Start the background worker:
    ```sh
    python worker.py
    ```

## Usage

### Upload Audio File for Processing

Endpoint: `POST /convert/`

#### Parameters:

- `charactername` (form data): The name of the character associated with the audio file.
- `audio_file` (form data): The audio file to be processed.

#### Example:

```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/convert/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'charactername=example_character' \
  -F 'audio_file=@path_to_your_audio_file'
