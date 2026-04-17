# FEC IoT Project

An Internet of Things (IoT) project that collects, processes, and visualizes sensor data in real-time. The project includes modular sensor scripts (temperature, humidity, light, and PM2.5), a central processing backend, and a dynamic web dashboard.

## Features

- **Real-time Monitoring:** Continuously updates sensor readings on the web dashboard.
- **Multiple Sensors:** Modular scripts for reading Temperature, Humidity, Light, and PM2.5 data.
- **Data Export:** Built-in functionality to export the collected IoT data to a CSV file directly from the dashboard.
- **Data Processing:** A dedicated processor to handle incoming sensor metrics.

## Project Structure

```text
FEC-IOT-PROJECT/
│
├── dashboard/                 # Frontend assets for the web dashboard
│   └── JS/
│       └── script.js          # Handles dashboard updates and CSV exports
│
├── sensors/                   # Individual modules for different sensor types
│   ├── config.py              # Configuration settings for sensors
│   ├── sensor_humidity.py     # Humidity sensor logic
│   ├── sensor_light.py        # Light sensor logic
│   ├── sensor_pm25.py         # PM2.5 (Air Quality) sensor logic
│   └── sensor_temperature.py  # Temperature sensor logic
│
├── app.py                     # Main application entry point (Backend Server)
├── processor.py               # Handles the processing of incoming sensor data
└── requirements.txt           # Python dependencies required for the project
```

## Prerequisites

- Python 3.x installed on your machine.
- Pip (Python package installer).

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DeltaDixshant/FEC_Iot_project.git
   cd FEC_Iot_project
   ```

2. **Create and activate a virtual environment (Optional but recommended):**
   ```bash
   # On Windows
   python -m venv dev
   .\dev\Scripts\activate

   # On macOS/Linux
   python3 -m venv dev
   source dev/bin/activate
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Start the application:**
   Run the main backend server:
   ```bash
   python app.py
   ```

2. **View the Dashboard:**
   Open the provided local URL (usually `http://127.0.0.1:5000` or similar, depending on your `app.py` setup) in your web browser.

3. **Export Data:**
   Click the export button on the dashboard to download the current sensor data as a `.csv` file.
