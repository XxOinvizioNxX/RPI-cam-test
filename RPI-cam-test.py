import threading

import cv2
from flask import Flask, render_template, Response, redirect, request
import socket

CAMERA_ID = 0

app = Flask(__name__)
frame = None
opencv_working = False


@app.route('/')
def index():
    """
    Main server page
    """
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    """
    Video from camera as JPEG image
    """
    global frame, opencv_working

    # Start new OpenCV thread
    if not opencv_working:
        opencv_working = True
        threading.Thread(target=opencv_thread).start()
        while frame is None:
            pass

    if frame is not None:
        # Make response with encoded frame as JPEG image
        new_response = Response(gen(),
                                mimetype="multipart/x-mixed-replace; boundary=frame")
        new_response.headers.add('Connection', 'close')
        new_response.headers.add('Max-Age', '0')
        new_response.headers.add('Expires', '0')
        new_response.headers.add('Cache-Control',
                                 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        new_response.headers.add('Pragma', 'no-cache')
        new_response.headers.add('Access-Control-Allow-Origin', '*')
        return new_response
    else:
        # Clear flag to reconnect to camera
        opencv_working = False
        return '', 204


@app.route('/move/<string:direction>')
def video_feed(direction):
    """
    Called from a GET request
    """
    print('New HTTP GET request! Moving', direction)
    return direction, 200


def opencv_thread():
    """
    Just reads the image from the camera into the frame
    """
    global frame, opencv_working
    try:
        # Start the camera
        capture = cv2.VideoCapture(CAMERA_ID)
        while opencv_working:
            # Read the frame
            ret, frame = capture.read()
            if not ret:
                print('Frame is empty!')
    except Exception as e:
        print('Error during openCV video thread!', e)

    # Clear flag
    opencv_working = False


def gen():
    """
    Encodes the camera image to JPG
    """
    global frame
    while True:
        if frame is not None:
            (flag, encoded_image) = cv2.imencode('.jpg', frame)
            if not flag:
                continue
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(encoded_image) + b'\r\n')
        else:
            break


if __name__ == '__main__':
    # Find local IP
    local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    local_socket.connect(('8.8.8.8', 80))
    local_ip = local_socket.getsockname()[0]

    # Start the server
    app.run(host=local_ip, port='5000', debug=False)
