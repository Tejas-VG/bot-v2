# Deployment Guide: Google Cloud (GCP) e2-micro VM

This guide explains how to deploy your Rasa chatbot backend (Rasa Server + Custom Action Server) to a **Google Cloud Platform (GCP) e2-micro Virtual Machine** for free.

---

## Step 1: Create your GCP Free VM

Google Cloud offers an **e2-micro** instance that is free forever, provided you launch it in one of these three US regions:
* `us-central1` (Iowa)
* `us-east1` (South Carolina)
* `us-west1` (Oregon)

### Setup Steps:
1. Log in to the [Google Cloud Console](https://console.cloud.google.com/).
2. Go to **Compute Engine** > **VM Instances** and click **Create Instance**.
3. Configure the VM:
   * **Name**: `rasa-bot`
   * **Region**: Choose `us-central1`, `us-east1`, or `us-west1`.
   * **Machine type**: Select **e2-micro** (under the General-purpose family).
   * **Boot disk**: Change the OS to **Ubuntu 22.04 LTS** (Standard persistent disk, up to 30 GB is free).
   * **Firewall**: Check both **Allow HTTP traffic** and **Allow HTTPS traffic**.
4. Click **Create** to launch your VM.

---

## Step 2: Configure GCP Firewall Rules (Allow Port 5005)

By default, GCP blocks incoming traffic on port `5005` (the port Rasa uses to communicate with your frontend web chat).

1. Search for **VPC network** in the Google Cloud console search bar and go to **Firewall**.
2. Click **Create Firewall Rule**:
   * **Name**: `allow-rasa`
   * **Targets**: Select `All instances in the network`
   * **Source IPv4 ranges**: `0.0.0.0/0` (Allows traffic from anywhere)
   * **Protocols and ports**: Check `Specified protocols and ports`, check `TCP`, and enter `5005`.
3. Click **Create**.

---

## Step 3: Connect to the VM and Install Docker

1. In the Compute Engine VM Instances list, find your VM and click the **SSH** button next to it. A terminal window will open in your browser.
2. Update the package list:
   ```bash
   sudo apt-get update
   ```
3. Install Docker:
   ```bash
   sudo apt-get install -y docker.io
   sudo systemctl start docker
   sudo systemctl enable docker
   ```
4. Install Docker Compose:
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```
5. Add your user to the docker group so you don't need `sudo` to run docker commands:
   ```bash
   sudo usermod -aG docker $USER
   ```
   *(Log out of the SSH session and connect again to apply this group change.)*

---

## Step 4: Clone the Repo and Deploy

1. Clone your repository onto the VM:
   ```bash
   git clone https://github.com/Tejas-VG/bot-v2.git
   cd bot-v2
   ```
2. Run Docker Compose to build and start both the Rasa server and the Action server in the background:
   ```bash
   docker-compose up -d
   ```
3. Check if the containers are running:
   ```bash
   docker ps
   ```
   *You should see `rasa-server` running on port `5005` and `action-server` running on port `5055`.*

4. To view logs and troubleshoot:
   ```bash
   docker-compose logs -f
   ```

---

## Step 5: Connect your Web UI (Frontend)

1. Find the **External IP** (Public IP) of your VM on the GCP Compute Engine dashboard (e.g. `34.123.45.67`).
2. Open your frontend `index.html` file.
3. Update the `socketUrl` or `data-websocket-url` to point to your VM's public IP:
   ```javascript
   socketUrl: "http://<YOUR_VM_EXTERNAL_IP>:5005/",
   ```
4. Save and deploy your frontend (e.g. to **Vercel** or double-click to run locally). Your frontend will now connect to the live backend running on Google Cloud!
