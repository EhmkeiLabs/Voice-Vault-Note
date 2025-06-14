import boto3
import os
import markdown
from bs4 import BeautifulSoup
import urllib.parse

s3 = boto3.client('s3')
polly = boto3.client('polly')

DESTINATION_BUCKET = os.environ['DESTINATION_BUCKET']

def lambda_handler(event, context):
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    source_key = event['Records'][0]['s3']['object']['key']
    source_key = urllib.parse.unquote_plus(source_key)

    if not source_key.lower().endswith(('.txt', '.md')):
        print(f"Skipping file {source_key} as it is not a .txt or .md file.")
        return {'statusCode': 200, 'body': 'File type not supported, skipping.'}

    try:
        response = s3.get_object(Bucket=source_bucket, Key=source_key)
        file_content = response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error getting object {source_key} from bucket {source_bucket}.")
        raise e

    if source_key.lower().endswith('.md'):
        html = markdown.markdown(file_content)
        text_to_process = "".join(BeautifulSoup(html, "html.parser").findAll(text=True))
    else:
        text_to_process = file_content
    
    # --- NEW: Logic to split the text into chunks ---
    # We split by newline to get paragraphs, and filter out any empty ones.
    text_chunks = [chunk for chunk in text_to_process.split('\n') if chunk.strip()]
    
    # This will hold the combined audio data
    combined_audio = bytearray()
    
    # Process each chunk with Polly
    for chunk in text_chunks:
        # Skip chunks that are too long to process even on their own
        if len(chunk) > 3000:
            print(f"Skipping a chunk because it is too long: {chunk[:50]}...")
            continue
            
        try:
            polly_response = polly.synthesize_speech(
                Text=chunk,
                OutputFormat='mp3',
                VoiceId='Joanna'
            )
            # Append the audio stream to our combined audio
            combined_audio.extend(polly_response['AudioStream'].read())
            
        except Exception as e:
            # If one chunk fails, just print an error and continue
            print(f"Error calling Polly for a chunk: {e}")
            continue

    # 4. Save the final combined audio stream to the destination S3 bucket
    if combined_audio:
        try:
            output_key = os.path.splitext(source_key)[0] + '.mp3'
            
            s3.put_object(
                Bucket=DESTINATION_BUCKET,
                Key=output_key,
                Body=combined_audio,
                ContentType='audio/mpeg'
            )
            print(f"Successfully converted {source_key} to {output_key} in {DESTINATION_BUCKET}.")
        except Exception as e:
            print(f"Error saving audio to bucket {DESTINATION_BUCKET}.")
            raise e
    else:
        print("No audio was generated.")
        
    return {
        'statusCode': 200,
        'body': 'Conversion process completed.'
    }