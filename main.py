from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

import time
import cv2
import json

from camera_manager import CameraManager

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# camera = CameraManager(device_index=0, width=4096, height=2160, fourcc="MJPG")
camera = CameraManager(device_index=0, width=1920, height=1080, fourcc="YUYV")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/control")
async def ws_control(ws: WebSocket):
    await ws.accept()
    print("[WS] client connected")
    try:
        while True:
            msg_text = await ws.receive_text()
            print(f"[WS] received:{msg_text}")

            try:
                msg = json.loads(msg_text)
            except json.JSONDecodeError:
                await ws.send_json(
                    {"type": "error", "error": "invalid_json", "raw": msg_text}
                )
                continue

            msg_type = msg.get("type")
            try:
                if msg_type == "camera_start":
                    camera.start()
                    await ws.send_json({"type": "ack", "action": "camera_start"})
                    continue

                if msg_type == "camera_stop":
                    camera.stop()
                    await ws.send_json({"type": "ack", "action": "camera_stop"})
                    continue

                if msg_type == "set_white_balance_temperature":
                    value = msg.get("value")
                    if value is None:
                        await ws.send_json(
                            {
                                "type": "error",
                                "error": "missing_value",
                                "for": "set_white_balance_temperature",
                            }
                        )
                        continue
                    result = camera.set_white_balance_temperature(float(value))
                    await ws.send_json(
                        {
                            "type": "ack",
                            "action": "set_white_balance_temperature",
                            "result": result,
                        }
                    )
                    continue

                if msg_type == "set_exposure":
                    value = msg.get("value")
                    if value is None:
                        await ws.send_json(
                            {
                                "type": "error",
                                "error": "missing_value",
                                "for": "set_exposure",
                            }
                        )
                        continue
                    result = camera.set_exposure(float(value))
                    await ws.send_json(
                        {"type": "ack", "action": "set_exposure", "result": result}
                    )
                    continue

                if msg_type == "set_gain":
                    value = msg.get("value")
                    if value is None:
                        await ws.send_json(
                            {
                                "type": "error",
                                "error": "missing_value",
                                "for": "set_gain",
                            }
                        )
                        continue
                    result = camera.set_gain(float(value))
                    await ws.send_json(
                        {"type": "ack", "action": "set_gain", "result": result}
                    )
                    continue

                if msg_type == "set_focus":
                    value = msg.get("value")
                    if value is None:
                        await ws.send_json(
                            {
                                "type": "error",
                                "error": "missing_value",
                                "for": "set_focus",
                            }
                        )
                        continue
                    result = camera.set_focus(float(value))
                    await ws.send_json(
                        {"type": "ack", "action": "set_focus", "result": result}
                    )
                    continue

                if msg_type == "set_zoom":
                    value = msg.get("value")
                    if value is None:
                        await ws.send_json(
                            {
                                "type": "error",
                                "error": "missing_value",
                                "for": "set_zoom",
                            }
                        )
                        continue
                    result = camera.set_zoom(float(value))
                    await ws.send_json(
                        {"type": "ack", "action": "set_zoom", "result": result}
                    )
                    continue

                await ws.send_json(
                    {"type": "error", "error": "unknown_type", "msg_type": msg_type}
                )

            except Exception as e:
                await ws.send_json(
                    {
                        "type": "error",
                        "error": "exception",
                        "msg_type": msg_type,
                        "detail": str(e),
                    }
                )
    except WebSocketDisconnect:
        print("[WS] client disconnected")
    finally:
        camera.stop()


@app.get("/mjpeg")
def mjpeg():
    # WS start/stop만 사용: 여기서는 카메라를 자동으로 켜지지 않음(보기 전용)
    with camera.lock:
        running = camera.running
    if not running:
        raise HTTPException(
            status_code=503, detail="Camera is not started. Use WS camera_start first."
        )
    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


def mjpeg_generator():
    boundary = b"--frame\r\n"
    while True:
        # "보기만" 모드: 캡처가 꺼지면 스트림도 종료
        with camera.lock:
            running = camera.running
            frame = camera.last_frame

        if not running:
            break

        if frame is None:
            time.sleep(0.02)
            continue

        ok, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        if not ok:
            continue

        jpg_bytes = jpg.tobytes()

        yield boundary
        yield b"Content-Type: image/jpeg\r\n"
        yield f"Content-Length: {len(jpg_bytes)}\r\n\r\n".encode("utf-8")
        yield jpg_bytes
        yield b"\r\n"
