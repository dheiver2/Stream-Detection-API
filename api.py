from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import cv2
import os
import threading
from ultralytics import YOLO
from queue import Queue
import numpy as np
import logging
import time
import json
from typing import List, Optional
import uuid
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="RTSP Person Detector API",
    description="API para detecção de pessoas em streams RTSP usando YOLO",
    version="1.0.0"
)

# Modelos de dados
class StreamConfig(BaseModel):
    url: str
    stream_id: str
    output_dir: Optional[str] = None

class DetectionResponse(BaseModel):
    message: str
    task_id: str
    streams: List[str]

class StreamStatus(BaseModel):
    stream_id: str
    status: str
    people_detected: int
    last_detection: Optional[str]

# Variáveis globais
active_streams = {}
detection_results = {}
model = None
model_lock = threading.Lock()

# Inicializar modelo YOLO
@app.on_event("startup")
async def startup_event():
    global model
    try:
        model = YOLO("yolo11n.pt")
        logging.info("Modelo YOLO carregado com sucesso")
    except Exception as e:
        logging.error(f"Erro ao carregar modelo YOLO: {e}")
        raise e

class CentroidTracker:
    def __init__(self, max_distance=50):
        self.next_id = 0
        self.centroids = {}
        self.max_distance = max_distance
        self.detections = []

    def update(self, boxes, frame, output_dir, stream_id):
        new_centroids = []
        for box in boxes:
            if int(box.cls) == 0:  # Apenas pessoas
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
                confidence = box.conf.cpu().numpy()[0]
                new_centroids.append((centroid, box, confidence))

        assigned_ids = []
        for centroid, box, confidence in new_centroids:
            matched_id = None
            min_dist = float('inf')
            
            for obj_id, (existing_centroid, _) in self.centroids.items():
                dist = np.sqrt((centroid[0] - existing_centroid[0])**2 + 
                             (centroid[1] - existing_centroid[1])**2)
                if dist < self.max_distance and dist < min_dist:
                    min_dist = dist
                    matched_id = obj_id

            if matched_id is None:
                matched_id = self.next_id
                self.centroids[matched_id] = (centroid, False)
                self.next_id += 1

            saved = self.centroids[matched_id][1]
            self.centroids[matched_id] = (centroid, saved)
            assigned_ids.append((matched_id, box, confidence))

            if not saved:
                try:
                    # Salvar frame anotado
                    annotated_frame = frame.copy()
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(annotated_frame, f"Person {matched_id}", 
                               (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    frame_filename = os.path.join(output_dir, f"person_{stream_id}_{matched_id}_{timestamp}.jpg")
                    cv2.imwrite(frame_filename, annotated_frame)
                    
                    # Registrar detecção
                    detection_info = {
                        "person_id": matched_id,
                        "stream_id": stream_id,
                        "timestamp": datetime.now().isoformat(),
                        "confidence": float(confidence),
                        "bbox": [int(x) for x in box.xyxy[0].cpu().numpy()],
                        "saved_frame": frame_filename
                    }
                    self.detections.append(detection_info)
                    
                    logging.info(f"[Stream {stream_id}] Pessoa ID {matched_id} detectada e salva")
                    self.centroids[matched_id] = (centroid, True)
                    
                except Exception as e:
                    logging.error(f"Erro ao salvar frame: {e}")

        return len(assigned_ids)

def process_stream_api(stream_config: StreamConfig, task_id: str):
    """Processa um stream RTSP para a API."""
    stream_id = stream_config.stream_id
    rtsp_url = stream_config.url
    output_dir = stream_config.output_dir or f"./detections/{stream_id}"
    
    # Criar diretório de saída
    os.makedirs(output_dir, exist_ok=True)
    
    # Inicializar status do stream
    active_streams[stream_id] = {
        "status": "connecting",
        "people_detected": 0,
        "last_detection": None,
        "task_id": task_id
    }
    
    # Configurar OpenCV
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|timeout;30000000"
    
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        active_streams[stream_id]["status"] = "error"
        logging.error(f"[Stream {stream_id}] Erro ao conectar: {rtsp_url}")
        return
    
    active_streams[stream_id]["status"] = "running"
    logging.info(f"[Stream {stream_id}] Conectado com sucesso!")
    
    tracker = CentroidTracker(max_distance=50)
    
    try:
        while active_streams.get(stream_id, {}).get("status") == "running":
            ret, frame = cap.read()
            if not ret:
                logging.warning(f"[Stream {stream_id}] Falha ao capturar frame")
                time.sleep(1)
                continue
            
            with model_lock:
                results = model(frame, conf=0.5, classes=[0])  # Apenas pessoas
            
            people_count = 0
            for result in results:
                if result.boxes is not None and len(result.boxes) > 0:
                    people_count = tracker.update(result.boxes, frame, output_dir, stream_id)
                    
                    if people_count > 0:
                        active_streams[stream_id]["people_detected"] += people_count
                        active_streams[stream_id]["last_detection"] = datetime.now().isoformat()
            
            # Armazenar detecções no resultado global
            if stream_id not in detection_results:
                detection_results[stream_id] = []
            detection_results[stream_id] = tracker.detections
            
            time.sleep(0.1)  # Controlar taxa de processamento
            
    except Exception as e:
        logging.error(f"[Stream {stream_id}] Erro durante processamento: {e}")
        active_streams[stream_id]["status"] = "error"
    finally:
        cap.release()
        if stream_id in active_streams:
            active_streams[stream_id]["status"] = "stopped"
        logging.info(f"[Stream {stream_id}] Stream finalizado")

# Endpoints da API

@app.get("/")
async def root():
    return {"message": "RTSP Person Detector API", "version": "1.0.0"}

@app.post("/start-detection", response_model=DetectionResponse)
async def start_detection(streams: List[StreamConfig], background_tasks: BackgroundTasks):
    """Inicia a detecção de pessoas em um ou mais streams RTSP."""
    if not model:
        raise HTTPException(status_code=500, detail="Modelo YOLO não carregado")
    
    task_id = str(uuid.uuid4())
    stream_ids = []
    
    for stream_config in streams:
        stream_id = stream_config.stream_id
        
        # Verificar se o stream já está ativo
        if stream_id in active_streams and active_streams[stream_id]["status"] == "running":
            raise HTTPException(status_code=400, detail=f"Stream {stream_id} já está ativo")
        
        # Iniciar processamento em background
        background_tasks.add_task(process_stream_api, stream_config, task_id)
        stream_ids.append(stream_id)
    
    return DetectionResponse(
        message="Detecção iniciada com sucesso",
        task_id=task_id,
        streams=stream_ids
    )

@app.get("/status")
async def get_status():
    """Retorna o status de todos os streams ativos."""
    status_list = []
    for stream_id, info in active_streams.items():
        status_list.append(StreamStatus(
            stream_id=stream_id,
            status=info["status"],
            people_detected=info["people_detected"],
            last_detection=info.get("last_detection")
        ))
    return {"active_streams": len(active_streams), "streams": status_list}

@app.get("/status/{stream_id}")
async def get_stream_status(stream_id: str):
    """Retorna o status de um stream específico."""
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream não encontrado")
    
    info = active_streams[stream_id]
    return StreamStatus(
        stream_id=stream_id,
        status=info["status"],
        people_detected=info["people_detected"],
        last_detection=info.get("last_detection")
    )

@app.get("/detections/{stream_id}")
async def get_detections(stream_id: str):
    """Retorna todas as detecções de um stream específico."""
    if stream_id not in detection_results:
        raise HTTPException(status_code=404, detail="Nenhuma detecção encontrada para este stream")
    
    return {
        "stream_id": stream_id,
        "total_detections": len(detection_results[stream_id]),
        "detections": detection_results[stream_id]
    }

@app.post("/stop/{stream_id}")
async def stop_stream(stream_id: str):
    """Para a detecção em um stream específico."""
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream não encontrado")
    
    active_streams[stream_id]["status"] = "stopping"
    return {"message": f"Stream {stream_id} será parado"}

@app.post("/stop-all")
async def stop_all_streams():
    """Para a detecção em todos os streams ativos."""
    stopped_streams = []
    for stream_id in active_streams.keys():
        active_streams[stream_id]["status"] = "stopping"
        stopped_streams.append(stream_id)
    
    return {"message": "Todos os streams serão parados", "streams": stopped_streams}

@app.get("/download/{stream_id}/{filename}")
async def download_frame(stream_id: str, filename: str):
    """Baixa um frame salvo específico."""
    file_path = f"./detections/{stream_id}/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='image/jpeg'
    )

@app.delete("/clear/{stream_id}")
async def clear_detections(stream_id: str):
    """Limpa as detecções de um stream específico."""
    if stream_id in detection_results:
        del detection_results[stream_id]
    
    if stream_id in active_streams:
        del active_streams[stream_id]
    
    return {"message": f"Detecções do stream {stream_id} foram limpas"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
