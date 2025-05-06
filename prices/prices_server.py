import cv2
import os
import time
import threading
from flask import Flask, Response, send_file
from datetime import datetime, timedelta
from prices_generator import get_prices

UPDATE_INTERVAL = 3600  # seconds (1 hour)

app = Flask(__name__)

# Schedule chart regeneration every hour
def schedule_image_update():
    def update_and_reschedule():
        while True:
            print("[INFO] Generating new chart image...")
            get_prices()
            time.sleep(UPDATE_INTERVAL)

    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    delay = (next_hour - now).total_seconds()
    print(f'Next prices in {delay} seconds')

    # Start the first timer to hit the top of the hour
    threading.Timer(delay, update_and_reschedule).start()

# MJPEG stream generator
def generate_stream():
    while True:
        timestamp = datetime.now().strftime('%Y%m%d%H')
        output_filename = f'{timestamp}_prices.png'
        output_path = os.path.join('images', output_filename)

        if os.path.exists(output_path):
            image = cv2.imread(output_path)
            if image is not None:
                _, jpeg = cv2.imencode('.jpg', image)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(1)

@app.route('/prices.png')
def serve_chart():
    timestamp = datetime.now().strftime('%Y%m%d%H')
    output_filename = f'{timestamp}_prices.png'
    output_path = os.path.join('images', output_filename)
    
    if not os.path.exists(output_path):
        return "Image not found", 404
    
    return send_file(output_path, mimetype='image/png')

@app.route('/prices')
def video_feed():
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Initial chart
    get_prices()

    # Run image generation thread
    threading.Thread(target=schedule_image_update, daemon=True).start()

    # Start web server
    app.run(host='0.0.0.0', port=8080)