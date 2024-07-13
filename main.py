import ffmpeg
import subprocess
import os
import cv2
import tempfile
import numpy as np

script_dir = os.path.dirname(os.path.realpath(__file__))

face_cascade_path = os.path.join(script_dir, "models/face_cascade.xml")
eye_cascade_path = os.path.join(script_dir, "models/eye_cascade.xml")
face_cascade = cv2.CascadeClassifier(face_cascade_path)
eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

def detect(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, minNeighbors=10, scaleFactor=1.1, minSize=(32,32))
    for (x,y,w,h) in faces:
        cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]
        eyes = eye_cascade.detectMultiScale(roi_gray, minNeighbors=10, scaleFactor=1.4, minSize=(30,30), maxSize=(100,100))
        for (ex,ey,ew,eh) in eyes:
            cv2.rectangle(roi_color, (ex,ey), (ex+ew,ey+eh), (0,255,0), 2)
    return frame

def detect_in_image(file):
    file = np.frombuffer(bytearray(file.read()), np.uint8)
    img = cv2.imdecode(file, cv2.IMREAD_COLOR)
    img = detect(img)  
    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()


def detect_in_video(file):
    input_file_path = tempfile.NamedTemporaryFile(delete=True, suffix=os.path.splitext(file.filename)[1]).name
    file.save(input_file_path)
    cap = cv2.VideoCapture(input_file_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    codec = cv2.VideoWriter_fourcc(*'avc1')

    output_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    out = cv2.VideoWriter(output_file_path, codec, fps, (width, height))
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = detect(frame)
        out.write(frame)
    cap.release()
    out.release()

    final_output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    input_video = ffmpeg.input(input_file_path)
    processed_video = ffmpeg.input(output_file_path)
    ffmpeg.output(processed_video.video, input_video.audio, final_output_path, vcodec='copy', acodec='aac', strict='experimental').run(overwrite_output=True)
    os.remove(input_file_path)
    os.remove(output_file_path)
    return final_output_path

# Individual frame of live video feed is given as input frame
def live_detect(frame):  
    frame = np.frombuffer(frame, np.uint8)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    frame = detect(frame)
    _, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes()
