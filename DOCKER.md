# Docker Deployment Guide

This guide provides step-by-step instructions for running the **eCTD PDF Validator** using Docker, both on your local machine and on a live server (like AWS EC2 Ubuntu).

---

## 🚀 1. Run Locally (Mac/Windows/Linux)

### Prerequisites

- Install **Docker Desktop** for your OS.

### Start the Application

Open your terminal in the project directory and run:

```bash
docker-compose up -d --build
```

- This builds the image and starts the container in the background.
- The app will be running at: `http://localhost:8000/health`

### Stop the Application

To stop and remove the containers:

```bash
docker-compose down
```

### View Logs

To see the output/logs of the running application:

```bash
docker-compose logs -f
```

---

## ☁️ 2. Deploy on AWS EC2 (Ubuntu)

### Prerequisites

- An AWS EC2 instance (Ubuntu 22.04 or 24.04 recommended).
- **Security Group Rules**: Ensure **Port 8000** (Custom TCP) is open in your Security Group (Inbound Rules) so you can access the API.

### Step 1: Connect to your Server

SSH into your instance:

```bash
ssh -i "your-key.pem" ubuntu@your-ec2-ip-address
```

### Step 2: Install Docker & Git

Run these commands to verify updates and install Docker + Compose:

```bash
# Update package list
sudo apt-get update

# Install Docker, Compose, and Git
sudo apt-get install -y docker.io docker-compose-v2 git

# Add your user to the docker group (optional, avoids using sudo for every command)
sudo usermod -aG docker $USER
# NOTE: You need to log out and log back in for the group change to take effect.
# For this guide, we will use 'sudo' just to be safe.
```

### Step 3: Clone the Repository

Clone your project code from GitHub:

```bash
git clone https://github.com/SandipKurmi/ectd-pdf-validator.git
cd ectd-pdf-validator
```

### Step 4: Run the Application

Start the application using Docker Compose.

_Note: On newer Docker versions, the command is `docker compose` (space). On older ones, it's `docker-compose` (dash)._

```bash
# Try the newer command first
sudo docker compose up -d --build

# OR if that says 'command not found', use the older one:
sudo docker-compose up -d --build
```

### Step 5: Verify Deployment

Your app should now be live!
Visit: `http://<your-ec2-public-ip>:8000/health`

---

## 🛠 Useful Commands Cheat Sheet

| Action            | Command                             |
| :---------------- | :---------------------------------- |
| **Start/Rebuild** | `sudo docker compose up -d --build` |
| **Stop**          | `sudo docker compose down`          |
| **View Logs**     | `sudo docker compose logs -f`       |
| **Restart**       | `sudo docker compose restart`       |
| **Pull New Code** | `git pull origin main`              |

### Updating the Live App

When you make changes to your code and want to update the server:

1.  SSH into the server.
2.  Go to the directory: `cd ectd-pdf-validator`
3.  Pull changes: `git pull origin main`
4.  Rebuild and restart: `sudo docker compose up -d --build`
