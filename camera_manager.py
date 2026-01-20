import threading
import time
import cv2


class CameraManager:
    """
    - 별도 스레드에서 USB 카메라 프레임을 지속적으로 읽어 last_frame에 최신 프레임을 저장합니다.
    - 다른 스레드(StreamingResponse generator 등)에서 last_frame을 안전하게 읽을 수 있도록 lock을 제공합니다.
    """

    def __init__(
        self,
        device_index: int = 0,
        width: int = 1920,  # 4096,
        height: int = 1080,  # 2160,
        prefer_backend: int = cv2.CAP_V4L2,
        fourcc: str = "YUYV",  # "MJPG",
    ):
        self.cap = None
        self.lock = threading.Lock()
        self.running = False
        self.last_frame = None
        self.thread = None

        self.device_index = device_index
        self.width = width
        self.height = height
        self.prefer_backend = prefer_backend
        self.fourcc = fourcc

    def start(self):
        """캡처 스레드를 시작합니다(이미 실행 중이면 무시)."""
        with self.lock:
            if self.running:
                return
            self.running = True

        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """캡처 스레드를 중단하고 카메라 리소스를 해제합니다."""
        with self.lock:
            self.running = False

        if self.thread:
            self.thread.join(timeout=1.0)

        with self.lock:
            if self.cap:
                try:
                    self.cap.release()
                except Exception:
                    pass
            self.cap = None
            self.last_frame = None

    def _open_camera(self):
        cap = cv2.VideoCapture(self.device_index, self.prefer_backend)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"Cannot open camera index={self.device_index}")

        # MJPG 수신 설정(카메라가 지원하면 성능에 유리할 때가 많음)
        if self.fourcc:
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.fourcc))

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        cap.set(cv2.CAP_PROP_AUTO_WB, 0)
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

        return cap

    def _capture_loop(self):
        try:
            cap = self._open_camera()
        except Exception as e:
            with self.lock:
                self.running = False
                self.cap = None
                self.last_frame = None
            print(f"[CAM] open failed: {e}")
            return

        with self.lock:
            self.cap = cap

        print("[CAM] capture started")

        while True:
            with self.lock:
                if not self.running:
                    break
                cap_ref = self.cap

            if cap_ref is None:
                break

            ok, frame = cap_ref.read()
            if not ok:
                time.sleep(0.01)
                continue

            with self.lock:
                self.last_frame = frame

        print("[CAM] capture stopping")
        with self.lock:
            try:
                if self.cap:
                    self.cap.release()
            except Exception:
                pass
            self.cap = None
            self.last_frame = None

    def _ensure_open(self):
        """cap이 열려있지 않으면 예외"""
        with self.lock:
            if self.cap is None or not self.cap.isOpened():
                raise RuntimeError("Camera is not started/opened")

    def set_white_balance_temperature(self, value: float) -> dict:
        """white balance temperature 설정"""
        self._ensure_open()
        with self.lock:
            ok = self.cap.set(23, float(value))
            readback = self.cap.get(23)
        return {"ok": bool(ok), "requested": value, "applied": readback}

    def set_exposure(self, value: float) -> dict:
        """
        exposure 설정.
        """
        self._ensure_open()
        with self.lock:
            ok = self.cap.set(cv2.CAP_PROP_EXPOSURE, float(value))
            readback = self.cap.get(cv2.CAP_PROP_EXPOSURE)
        return {"ok": ok, "requested": value, "applied": readback}

    def set_gain(self, value: float) -> dict:
        """gain 설정"""
        self._ensure_open()
        with self.lock:
            ok = self.cap.set(cv2.CAP_PROP_GAIN, float(value))
            readback = self.cap.get(cv2.CAP_PROP_GAIN)
        return {"ok": bool(ok), "requested": value, "applied": readback}

    def set_focus(self, value: float) -> dict:
        """
        focus 설정.
        """
        self._ensure_open()
        with self.lock:
            ok = self.cap.set(cv2.CAP_PROP_FOCUS, float(value))  # 0~255
            readback = self.cap.get(cv2.CAP_PROP_FOCUS)
        return {"ok": bool(ok), "requested": value, "applied": readback}

    def set_zoom(self, value: float) -> dict:
        """
        zoom 설정.
        """
        self._ensure_open()
        with self.lock:
            ok = self.cap.set(cv2.CAP_PROP_ZOOM, float(value))
            readback = self.cap.get(cv2.CAP_PROP_ZOOM)
        return {"ok": bool(ok), "requested": value, "applied": readback}

    def get_props(self) -> dict:
        """현재 주요 속성 readback(디버깅/표시용)"""
        self._ensure_open()
        with self.lock:
            return {
                "white_balance_auto": self.cap.get(cv2.CAP_PROP_AUTO_WB),
                "white_balance": self.cap.get(23),
                "auto_exposure": self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE),
                "exposure": self.cap.get(cv2.CAP_PROP_EXPOSURE),
                "gain": self.cap.get(cv2.CAP_PROP_GAIN),
                "autofocus": self.cap.get(cv2.CAP_PROP_AUTOFOCUS),
                "focus": self.cap.get(cv2.CAP_PROP_FOCUS),
                "zoom": self.cap.get(cv2.CAP_PROP_ZOOM),
                "width": self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                "height": self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
            }
