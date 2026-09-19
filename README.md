# Sliding Window Protocol Simulator

A Python-based graphical simulator for demonstrating the **Sliding Window Protocol** using **Go-Back-N** and **Selective Repeat**.

This project is developed as a mini project for the **Data Communication and Networking** course.

---

## 📌 Project Overview

The Sliding Window Protocol is a data-link layer mechanism that allows multiple frames to be transmitted before receiving acknowledgements.

This simulator provides a graphical demonstration of:

- Go-Back-N (GBN)
- Selective Repeat (SR)
- Sender and Receiver communication
- Sliding transmission windows
- Data packet loss
- ACK loss
- Timeout and retransmission
- Frame-by-frame protocol events

The simulator is designed to make the working of these protocols easier to understand and demonstrate.

---

## ✨ Features

- Graphical user interface using Tkinter
- Go-Back-N simulation
- Selective Repeat simulation
- Configurable number of frames
- Configurable window size
- Configurable packet loss
- Configurable ACK loss
- Slow, Normal and Fast animation speeds
- Sender/Receiver network visualization
- Real-time simulation event log
- Timeout and retransmission demonstration
- Simulation statistics
- START, STOP and RESET controls
- Input validation

---

## 🖥️ Interface

The simulator contains:

1. **Simulation Settings**
   - Protocol
   - Number of Frames
   - Window Size
   - Packet Loss %
   - ACK Loss %
   - Animation Speed

2. **Network Visualization**
   - Sender
   - Receiver
   - Data Channel
   - ACK Channel
   - Current Frame
   - Current Status

3. **Simulation Event Log**
   - Frame transmission
   - Frame reception
   - Packet loss
   - ACK loss
   - ACK reception
   - Timeout
   - Retransmission

4. **Simulation Controls**
   - START
   - STOP
   - RESET

---

## ⚙️ Technologies Used

- **Python 3**
- **Tkinter**
- **Git & GitHub**

No external Python packages are required.

---

## 📂 Project Structure

```text
Sliding-Window-Protocol-Simulator/
│
├── main.py
├── protocol.py
├── DCN_Sliding_Window_Protocol_Project_Report.pdf
├── README.md
└── .gitignore