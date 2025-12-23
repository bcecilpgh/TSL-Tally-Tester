# TSL Tally Tester

A professional, standalone utility for testing TSL 3.1 tally systems. Send tally commands to video switchers, tally bridges, and UMD displays.

## Features

- **80 Input Support** - Control up to 80 tally inputs with pagination
- **TSL 3.1 Protocol** - Industry-standard tally protocol over UDP
- **Modern Dark UI** - Clean, professional interface
- **Live Status** - Real-time packet count and error tracking
- **Quick Actions**
  - All OFF - Clear all tally states instantly
  - Send Labels - Push all labels to the receiver
  - Demo Mode - Cycle through inputs 1-8 automatically
  - Chase Mode - Run a chase pattern across all 80 inputs
  - Random - Set random PGM and PVW inputs
- **Label Presets** - Quickly apply CAM #, Camera #, Input #, Source #, or clear all
- **Save/Load Config** - Export and import your settings and labels as JSON
- **Per-Input Controls**
  - Click main button to cycle: OFF -> PGM -> PVW -> BOTH
  - Quick P/V/X buttons for direct state control
  - Editable label field (14 characters max per TSL spec)

## Installation

### Windows

1. Install Python 3.8+ from [python.org](https://python.org)
   - During installation, check "Add Python to PATH"
2. Download this folder
3. Double-click `tsl_tally_tester.py` to run

Or from Command Prompt:
```cmd
python tsl_tally_tester.py
```

### macOS

1. Python 3 comes pre-installed on modern macOS. Verify with:
   ```bash
   python3 --version
   ```
2. If not installed, get it from [python.org](https://python.org) or via Homebrew:
   ```bash
   brew install python3 python-tk
   ```
3. Run the application:
   ```bash
   python3 tsl_tally_tester.py
   ```

### Linux

1. Ensure Python 3 and tkinter are installed:
   ```bash
   sudo apt install python3 python3-tk
   ```
2. Run:
   ```bash
   python3 tsl_tally_tester.py
   ```

## Usage

1. **Set Target IP** - Enter the IP address of your tally receiver/bridge
2. **Set Port** - Default is 5727 (standard TSL 3.1 port)
3. **Control Tallies** - Click buttons to send tally commands
4. **Watch Status** - Green flash = packet sent, Red flash = error

### TSL 3.1 Packet Format

Each packet is 18 bytes:
- Byte 0: `0x80` (header)
- Byte 1: Address (0-126, representing inputs 1-127)
- Byte 2: Control byte
  - Bit 0: Program/Tally 1 (Red)
  - Bit 1: Preview/Tally 2 (Green)
- Byte 3: Reserved
- Bytes 4-17: 14-character ASCII label

## Configuration
You can export/import configurations using Save/Load buttons:
- IP address
- Port number
- All 80 input labels

## Compatibility

Tested with:
- Blackmagic ATEM switchers (via tally bridges)
- TSL UMD displays
- Custom tally receivers
- Fresh AV Labs Tally Bridge

## License

MIT License - Free for personal and commercial use.

## Author

Fresh AV Labs  
https://www.freshavlabs.com
