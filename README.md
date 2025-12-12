# 🛡️ KernelGuard: Real-Time System Health Monitor

![React](https://img.shields.io/badge/Frontend-React_18-blue?logo=react)
![Python](https://img.shields.io/badge/Backend-FastAPI-green?logo=fastapi)
![Socket.IO](https://img.shields.io/badge/RealTime-WebSockets-orange?logo=socket.io)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> **A full-stack diagnostic suite that visualizes kernel-level metrics, hardware performance, and system anomalies in real-time using asynchronous WebSockets.**

---

## 🎥 Project Demo
*[Insert your demo video link here]*

---

## 📖 Overview
**KernelGuard** is designed to provide granular visibility into a machine's performance. Unlike standard task managers, this application focuses on **kernel latency (DPCs)**, **interrupt handling**, and **hardware safety**, helping users diagnose overheating or system stalls before they cause crashes.

The system uses a **Client-Server architecture** where a Python-based kernel agent streams data to a React dashboard with sub-millisecond latency.

## 🚀 Key Features

### 1. Real-Time Telemetry Streaming
* **What it does:** Streams CPU, GPU, and Memory data every 2 seconds without page refreshes.
* **The Tech:** Powered by **Socket.IO (WebSockets)**, enabling bi-directional, persistent communication between the Python backend and React frontend.

### 2. Kernel-Level Diagnostics
* **What it does:** Tracks low-level OS metrics including **Context Switches**, **System Interrupts**, and **DPC (Deferred Procedure Call) Latency**.
* **The Tech:** Utilizes Python's `psutil` library to interface directly with operating system counters.

### 3. Intelligent Threat Analysis
* **What it does:** Automatically flags system anomalies (e.g., "CPU Overheating" or "Kernel Stalls") and triggers visual alerts (Red/Yellow states).
* **The Tech:** A custom Python analysis engine (`analyzer.py`) evaluates incoming data streams against safety thresholds before broadcasting.

### 4. Interactive Data Visualization
* **What it does:** Renders live, moving area charts for hardware usage trends over time.
* **The Tech:** Built with **Recharts**, utilizing SVG-based rendering for high-performance graphing that doesn't bog down the browser.

### 5. Secure Session Management
* **What it does:** Prevents unauthorized access to the monitoring dashboard.
* **The Tech:** Implements **JWT (JSON Web Token)** authentication with secure password hashing (`bcrypt`) via FastAPI.

---

## 🛠️ Technical Architecture

### 🖥️ Frontend (The Dashboard)
* **React.js:** Used for its component-based architecture, allowing the "Metric Cards" and "Graphs" to update independently.
* **Tailwind CSS:** Employed for a responsive, "Hacker-style" UI with a robust **Dark/Light Mode** engine.
* **Lucide React:** Provides lightweight, vector-based iconography for system status indicators.

### ⚙️ Backend (The Engine)
* **FastAPI:** Chosen for its asynchronous capabilities (`async`/`await`), essential for handling WebSocket connections without blocking the main thread.
* **GPUtil:** Interfaces with NVIDIA/AMD drivers to fetch GPU temperature and load.
* **SQLite:** A lightweight, serverless database used to store user credentials and session history logs.

---

## ⚡ Installation & Setup

Follow these steps to deploy KernelGuard on your local machine.

### Prerequisites
* Python 3.8+
* Node.js & npm

### 1. Clone the Repository
```bash
git clone [https://github.com/tejas-nama/kernal-health-manager.git](https://github.com/tejas-nama/kernal-health-manager.git)
cd kernal-health-manager
