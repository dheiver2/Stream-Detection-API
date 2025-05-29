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
from typing import List, Optional, Dict
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

# Adicionar constantes para classes YOLO
YOLO_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    4: "airplane",
    5: "bus",
    6: "train",
    7: "truck",
    8: "boat",
    9: "traffic light",
    10: "fire hydrant",
    11: "stop sign",
    12: "parking meter",
    13: "bench",
    14: "bird",
    15: "cat",
    16: "dog",
    17: "horse",
    18: "sheep",
    19: "cow",
    20: "elephant",
    21: "bear",
    22: "zebra",
    23: "giraffe",
    24: "backpack",
    25: "umbrella",
    26: "handbag",
    27: "tie",
    28: "suitcase",
    29: "frisbee",
    30: "skis",
    31: "snowboard",
    32: "sports ball",
    33: "kite",
    34: "baseball bat",
    35: "baseball glove",
    36: "skateboard",
    37: "surfboard",
    38: "tennis racket",
    39: "bottle",
    40: "wine glass",
    41: "cup",
    42: "fork",
    43: "knife",
    44: "spoon",
    45: "bowl",
    46: "banana",
    47: "apple",
    48: "sandwich",
    49: "orange",
    50: "broccoli",
    51: "carrot",
    52: "hot dog",
    53: "pizza",
    54: "donut",
    55: "cake",
    56: "chair",
    57: "couch",
    58: "potted plant",
    59: "bed",
    60: "dining table",
    61: "toilet",
    62: "tv",
    63: "laptop",
    64: "mouse",
    65: "remote",
    66: "keyboard",
    67: "cell phone",
    68: "microwave",
    69: "oven",
    70: "toaster",
    71: "sink",
    72: "refrigerator",
    73: "book",
    74: "clock",
    75: "vase",
    76: "scissors",
    77: "teddy bear",
    78: "hair drier",
    79: "toothbrush"
}

# Modelos de dados
class StreamConfig(BaseModel):
    url: str
    stream_id: str
    output_dir: Optional[str] = None
    model_config: Optional[dict] = {
        "model_name": "yolov8n.pt",  # Modelo padrão
        "conf_threshold": 0.5,       # Limiar de confiança
        "classes": [0],              # Classes a detectar (0 = pessoa)
        "img_size": 640,            # Tamanho da imagem
        "process_every_n_frames": 1, # Processar a cada N frames
        "tracking": {               # Configuração de rastreamento
            "enabled": True,        # Habilitar rastreamento
            "type": "centroid",     # Tipo de rastreamento (centroid, deep_sort, etc)
            "max_distance": 50,     # Distância máxima para rastreamento
            "min_confidence": 0.3,  # Confiança mínima para rastreamento
            "max_age": 30,         # Idade máxima do rastreamento
            "min_hits": 3          # Mínimo de detecções para confirmar rastreamento
        },
        "analysis": {              # Configuração de análise
            "enabled": False,      # Habilitar análise
            "type": None,          # Tipo de análise (crowd, queue, behavior, etc)
            "parameters": {}       # Parâmetros específicos da análise
        }
    }
    rtsp_config: Optional[dict] = {
        "timeout": 30000000,        # Timeout em microssegundos
        "buffer_size": 1024,        # Tamanho do buffer
        "reconnect_attempts": 3,    # Tentativas de reconexão
        "reconnect_delay": 5,       # Delay entre tentativas em segundos
        "drop_frames": False,       # Descartar frames em caso de atraso
        "max_queue_size": 10        # Tamanho máximo da fila de frames
    }

class DetectionResponse(BaseModel):
    message: str
    task_id: str
    streams: List[str]

class DetectionInfo(BaseModel):
    object_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: List[int]
    centroid: List[float]
    timestamp: str
    track_id: Optional[int]
    track_history: Optional[List[List[float]]]
    analysis_data: Optional[dict]

class StreamStatus(BaseModel):
    stream_id: str
    status: str
    detections: Dict[str, int]  # Contagem por classe
    last_detection: Optional[str]
    analysis_status: Optional[dict]
    performance_metrics: Optional[dict]

# Variáveis globais
active_streams = {}
detection_results = {}
model_manager = None
model_lock = threading.Lock()

# Inicializar modelo YOLO
@app.on_event("startup")
async def startup_event():
    global model_manager
    try:
        model_manager = ModelManager()
        logging.info("API iniciada")
    except Exception as e:
        logging.error(f"Erro ao iniciar API: {e}")
        raise e

class CentroidTracker:
    def __init__(self, config: dict):
        self.next_id = 0
        self.centroids = {}
        self.track_history = {}
        self.max_distance = config["max_distance"]
        self.min_confidence = config["min_confidence"]
        self.max_age = config["max_age"]
        self.min_hits = config["min_hits"]
        self.detections = []
        self.frame_count = 0

    def update(self, boxes, frame, output_dir, stream_id, model_config):
        self.frame_count += 1
        new_centroids = []
        
        # Processar detecções
        for box in boxes:
            class_id = int(box.cls)
            confidence = float(box.conf.cpu().numpy()[0])
            
            if confidence >= self.min_confidence:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
                new_centroids.append((centroid, box, confidence, class_id))

        # Atualizar rastreamentos existentes
        for obj_id, (centroid, age, hits) in list(self.centroids.items()):
            if age > self.max_age:
                del self.centroids[obj_id]
                if obj_id in self.track_history:
                    del self.track_history[obj_id]
                continue
            
            self.centroids[obj_id] = (centroid, age + 1, hits)

        # Associar novas detecções
        assigned_ids = []
        for centroid, box, confidence, class_id in new_centroids:
            matched_id = None
            min_dist = float('inf')
            
            for obj_id, (existing_centroid, age, hits) in self.centroids.items():
                dist = np.sqrt((centroid[0] - existing_centroid[0])**2 + 
                             (centroid[1] - existing_centroid[1])**2)
                if dist < self.max_distance and dist < min_dist:
                    min_dist = dist
                    matched_id = obj_id

            if matched_id is None:
                matched_id = self.next_id
                self.centroids[matched_id] = (centroid, 0, 1)
                self.track_history[matched_id] = [centroid]
                self.next_id += 1
            else:
                _, age, hits = self.centroids[matched_id]
                self.centroids[matched_id] = (centroid, age, hits + 1)
                self.track_history[matched_id].append(centroid)

            # Manter histórico limitado
            if len(self.track_history[matched_id]) > 30:
                self.track_history[matched_id] = self.track_history[matched_id][-30:]

            assigned_ids.append((matched_id, box, confidence, class_id))

            # Salvar frame se necessário
            if model_config["tracking"]["enabled"] and hits >= self.min_hits:
                self._save_detection(frame, box, matched_id, class_id, confidence, 
                                  stream_id, output_dir, model_config)

        return assigned_ids

    def _save_detection(self, frame, box, track_id, class_id, confidence, 
                       stream_id, output_dir, model_config):
        try:
            # Preparar frame anotado
            annotated_frame = frame.copy()
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            
            # Desenhar bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Adicionar informações
            label = f"{YOLO_CLASSES[class_id]} {track_id} ({confidence:.2f})"
            cv2.putText(annotated_frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Desenhar histórico de rastreamento
            if track_id in self.track_history:
                history = self.track_history[track_id]
                for i in range(1, len(history)):
                    cv2.line(annotated_frame, 
                            (int(history[i-1][0]), int(history[i-1][1])),
                            (int(history[i][0]), int(history[i][1])),
                            (0, 255, 0), 2)
            
            # Salvar frame
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            frame_filename = os.path.join(
                output_dir, 
                f"{YOLO_CLASSES[class_id]}_{stream_id}_{track_id}_{timestamp}.jpg"
            )
            cv2.imwrite(frame_filename, annotated_frame)
            
            # Registrar detecção
            detection_info = {
                "object_id": track_id,
                "class_id": class_id,
                "class_name": YOLO_CLASSES[class_id],
                "confidence": float(confidence),
                "bbox": [int(x) for x in box.xyxy[0].cpu().numpy()],
                "centroid": [float(x) for x in self.centroids[track_id][0]],
                "timestamp": datetime.now().isoformat(),
                "track_id": track_id,
                "track_history": [[float(x), float(y)] for x, y in self.track_history[track_id]],
                "saved_frame": frame_filename
            }
            
            # Adicionar dados de análise se disponível
            if model_config["analysis"]["enabled"]:
                detection_info["analysis_data"] = self._analyze_detection(
                    detection_info, model_config["analysis"]
                )
            
            self.detections.append(detection_info)
            logging.info(f"[Stream {stream_id}] {YOLO_CLASSES[class_id]} ID {track_id} detectado e salvo")
            
        except Exception as e:
            logging.error(f"Erro ao salvar detecção: {e}")

    def _analyze_detection(self, detection_info: dict, analysis_config: dict) -> dict:
        """Realiza análise específica baseada na configuração."""
        analysis_data = {}
        
        if analysis_config["type"] == "crowd":
            # Análise de multidão
            analysis_data["crowd_density"] = self._calculate_crowd_density()
            analysis_data["movement_pattern"] = self._analyze_movement_pattern(
                detection_info["track_history"]
            )
        
        elif analysis_config["type"] == "queue":
            # Análise de fila
            analysis_data["queue_length"] = self._calculate_queue_length()
            analysis_data["wait_time"] = self._estimate_wait_time(
                detection_info["track_id"]
            )
        
        elif analysis_config["type"] == "behavior":
            # Análise de comportamento
            analysis_data["behavior_type"] = self._classify_behavior(
                detection_info["track_history"]
            )
            analysis_data["suspicious_score"] = self._calculate_suspicious_score(
                detection_info
            )
        
        return analysis_data

    def _calculate_crowd_density(self) -> float:
        """Calcula a densidade da multidão."""
        # Implementar lógica de cálculo de densidade
        return 0.0

    def _analyze_movement_pattern(self, track_history: List[List[float]]) -> str:
        """Analisa o padrão de movimento."""
        # Implementar lógica de análise de movimento
        return "unknown"

    def _calculate_queue_length(self) -> int:
        """Calcula o comprimento da fila."""
        # Implementar lógica de cálculo de fila
        return 0

    def _estimate_wait_time(self, track_id: int) -> float:
        """Estima o tempo de espera."""
        # Implementar lógica de estimativa de tempo
        return 0.0

    def _classify_behavior(self, track_history: List[List[float]]) -> str:
        """Classifica o comportamento."""
        # Implementar lógica de classificação
        return "normal"

    def _calculate_suspicious_score(self, detection_info: dict) -> float:
        """Calcula score de comportamento suspeito."""
        # Implementar lógica de cálculo de score
        return 0.0

class ModelManager:
    def __init__(self):
        self.models = {}
        self.model_locks = {}
    
    def get_model(self, model_name: str):
        if model_name not in self.models:
            with threading.Lock():
                if model_name not in self.models:  # Double-check locking
                    try:
                        self.models[model_name] = YOLO(model_name)
                        self.model_locks[model_name] = threading.Lock()
                        logging.info(f"Modelo {model_name} carregado com sucesso")
                    except Exception as e:
                        logging.error(f"Erro ao carregar modelo {model_name}: {e}")
                        raise e
        return self.models[model_name], self.model_locks[model_name]

def process_stream_api(stream_config: StreamConfig, task_id: str):
    """Processa um stream RTSP para a API."""
    stream_id = stream_config.stream_id
    rtsp_url = stream_config.url
    output_dir = stream_config.output_dir or f"./detections/{stream_id}"
    model_config = stream_config.model_config
    rtsp_config = stream_config.rtsp_config
    save_config = model_config.get("save_config", {
        "save_all_frames": False,
        "save_detections": True,
        "save_events": True,
        "max_frames_per_day": 1000,
        "compression_quality": 85,
        "max_storage_days": 7
    })
    
    # Criar estrutura de diretórios
    dirs = {
        "frames": os.path.join(output_dir, "frames"),
        "events": os.path.join(output_dir, "events"),
        "logs": os.path.join(output_dir, "logs"),
        "temp": os.path.join(output_dir, "temp")
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    # Inicializar contadores e métricas
    frame_count = 0
    daily_frame_count = 0
    last_day = datetime.now().date()
    start_time = time.time()
    
    # Inicializar status do stream
    active_streams[stream_id] = {
        "status": "connecting",
        "detections": {YOLO_CLASSES[i]: 0 for i in model_config["classes"]},
        "last_detection": None,
        "task_id": task_id,
        "model_config": model_config,
        "rtsp_config": rtsp_config,
        "analysis_status": None,
        "performance_metrics": {
            "fps": 0,
            "processing_time": 0,
            "detection_count": 0,
            "daily_frames_saved": 0
        }
    }
    
    # Configurar OpenCV com parâmetros RTSP
    rtsp_options = f"rtsp_transport;tcp|timeout;{rtsp_config['timeout']}|buffer_size;{rtsp_config['buffer_size']}"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = rtsp_options
    
    # Obter modelo específico para este stream
    model, model_lock = model_manager.get_model(model_config["model_name"])
    
    # Inicializar tracker
    tracker = CentroidTracker(model_config["tracking"])
    
    reconnect_count = 0
    
    while reconnect_count < rtsp_config["reconnect_attempts"]:
        try:
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            if not cap.isOpened():
                raise Exception(f"Falha ao conectar ao stream: {rtsp_url}")
            
            active_streams[stream_id]["status"] = "running"
            logging.info(f"[Stream {stream_id}] Conectado com sucesso!")
            
            while active_streams.get(stream_id, {}).get("status") == "running":
                ret, frame = cap.read()
                if not ret:
                    logging.warning(f"[Stream {stream_id}] Falha ao capturar frame")
                    time.sleep(1)
                    continue
                
                frame_count += 1
                
                # Verificar limite diário de frames
                current_day = datetime.now().date()
                if current_day != last_day:
                    daily_frame_count = 0
                    last_day = current_day
                
                if daily_frame_count >= save_config["max_frames_per_day"]:
                    logging.warning(f"[Stream {stream_id}] Limite diário de frames atingido")
                    time.sleep(1)
                    continue
                
                if frame_count % model_config["process_every_n_frames"] != 0:
                    continue
                
                # Redimensionar frame se necessário
                if frame.shape[1] > model_config["img_size"]:
                    scale = model_config["img_size"] / frame.shape[1]
                    frame = cv2.resize(frame, None, fx=scale, fy=scale)
                
                # Processar frame
                process_start = time.time()
                with model_lock:
                    results = model(
                        frame,
                        conf=model_config["conf_threshold"],
                        classes=model_config["classes"]
                    )
                
                # Atualizar tracker e processar detecções
                detections_saved = False
                for result in results:
                    if result.boxes is not None and len(result.boxes) > 0:
                        detections = tracker.update(
                            result.boxes, frame, dirs["frames"], stream_id, model_config
                        )
                        
                        if detections and save_config["save_detections"]:
                            detections_saved = True
                            daily_frame_count += 1
                            active_streams[stream_id]["performance_metrics"]["daily_frames_saved"] = daily_frame_count
                        
                        # Atualizar contadores
                        for _, box, conf, class_id in detections:
                            class_name = YOLO_CLASSES[class_id]
                            active_streams[stream_id]["detections"][class_name] += 1
                            active_streams[stream_id]["last_detection"] = datetime.now().isoformat()
                
                # Salvar frame se necessário
                if save_config["save_all_frames"] and not detections_saved:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    frame_filename = os.path.join(
                        dirs["frames"],
                        f"frame_{stream_id}_{timestamp}.jpg"
                    )
                    cv2.imwrite(
                        frame_filename,
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, save_config["compression_quality"]]
                    )
                    daily_frame_count += 1
                
                # Atualizar métricas de performance
                process_time = time.time() - process_start
                fps = 1 / process_time if process_time > 0 else 0
                
                active_streams[stream_id]["performance_metrics"].update({
                    "fps": fps,
                    "processing_time": process_time,
                    "detection_count": frame_count
                })
                
                # Atualizar status de análise se necessário
                if model_config["analysis"]["enabled"]:
                    active_streams[stream_id]["analysis_status"] = tracker._analyze_detection(
                        {"track_history": tracker.track_history},
                        model_config["analysis"]
                    )
                
                time.sleep(0.1)  # Controlar taxa de processamento
            
            break  # Sair do loop de reconexão se o stream foi parado normalmente
            
        except Exception as e:
            logging.error(f"[Stream {stream_id}] Erro durante processamento: {e}")
            reconnect_count += 1
            
            if reconnect_count < rtsp_config["reconnect_attempts"]:
                logging.info(f"[Stream {stream_id}] Tentando reconectar em {rtsp_config['reconnect_delay']} segundos...")
                time.sleep(rtsp_config["reconnect_delay"])
            else:
                active_streams[stream_id]["status"] = "error"
                logging.error(f"[Stream {stream_id}] Número máximo de tentativas de reconexão atingido")
        
        finally:
            if 'cap' in locals():
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
    if not model_manager:
        raise HTTPException(status_code=500, detail="API não iniciada")
    
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
            detections=info["detections"],
            last_detection=info.get("last_detection"),
            analysis_status=info.get("analysis_status"),
            performance_metrics=info["performance_metrics"]
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
        detections=info["detections"],
        last_detection=info.get("last_detection"),
        analysis_status=info.get("analysis_status"),
        performance_metrics=info["performance_metrics"]
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
