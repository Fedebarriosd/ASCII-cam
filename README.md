# ascii-cam

Real-time ASCII art webcam filter for OBS Studio on Windows.

Captures your webcam feed, converts each frame to colored ASCII art, and outputs it to OBS via a virtual camera. Supports automatic scene switching: the webcam is only captured when a designated OBS scene is active, freeing it for normal use in other scenes.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)
![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey)

## Features

- Colored ASCII art rendered in real time
- Outputs to OBS via OBS Virtual Camera (no third-party drivers needed)
- OBS WebSocket integration: automatically opens/releases the webcam based on the active scene
- Configurable resolution, font size, character density, color boost, and brightness

## Requirements

- Windows 10/11
- [OBS Studio](https://obsproject.com/) 28+ (includes Virtual Camera and WebSocket server)
- Python 3.10+

## Installation

```bash
pip install opencv-python pyvirtualcam Pillow numpy obsws-python
```

## OBS Setup

1. In OBS, go to **Tools → WebSocket Server Settings** and enable the WebSocket server (default port: 4455).
2. Add a **Video Capture Device** source in your target scene and set the device to **OBS Virtual Camera**.
3. For your normal webcam source (in other scenes), enable **Deactivate when not showing** in its properties.

## Configuration

Edit the constants at the top of `ascii_cam.py`:

| Variable | Description | Default |
|---|---|---|
| `CAM_INDEX` | Webcam index (0 = default) | `0` |
| `ASCII_COLS` | Number of character columns | `100` |
| `FONT_SIZE` | Font size in pt | `16` |
| `ASPECT` | Output aspect ratio | `400/720` |
| `COLOR_BOOST` | Saturation multiplier | `2.0` |
| `BRIGHTNESS_BOOST` | Brightness multiplier | `1.5` |
| `ASCII_SCENE` | OBS scene name that activates the filter | `"Gárrulo"` |
| `GAMEPLAY_SCENE` | OBS scene with your normal webcam | `"Gameplay"` |
| `GAMEPLAY_CAM_GRP` | Source group name containing the webcam in the gameplay scene | `"Webcam"` |
| `OBS_HOST` | OBS WebSocket host | `"localhost"` |
| `OBS_PORT` | OBS WebSocket port | `4455` |
| `OBS_PASSWORD` | OBS WebSocket password (leave empty if none) | `""` |

## Usage

1. Start OBS first.
2. Run the script:
   ```bash
   python ascii_cam.py
   ```
   Or double-click it in File Explorer.
3. The virtual camera starts automatically — do **not** click "Start Virtual Camera" in OBS manually.
4. Switch to your designated ASCII scene in OBS. The webcam will activate automatically.
5. Press **Q** in the terminal to quit.

## Philosophy

Free as in freedom, not free pizza. Forever.

## License

[GNU Affero General Public License v3.0](LICENSE)
