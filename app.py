from flask import Flask, request, render_template, send_file, after_this_request
# import magic
import main
import time
import io
import os

app = Flask(__name__)

ALLOWED_IMAGE_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif'}
ALLOWED_VIDEO_MIME_TYPES = {    'video/mp4', 
    'video/x-msvideo',
    'video/quicktime',
    'video/x-ms-wmv',
    }

def allowed_file_mime(file_stream, allowed_mime_types):
    # mime = magic.from_buffer(file_stream.read(2048), mime=True, )
    # file_stream.seek(0)  # Reset file stream position after reading
    # return mime in allowed_mime_types
    return True

@app.route('/')
def index():
    return render_template('index.html')
        
@app.route('/upload/image', methods=['POST'])
def upload_image():
    if 'imageFile' not in request.files:
        return 'No file part', 400
    file = request.files['imageFile']
    if file.filename == '':
        return 'No selected file', 400
    if not allowed_file_mime(file.stream, ALLOWED_IMAGE_MIME_TYPES):
        return 'Invalid file type', 400
    processed_frame = main.detect_in_image(file)
    return send_file(io.BytesIO(processed_frame), as_attachment=True, download_name="processed_image.jpeg", mimetype='image/jpeg')

@app.route('/upload/video', methods=['POST'])
def upload_video():
    if 'videoFile' not in request.files:
        return 'No file part', 400
    file = request.files['videoFile']
    if file.filename == '':
        return 'No selected file', 400
    if not allowed_file_mime(file.stream, ALLOWED_VIDEO_MIME_TYPES):
        return 'Invalid file type', 400
    processed_video_path = main.detect_in_video(file)

    @after_this_request
    def remove_file(response):
        time.sleep(5)
        try:
            os.remove(processed_video_path)
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle", error)
        return response  
    return send_file(processed_video_path, as_attachment=True, download_name=f"processed_video.mp4")

@app.route('/live_detection', methods=['POST'])
def process_frame():
    if 'frame' not in request.files:
        return 'No file part', 400
    file = request.files['frame']
    if file.filename == '':
        return 'No selected file', 400
    frame = file.read()
    processed_frame = main.live_detect(frame)
    return send_file(io.BytesIO(processed_frame), as_attachment=True, download_name="processed_frame.jpeg", mimetype='image/jpeg')


if __name__ == '__main__':
    app.run(debug=False)