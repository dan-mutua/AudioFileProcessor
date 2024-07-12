import redis
import json
import os
import subprocess
import pika
import time

# Setup Redis connection
redis_conn = redis.Redis(host='localhost', port=6379, db=0)

# Setup RabbitMQ connection
rabbitmq_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = rabbitmq_connection.channel()

# Ensure the queue exists
channel.queue_declare(queue='video_processing_queue')

def update_progress_in_redis(job_id, progress):
    redis_conn.set(f"{job_id}_progress", json.dumps({'status': 'progress', 'progress': progress}))

def process_audio_file(input_file_path, job_id):
    
    for progress in range(0, 101, 10):
        update_progress_in_redis(job_id, progress)
        time.sleep(0.5)

    output_file_path = os.path.splitext(input_file_path)[0] + '_cut.mp3'
    
    # Construct the FFmpeg command to cut the first 5 seconds
    ffmpeg_command = [
        'ffmpeg', '-y',  # '-y' to overwrite output files without asking
        '-i', input_file_path,  # Input file
        '-ss', '0',  # Start cutting from the beginning
        '-t', '5',  # Duration of the cut, in seconds
        output_file_path  # Output file
    ]
    
    # Execute the FFmpeg command
    subprocess.call(ffmpeg_command)
    
    # Report completion and the output file location
    redis_conn.set(job_id, json.dumps({'status': 'completed', 'file_location': output_file_path}))
    
    return output_file_path


def callback(ch, method, properties, body):
    job_data = json.loads(body)
    job_id = job_data['job_id']
    audio_file_path = job_data['audio_file_path']
    
    output_file_path = process_audio_file(audio_file_path)
    
    # Update job status in Redis
    redis_conn.set(job_id, json.dumps({'status': 'completed', 'file_location': output_file_path}))
    
    # Acknowledge the message to RabbitMQ indicating the job is done
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Setup the consumption of messages
channel.basic_consume(queue='video_processing_queue', on_message_callback=callback, auto_ack=False)

print('Worker is started and awaiting jobs')
channel.start_consuming()
