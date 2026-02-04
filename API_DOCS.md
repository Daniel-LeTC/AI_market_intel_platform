# RnD Scout Worker API Documentation
*The Gatekeeper Interface for Background Jobs*

## Overview
This API allows you to trigger long-running background tasks (Mining, Cleaning) asynchronously.
The server runs on **Port 8000** by default.

**Base URL:** `http://localhost:8000` (Local) or `http://<vps-ip>:8000` (Production)

---

## Endpoints

### 1. Health Check
Check if the worker service is alive.
*   **GET** `/`
*   **Response:**
    ```json
    {
      "status": "online",
      "role": "Gatekeeper Worker"
    }
    ```

### 2. Trigger Miner (AI Extraction)
Start the AI mining process for pending raw reviews.
*   **POST** `/trigger/miner`
*   **Query Parameters:**
    *   `limit` (int, optional): Number of reviews to process. Default: `100`.
*   **Example (cURL):**
    ```bash
    curl -X POST "http://localhost:8000/trigger/miner?limit=50"
    ```
*   **Response:**
    ```json
    {
      "status": "accepted",
      "job": "miner",
      "limit": 50
    }
    ```

### 3. Trigger Janitor (Data Cleaning)
Start the Normalization pipeline to clean raw tags.
*   **POST** `/trigger/janitor`
*   **Example (cURL):**
    ```bash
    curl -X POST "http://localhost:8000/trigger/janitor"
    ```
*   **Response:**
    ```json
    {
      "status": "accepted",
      "job": "janitor"
    }
    ```

---

## Integration Notes
*   **Asynchronous:** These endpoints return `202 Accepted` immediately. The actual work happens in the background. Check server logs (`docker logs scout_worker`) to see progress.
*   **Concurrency:** Do not trigger multiple jobs simultaneously if using SQLite/DuckDB to avoid write locks (though the system has retry logic, it's safer to wait).
