from fastapi import FastAPI, UploadFile, File, Form, WebSocket
import uuid
import aiofiles
import os
import pika
import json
import asyncio
import aioredis

app = FastAPI()


UPLOAD_DIR = "uploaded_files"

if not os.path.isdir(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def publish_to_rabbitmq(job_id, file_path):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='video_processing_queue')
    job_data = {'job_id': job_id, 'audio_file_path': file_path}
    channel.basic_publish(exchange='',
                          routing_key='video_processing_queue',
                          body=json.dumps(job_data))
    connection.close()

@app.post("/convert/")
async def create_convert_task(charactername: str = Form(...), 
                              audio_file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    file_location = f"{UPLOAD_DIR}/{job_id}_{audio_file.filename}"
    
    # Save uploaded file
    async with aiofiles.open(file_location, 'wb') as out_file:
        content = await audio_file.read()  # Read file content
        await out_file.write(content)  # Write to disk
    
    # Publish job details to RabbitMQ for processing
    publish_to_rabbitmq(job_id, file_location)
    
    return {"job_id": job_id, "file_location": file_location}

@app.post("/convert_full/")
async def create_convert_task(charactername: str = Form(...), 
                              audio_file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    file_location = f"{UPLOAD_DIR}/{job_id}_{audio_file.filename}"
    
    # Save uploaded file
    async with aiofiles.open(file_location, 'wb') as out_file:
        content = await audio_file.read()  # Read file content
        await out_file.write(content)  # Write to disk
    
    # Publish job details to RabbitMQ for processing
    publish_to_rabbitmq(job_id, file_location)
    
    return {"job_id": job_id, "file_location": file_location}


async def startup():
    # Create a Redis connection
    app.redis = await aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)

async def shutdown():
    await app.redis.close()

@app.on_event("startup")
async def startup_event():
    await startup()

@app.on_event("shutdown")
async def shutdown_event():
    await shutdown()

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):    
    await websocket.accept()
    await websocket.send_text(f"Subscribed to updates for job {job_id}")

    while True:
        job_data = await app.redis.get(job_id)
        if job_data:
            job_info = json.loads(job_data)
            if job_info['status'] == 'completed':
                await websocket.send_text(f"Job completed. Processed file located at: {job_info['file_location']}")
                break
        await asyncio.sleep(1)  # Adjust polling rate as needed

    await websocket.close()