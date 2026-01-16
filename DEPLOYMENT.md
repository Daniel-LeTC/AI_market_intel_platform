# RnD Scout Deployment Guide
*From Localhost to VPS (Production Ready)*

## Prerequisites
1.  A Linux VPS (Ubuntu 22.04/24.04 recommended).
2.  Docker & Docker Compose installed on VPS.
3.  SSH Access to the VPS.

---

## Strategy: The "Hybrid Transfer"
We do NOT commit secrets (`.env`) or heavy data (`.duckdb`, `staging_data/`) to Git.
*   **Code:** Transfer via **Git**.
*   **Secrets:** Create manually or **SCP**.
*   **Data:** Transfer via **Rsync**.

---

## Step 1: Code Setup (On VPS)
1.  SSH into your VPS:
    ```bash
    ssh user@your-vps-ip
    ```
2.  Clone the repository:
    ```bash
    git clone https://github.com/your-repo/bright_scraper_tool.git
    cd bright_scraper_tool
    ```

---

## Step 2: Secrets (The .env file)
**Option A: Create Manually (Secure)**
```bash
nano .env
# Paste your API Keys here
```

**Option B: Upload from Local (Fast)**
From your *Local Machine*:
```bash
scp .env user@your-vps-ip:/path/to/bright_scraper_tool/.env
```

---

## Step 3: Data Migration (The Database)
Since DuckDB is a file, we just copy it over.
**Use `rsync` instead of `scp`** (It compresses data and can resume if connection drops).

From your *Local Machine*:
```bash
# 1. Sync the Database file
rsync -avz --progress scout.duckdb user@your-vps-ip:/path/to/bright_scraper_tool/

# 2. Sync the raw/staging data folders (Optional but recommended)
rsync -avz --progress staging_data/ user@your-vps-ip:/path/to/bright_scraper_tool/staging_data/
```

*Note: Make sure no process is writing to the DB on Local when you copy.*

---

## Step 4: Launch via Docker
On the *VPS*:
```bash
# Build and Run in background
docker-compose up --build -d
```

### Verification
1.  Check containers: `docker ps`
2.  View Logs: `docker-compose logs -f`
3.  Access UI: `http://your-vps-ip:8501`

---

## Updating / Maintenance
When you change code locally:
1.  **Local:** `git push`
2.  **VPS:**
    ```bash
    git pull
    docker-compose up --build -d  # Rebuilds containers with new code
    ```

When you want to download the Production DB to analyze locally:
```bash
# From Local Machine
rsync -avz --progress user@your-vps-ip:/path/to/bright_scraper_tool/scout.duckdb ./scout_prod_backup.duckdb
```
