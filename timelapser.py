import os
import time
import zipfile
from http.server import HTTPServer, SimpleHTTPRequestHandler
from picamera2 import Picamera2
from datetime import datetime
from threading import Thread

SAVE_DIR = "/home/pi/photos"
os.makedirs(SAVE_DIR, exist_ok=True)

def capture_photo():
    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration()) 
    picam2.start()

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = os.path.join(SAVE_DIR, f"photo_{timestamp}.jpg")
            
            picam2.capture_file(file_path)
            print(f"Foto salvata: {file_path}")

            time.sleep(60)#delay 1 min

    finally:
        picam2.stop()

def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp_millidegrees = int(f.read().strip())
    return temp_millidegrees / 1000.0  

def create_zip():
    zip_filename = os.path.join(SAVE_DIR, "photos.zip")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(SAVE_DIR):
            for file in files:
                if file.endswith('.jpg'):
                    zipf.write(os.path.join(root, file), file)
    return zip_filename

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/temperature": #temperature page
            temp = get_cpu_temperature()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Temperatura CPU</h1><p>{temp:.2f} °C</p></body></html>".encode("utf-8"))
        elif self.path == "/download_photos": #download photo page
            zip_filename = create_zip()
            self.send_response(200)
            self.send_header("Content-type", "application/zip")
            self.send_header("Content-Disposition", f"attachment; filename={os.path.basename(zip_filename)}")
            self.end_headers()
            with open(zip_filename, "rb") as f:
                self.wfile.write(f.read())
        else:
            super().do_GET()

def start_server():
    os.chdir(SAVE_DIR)
    server = HTTPServer(("0.0.0.0", 8000), CustomHTTPRequestHandler)
    print("Server avviato su http://<IP_RASPBERRY>:8000")
    print("Temperatura disponibile su http://<IP_RASPBERRY>:8000/temperature")
    print("Scarica tutte le foto su http://<IP_RASPBERRY>:8000/download_photos")
    server.serve_forever()

if __name__ == "__main__":
    capture_thread = Thread(target=capture_photo, daemon=True)
    capture_thread.start()

    start_server()
