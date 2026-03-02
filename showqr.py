import qrcode
import socket

def show_qr():
    # Get local IP automatically
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    
    url = f"http://{local_ip}:8501"
    print(f"Generating QR for: {url}")
    qrcode.make(url).show()

if __name__ == "__main__":
    show_qr()