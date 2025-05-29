import requests
import os

def download_file(url, filename):
    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Get the total file size
    total_size = int(response.headers.get('content-length', 0))
    
    # Download with progress
    with open(filename, 'wb') as f:
        if total_size == 0:
            f.write(response.content)
        else:
            downloaded = 0
            for data in response.iter_content(chunk_size=4096):
                downloaded += len(data)
                f.write(data)
                done = int(50 * downloaded / total_size)
                print(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded}/{total_size} bytes", end='')
    print(f"\nDownloaded {filename} successfully!")

def main():
    models = {
        'yolov8n.pt': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt',
        'yolov8x.pt': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8x.pt'
    }
    
    for filename, url in models.items():
        if os.path.exists(filename):
            print(f"{filename} already exists. Skipping...")
            continue
        try:
            download_file(url, filename)
        except Exception as e:
            print(f"Error downloading {filename}: {e}")

if __name__ == "__main__":
    main() 