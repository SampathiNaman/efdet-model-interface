document.addEventListener('DOMContentLoaded', () => {
    const imageUploadForm = document.getElementById('imageUploadForm');
    const videoUploadForm = document.getElementById('videoUploadForm');
    const canvas = document.getElementById('resultCanvas');
    let context = canvas.getContext('2d');
    let img = new Image();
    const videoElement = document.getElementById('resultVideo');
    const captureButton = document.getElementById('capture');
    const stopButton = document.getElementById('stopCapture');
    const errorElement = document.getElementById('errorMessage');
    let captureInterval = null;
    let videoStream = null;
    let canvasSizeSet = false;
    
    const displayImage = (url) => {
        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            context.drawImage(img, 0, 0); 
        }
        img.src = url;
    };
    const displayVideo = (url) => {
        videoElement.src = url;
        videoElement.play();
    }
    const displayStreamImage = (url) => {
        if (!canvasSizeSet && captureInterval) {
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            canvasSizeSet = true;
            canvas.style.display = "block";
        }
        requestAnimationFrame(() => {
            img.onload = () => {
                context.drawImage(img, 0, 0, canvas.width, canvas.height);
            };
            img.src = url;
        });
    }

    const handleSubmit = async (event) => {
        event.preventDefault();
        stopRealTimeCapture();
        errorElement.textContent = 'Processing uploaded file...';
        const formData = new FormData(event.target);
        try {
            const response = await fetch(event.target.action, {
                method: 'POST',
                body: formData,
            }); 
            if (response.ok) {
                stopRealTimeCapture();
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                if (blob.type.startsWith('image/')) {
                    canvas.style.display = "block";
                    videoElement.style.display = "none";
                    displayImage(url) 
                 } else {
                    alert("Video is processed and ready to play.");
                    canvas.style.display = "none";
                    videoElement.style.display = "block";
                    displayVideo(url);
                 }
                errorElement.textContent = '';
            } else if (response.status === 400) {
                errorElement.textContent = await response.text();
            }
            else {
                errorElement.textContent = 'Couldn\'t upload file. Click on "Stop Capture" and try uploading again.';
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    const startRealTimeCapture = async () => {
        if (captureInterval) clearInterval(captureInterval);
        if (!navigator.mediaDevices) {
            console.error("navigator.mediaDevices not supported by this browser.");
            alert("navigator.mediaDevices not supported by this browser. Please try another browser.");
            return;
        }
        try {
            videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
            videoElement.srcObject = videoStream;
            videoElement.play();
            videoElement.style.display = "none";
        } catch (error) {
            console.error('Error initializing video stream:', error);
            alert("Error initializing video stream. Please check your camera and try again.");
            return;
        }
        canvasSizeSet = false;
        errorElement.textContent = '';
        captureInterval = setInterval(async () => {
            if (videoStream.readyState === videoStream.HAVE_ENOUGH_DATA) {
                canvas.width = videoElement.videoWidth;
                canvas.height = videoElement.videoHeight;
                context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
                canvas.toBlob(async (blob) => {
                    const formData = new FormData();
                    formData.append('frame', blob, 'frame.jpg');
                    const response = await fetch('/live_detection', {
                        method: 'POST',
                        body: formData,
                    });
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = URL.createObjectURL(blob);
                        displayStreamImage(url);
                    }
                }, 'image/jpg');
            }
        }, 100);
    }

    const stopRealTimeCapture = () => {
        clearInterval(captureInterval);
        captureInterval = null;
        canvasSizeSet = false;
        context.clearRect(0, 0, canvas.width, canvas.height);
        canvas.style.display = "none";
        if (videoStream && videoStream.getTracks){
            videoStream.getTracks().forEach(track => track.stop());
        }
        videoElement.srcObject = null;
        videoElement.style.display = "none";
    }

    if (imageUploadForm) imageUploadForm.addEventListener('submit', handleSubmit);
    if (videoUploadForm) videoUploadForm.addEventListener('submit', handleSubmit);
    if (captureButton) captureButton.addEventListener('click', startRealTimeCapture);
    if (stopButton) stopButton.addEventListener('click', stopRealTimeCapture);
});

