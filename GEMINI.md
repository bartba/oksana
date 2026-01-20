# Project Context: Durak Camera Control

## Project Overview

This project is a **FastAPI-based web application** designed to control and stream video from a USB camera. It provides a real-time MJPEG video stream and allows users to adjust various camera parameters dynamically via a WebSocket connection.

**Key Features:**
*   **Real-time Streaming:** MJPEG video feed accessible via a web browser.
*   **Camera Control:** Start/Stop functionality.
*   **Parameter Adjustment:** Fine-tune camera settings including:
    *   Exposure
    *   Gain
    *   Focus
    *   Zoom
    *   White Balance Temperature

**Architecture:**
*   **Backend:** Python (FastAPI) handles HTTP requests and WebSocket connections.
*   **Camera Interface:** `opencv-python` (cv2) manages the physical camera device in a separate thread (`CameraManager`).
*   **Frontend:** A single-page HTML/JS interface (`templates/index.html`) for viewing the stream and controlling settings.

## Building and Running

### Prerequisites
*   Python 3.10+
*   A connected USB Camera (default index `0`)
*   Linux environment (based on file paths)

### Setup & Execution

1.  **Activate the Virtual Environment:**
    ```bash
    source .venv/bin/activate
    ```

2.  **Run the Application:**
    Use `uvicorn` to start the server.
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

3.  **Access the Interface:**
    Open a web browser and navigate to `http://localhost:8000` (or the server's IP address).

## Development Conventions

### Code Structure
*   **`main.py`**: The application entry point. Defines the FastAPI app, WebSocket endpoints, and MJPEG streaming route.
*   **`camera_manager.py`**: Encapsulates camera logic.
    *   Uses a dedicated thread for frame capturing to ensure non-blocking operation.
    *   Provides thread-safe access to the latest frame and camera properties using `threading.Lock`.
    *   *Note:* Contains Korean comments documenting the threading and locking mechanisms.
*   **`templates/index.html`**: The frontend UI. Implements WebSocket communication (`ws://.../ws/control`) and updates the MJPEG stream source.

### Dependencies
Inferred from usage and environment:
*   `fastapi`
*   `uvicorn`
*   `opencv-python`
*   `jinja2`
*   `websockets`

### Style
*   Follows standard Python PEP 8 conventions.
*   Type hinting is used in `main.py` and `camera_manager.py`.
