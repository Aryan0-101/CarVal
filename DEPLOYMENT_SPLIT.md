# Split Deployment: Cloudflare Pages + AWS

This guide will show you how to host the Frontend on Cloudflare Pages (for free and incredibly fast global delivery) and the Python Backend on AWS.

## Step 1: Deploy Backend to AWS
1. **Launch an EC2 Instance:** Spin up a `t2.micro` or `t3.micro` Ubuntu instance on AWS (eligible for the free tier).
2. **Open Port 8000:** In your AWS Security Group settings, add an Inbound Rule allowing **Custom TCP on port 8000** from anywhere (`0.0.0.0/0`).
3. **SSH into your EC2:**
   ```bash
   ssh -i your-key.pem ubuntu@YOUR_AWS_IP
   ```
4. **Install Docker:**
   ```bash
   sudo apt update
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```
5. **Clone and Run Backend:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/car_price_pred.git
   cd car_price_pred
   
   # We use the special backend-only compose file
   sudo docker compose -f docker-compose.backend.yml up -d --build
   ```
6. Verify your backend is running by going to `http://YOUR_AWS_IP:8000/` in your browser. Note this IP address for Step 2.

---

## Step 2: Deploy Frontend to Cloudflare Pages
1. Go to your [Cloudflare Dashboard](https://dash.cloudflare.com/) -> **Workers & Pages**.
2. Click **Create** -> **Pages** -> **Connect to Git**.
3. Select your `car_price_pred` repository.
4. **Configure the Build Settings:**
   - **Framework Preset:** `Vite` (or None)
   - **Build Command:** `cd frontend && npm run build`
   - **Build Output Directory:** `frontend/dist`
5. **Crucial Step: Add Environment Variable:**
   - Scroll down to "Environment Variables (Advanced)"
   - Add a new variable:
     - Variable name: `VITE_API_URL`
     - Value: `http://YOUR_AWS_IP:8000` (Replace with your actual AWS IP from Step 1).
6. Click **Save and Deploy**.

Cloudflare will build your frontend, inject the AWS backend URL into the code, and give you a free `your-app.pages.dev` domain with SSL!

---
*Note: Because your backend is running on `http` (AWS IP) rather than `https`, some strict browsers might block the connection due to "Mixed Content" (loading insecure data on a secure site). For a production launch, you'll eventually want to point a subdomain to your AWS IP and add a free SSL certificate to your AWS server using Let's Encrypt.*
