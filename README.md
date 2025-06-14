This guide will walk you through creating the serverless application that automatically converts your uploaded text notes into audio files you can listen to anywhere. We will follow the exact architecture from the video: an S3 bucket triggers a Lambda function, which uses Amazon Polly to perform the text-to-speech conversion.

[Watch the demo video](./Screen%20Recording%202025-06-14%20at%201.38.30%20PM.mov)

### **Step 1: Create the IAM Role (Granting Permissions)**

![Screenshot showing IAM role creation](./Screenshot%202025-06-14%20at%2012.31.22%20PM.png)

First, we need to create a security role that allows our Lambda function to access other AWS services—specifically, to read from S3, write logs to CloudWatch, and use Amazon Polly.

1. **Navigate to IAM:** Open the AWS Management Console and search for `IAM`.
2. **Create Role:** In the IAM dashboard, click on **Roles** in the left sidebar, then click the **Create role** button.
3. **Select Trusted Entity:**
    - For "Trusted entity type," select **AWS service**.
    - For "Service or use case," choose **Lambda**.
    - Click **Next**.
4. **Add Permissions:** We need to attach three policies to this role.
    - In the search bar, type `AWSLambdaBasicExecutionRole` and check the box next to it. This allows the function to write logs.
    - Search for `AmazonS3ReadOnlyAccess` and check the box. This allows the function to read the text file you upload.
    - Search for `AmazonPollyFullAccess` and check the box. This gives the function permission to use the Polly service. _(For production, you'd use a more restrictive policy, but this is fine for our project)._
5. **Name the Role:**
    - Click **Next**.
    - On the "Name, review, and create" page, give your role a memorable name, like `VoiceVault-Lambda-Role`.
    - Click **Create role**.


### **Step 2: Create the S3 Buckets**

We need two S3 buckets: one to upload the source text files and another to store the output MP3 audio files.

![Screenshot showing S3 bucket creation](./Screenshot%202025-06-14%20at%2012.38.05%20PM.png)

1. **Navigate to S3:** In the AWS Console, search for `S3`.
2. **Create Input Bucket:**
    - Click **Create bucket**.
    - Give it a **globally unique name**, like `voice-vault-notes-input-[your-initials]`.
    - Ensure the **AWS Region** is the same one you plan to use for your Lambda function.
    - Leave all other settings as default and click **Create bucket**.
3. **Create Output Bucket:**
    - Click **Create bucket** again.
    - Give it another unique name, like `voice-vault-audio-output-[your-initials]`.
    - Use the same AWS Region.
    - Leave all other settings as default and click **Create bucket**.

### **Step 3: Create the Lambda Function**

This is the core of our project where the logic lives.

![Screenshot showing Lambda function creation](./Screenshot%202025-06-14%20at%2012.44.41%20PM.png)

1. **Navigate to Lambda:** In the AWS Console, search for `Lambda`.
    
2. **Create Function:**
    
    - Click **Create function**.
    - Select **Author from scratch**.
    - **Function name:** Enter `VoiceVault-Processor`.
    - **Runtime:** Select **Python 3.12** (or a recent Python version).
    - **Architecture:** Leave it as `x86_64`.
3. **Assign Permissions:**
    
    - Expand the **Change default execution role** section.
    - Select **Use an existing role**.
    - From the dropdown, choose the `VoiceVault-Lambda-Role` you created in Step 1.
4. **Create the Function:** Click **Create function**.
    
5. **Add the Python Code:**
    
    - You will be taken to the function's configuration page. Scroll down to the **Code source** editor.
    - Delete the default boilerplate code and paste the following Python code:


- **Add Environment Variable:**
    
    - Go to the **Configuration** tab and click **Environment variables**.
    - Click **Edit**, then **Add environment variable**.
    - For **Key**, enter `DESTINATION_BUCKET`.
    - For **Value**, enter the name of your output S3 bucket (e.g., `voice-vault-audio-output-[your-initials]`).
    - Click **Save**.
- **Deploy the Code:** Click the **Deploy** button above the code editor to save your changes.


### **Step 4: Configure the S3 Trigger**

The final step is to connect your input S3 bucket to your Lambda function.

1. **Add Trigger:** In your Lambda function's page (`VoiceVault-Processor`), click **Add trigger** in the "Function overview" diagram.
2. **Configure Trigger:**
    - In the "Select a source" dropdown, choose **S3**.
    - **Bucket:** Select your input bucket (`voice-vault-notes-input-...`).
    - **Event type:** Leave it as **All object create events**.
    - **Suffix (Optional but Recommended):** To ensure the function only runs on text files, enter `.txt` in the suffix field. This prevents infinite loops if you accidentally upload to the wrong bucket.
3. **Acknowledge and Add:** Check the box that says "I acknowledge that using S3 to invoke Lambda functions..."
4. Click **Add**.


### **Let's Test It.**

Your entire "Voice Vault" system is now built. To test it:

1. Create a simple text file on your computer named `my-notes.txt`. Inside the file, write a few sentences like, "Project one is the voice vault. This project turns study notes into mini-podcasts."
2. Navigate to your **input S3 bucket** (`voice-vault-notes-input-...`) in the AWS console.
3. Click **Upload**, then **Add files**, and select your `my-notes.txt` file. Click **Upload**.
4. Wait a few seconds. This upload action triggers your Lambda function.
5. Now, navigate to your **output S3 bucket** (`voice-vault-audio-output-...`). You should see a new file named `my-notes.mp3`.
6. Click on the `my-notes.mp3` file, then click the **Download** button. Open the downloaded file to hear the audio version of your notes

![Pasted image 20250614134207](./Pasted%20image%2020250614134207.png)

![Pasted image 20250614134000](./Pasted%20image%2020250614134000.png)


### Advanced Features & Improvements

The initial version of this project was great, but real-world use required making it more robust. The current `lambda_function.py` in this repository includes several key upgrades:

* **Markdown File Support:** The function now automatically detects `.md` files. It intelligently strips all Markdown formatting (like headers, bullet points, and links) to produce a clean, natural-sounding audio file.

* **Long-Form Content Processing:** The initial version would fail on long documents due to API limits. The code now automatically splits long texts into smaller chunks, processes each one with Amazon Polly, and seamlessly stitches the audio back together into a single MP3 file.

* **Robust File Name Handling:** The code now correctly handles filenames that contain spaces or other special characters, which previously caused errors.

* **Increased Timeout for Large Files:** To handle the extra processing time required for long documents, the function's timeout has been increased. This ensures even large, complex notes can be converted without interruption.

### Project Evolution & Troubleshooting Steps

This list documents the steps taken to develop the Voice Vault project from a simple script into a robust application.

1. **Corrected Initial Permissions:**
    
    - **Problem:** The function executed but no audio file was saved to the output S3 bucket.
    - **Diagnosis:** CloudWatch logs showed an `AccessDenied` error when calling `s3:PutObject`.
    - **Action:** The Lambda's IAM Role was updated with `AmazonS3FullAccess` permissions to allow the function to write files to the destination S3 bucket.
2. **Added Support for Markdown Files (`.md`):**
    
    - **Problem:** The function needed to process `.md` files, not just `.txt` files, and intelligently handle the Markdown syntax.
    - **Action:**
        - The S3 trigger's suffix filter (`.txt`) was removed.
        - The Python script was updated to include the `markdown` and `beautifulsoup4` libraries to strip formatting and extract clean, readable text.
3. **Created a Lambda Deployment Package:**
    
    - **Problem:** The new Python libraries were not included in the standard AWS Lambda runtime.
    - **Action:** A `.zip` deployment package was created by installing the libraries and the `lambda_function.py` script into a local folder and then compressing the contents.
4. **Corrected Deployment Package Structure:**
    
    - **Problem:** The function failed to start, showing a `Runtime.ImportModuleError: No module named 'lambda_function'` in the logs.
    - **Diagnosis:** The `.zip` file contained a parent folder, preventing Lambda from finding the script at the root level.
    - **Action:** The `.zip` file was recreated, ensuring all files (the `.py` script and library folders) were at the top level of the archive.
5. **Added Handling for Filenames with Spaces:**
    
    - **Problem:** Files with spaces in their names caused a `NoSuchKey` error.
    - **Diagnosis:** S3 URL-encodes spaces in filenames within the event notification sent to Lambda (e.g., "My Note.md" becomes "My+Note.md").
    - **Action:** The Python script was updated to use `urllib.parse.unquote_plus()` to decode the filename back to its original state before trying to access the file in S3.
6. **Implemented Text Chunking for Long Documents:**
    
    - **Problem:** Processing long files resulted in a `TextLengthExceededException` from the Amazon Polly API.
    - **Diagnosis:** The total text size was larger than Polly's character limit for a single API call.
    - **Action:** The code was refactored to split the source text into smaller chunks (by paragraph). It now loops through each chunk, converts it to audio, and concatenates the audio streams into a single MP3 file.
7. **Increased Function Timeout:**
    
    - **Problem:** The function was being terminated prematurely when processing large files, resulting in a `Status: timeout` error in the logs.
    - **Diagnosis:** The default 3-second Lambda timeout was not long enough for the new chunking process.
    - **Action:** The function's timeout setting was increased in the Lambda configuration to allow sufficient time for processing and saving the audio file.