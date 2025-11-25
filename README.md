# Wearable Accelerometer Desktop Client

This application uses QFluentWidgets framework https://qfluentwidgets.com

This repository contains the source code for wearable accelerometer Desktop Client.
<p align="center">
  <img src="desktop_client.png" alt="Logo"/>
</p>


## Prerequisites

- Python 3.7 or <= 3.12

## Installation

1. Clone the repository and navigate to the project directory.

```bash
https://github.com/biospi/wearableAccelerometerClient.git
cd client
```

2. Create a virtual environment 
```bash
python -m venv .venv
.\.venv\Scripts\activate    # Windows
source .venv/bin/activate   # macOS/Linux
```

3. Install the required dependencies.

You can install the required dependencies by running:

```bash
pip install -r requirements.txt
```

This will install the following packages:

- PyQt5
- PyQt5-Frameless-Window
- darkdetect
- colorthief
- scipy
- pillow
- bleak

Alternatively, you can install the full set of dependencies using the setup script:

```bash
pip install .
```

## Running the Application

To launch the GUI, run the following command:

```bash
python gui.py
```

This will open the main window of the application. If your system has DPI scaling enabled, the application will automatically adjust accordingly.

## License

This project is licensed under the GPLv3 License. See the [LICENSE](LICENSE) file for details.