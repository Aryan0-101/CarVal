# Deployment Guide: Precision Valuation Engine

This guide walks you through deploying your full-stack Dockerized application (Frontend + FastAPI Backend + SQLite + Machine Learning Pipeline) to a standard cloud Virtual Machine (such as AWS EC2, DigitalOcean Droplet, or Google Cloud VM).

## Prerequisites
Before you start, ensure you have:
1. Created an account on a Cloud Provider (e.g., AWS, DigitalOcean, Linode).
2. Pushed your codebase to a Git repository (like GitHub or GitLab).

---

## Step 1: Provision a Server (VM)
1. **Launch a VM**: Create a new Linux instance (Ubuntu 22.04 LTS is highly recommended).
2. **Sizing**: Because the ML model requires some memory to load into RAM, choose an instance with **at least 2GB of RAM** (e.g., a $12/mo DigitalOcean droplet or AWS t3.small).
3. **Network/Security**: Open the following ports in your firewall settings:
   - Port `22` (SSH for access)
   - Port `80` (HTTP for the frontend)
   - Port `8001` (If you want to expose the backend directly, though in production you typically route this through Nginx).

## Step 2: SSH into your Server
Connect to your new server via your terminal:
```bash
ssh root@YOUR_SERVER_IP
```

## Step 3: Install Docker & Git
Once inside the server, run the following commands to install the required tools:
```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install Git
sudo apt install git -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin -y
```

## Step 4: Clone Your Project
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/car_price_pred.git

# Enter the directory
cd car_price_pred
```

## Step 5: Configure Port Mappings (Optional)
Currently, our `docker-compose.yml` exposes the frontend on port `80` and the backend on port `8001`. 
If you want the frontend accessible instantly over the web without typing a port, ensure `docker-compose.yml` maps the frontend to `80:80`. *(Note: Our current setup already maps the Nginx frontend to port 80).*

Additionally, in `frontend/main.js` and `frontend/evaluation.html`, you are currently fetching `http://localhost:8001`. Before pushing to production, change `localhost` in those files to your actual server's IP address (e.g., `http://198.51.100.23:8001`), or set up a reverse proxy.

## Step 6: Build and Launch
Run the entire stack in detached mode:
```bash
sudo docker compose up -d --build
```
*Note: This will take a few minutes as it downloads the Python and Node environments and installs dependencies.*

## Step 7: Verify Deployment
1. **Frontend:** Open your web browser and navigate to `http://YOUR_SERVER_IP`. You should see the sleek Hero section and animation.
2. **Backend API:** Navigate to `http://YOUR_SERVER_IP:8001/`. You should see `{"status": "running", "model_loaded": true}`.

---

## 🔒 Production Enhancements (Next Steps)
To make this enterprise-ready:
1. **Domain Name & SSL:** Point a domain name to your server's IP and use **Certbot (Let's Encrypt)** to generate a free HTTPS SSL certificate.
2. **Reverse Proxy:** Instead of exposing port 8001 directly, configure Nginx to route `/api/` traffic internally to the backend container.
3. **Persistent Volumes:** Since you use SQLite, ensure the database volume is safely mapped to the host machine so data isn't lost when containers restart. (Our `docker-compose.yml` already maps `./backend:/app` which protects the `history.db`!).
