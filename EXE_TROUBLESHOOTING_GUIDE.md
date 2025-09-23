# VFS Global Automation - EXE Troubleshooting Guide

## Overview
This guide addresses common issues when running the VFS Global automation system as a Windows executable (.exe) file.

## Common Issues and Solutions

### 1. Bot Start Button Issues
**Problem**: Clicking "Start Bot" causes the status light to turn yellow and then automatically turn off.

**Causes & Solutions**:
- **Missing Dependencies**: Ensure all required modules are included in the EXE
  - Solution: Use the updated `app_main.spec` with comprehensive hiddenimports
- **Import Path Issues**: Modules not found in EXE environment
  - Solution: Fixed with proper path resolution in `_ensure_module_paths()`
- **Threading Issues**: VFSBotWorker signals not properly connected
  - Solution: Enhanced error handling in BotWorker class

### 2. Camera Access Issues
**Problem**: Clicking "Start Camera" in Image tab causes the executable to stop.

**Causes & Solutions**:
- **Camera Permission**: Windows may block camera access for EXE files
  - Solution: Run as administrator or grant camera permissions
- **OpenCV Cascade Files**: Face detection cascade files not found
  - Solution: Build script now copies cascade files to EXE directory
- **Camera Index Issues**: Default camera index (0) may not work
  - Solution: Enhanced camera detection tries multiple indices (0, 1, 2)

### 3. Data Persistence Issues
**Problem**: Data saved in the application is not being saved correctly.

**Causes & Solutions**:
- **Wrong File Paths**: Hardcoded paths don't work in EXE environment
  - Solution: Dynamic path resolution based on EXE location
- **Permission Issues**: EXE may not have write permissions to certain directories
  - Solution: Data saved to EXE directory (same folder as executable)

### 4. Setup Detection Error
**Problem**: "Setup has detected that Setup is currently running" error when closing.

**Causes & Solutions**:
- **Multiple Instances**: Another instance of the application is running
  - Solution: Check Task Manager and close all instances
- **Incomplete Shutdown**: Application didn't close properly
  - Solution: Enhanced cleanup in application shutdown

## Build Process Improvements

### Updated PyInstaller Spec Files
- Added comprehensive hiddenimports for all dependencies
- Included proper path resolution for both source and EXE environments
- Added all required data files and directories

### Enhanced Build Scripts
- Automatic Playwright browser installation
- Creation of required data directories
- Copying of initial configuration files
- OpenCV cascade file copying

### Runtime Environment Detection
- Automatic detection of EXE vs source environment
- Dynamic path resolution for data files
- Proper module import handling

## Best Practices for EXE Deployment

### 1. First Run
- The first run may take longer as Playwright downloads browser binaries
- Ensure internet connection for initial setup
- Run as administrator if camera access is needed

### 2. Data Management
- All data is saved in the same directory as the EXE
- Create backups of `clients.csv` and other data files
- The EXE creates `info/`, `documents/`, and `logs/` directories automatically

### 3. Camera Usage
- Grant camera permissions when prompted
- Ensure no other applications are using the camera
- Try different camera indices if the default doesn't work

### 4. Network Requirements
- Internet connection required for VFS Global website access
- Proxy configuration in `proxies.txt` for better success rates
- Playwright browser downloads on first run

## File Structure in EXE Directory
```
VFS-Desktop/
├── VFS-Desktop.exe          # Main executable
├── clients.csv              # Client data
├── proxies.txt              # Proxy configuration
├── config.py                # Application configuration
├── haarcascade_frontalface_default.xml  # OpenCV cascade file
├── info/                    # Image capture data
├── documents/               # Uploaded documents
└── logs/                    # Application logs
```

## Troubleshooting Steps

### If Bot Won't Start:
1. Check if all dependencies are installed
2. Verify internet connection
3. Check proxy configuration in `proxies.txt`
4. Run as administrator
5. Check Windows Defender/antivirus settings

### If Camera Won't Work:
1. Grant camera permissions
2. Close other applications using camera
3. Try running as administrator
4. Check camera hardware connection
5. Verify OpenCV installation

### If Data Won't Save:
1. Check write permissions to EXE directory
2. Run as administrator
3. Verify disk space
4. Check antivirus interference

### If Application Crashes:
1. Check Windows Event Viewer for error details
2. Run from command line to see error messages
3. Verify all required files are present
4. Check system requirements (Python 3.8+, Windows 10+)

## System Requirements
- Windows 10 or later
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Internet connection
- Camera (optional, for image capture)
- Administrator privileges (recommended)

## Support
If issues persist after following this guide:
1. Check the logs in the `logs/` directory
2. Run the application from command line to see detailed error messages
3. Verify all files are present in the EXE directory
4. Test with a fresh installation

## Alternative Deployment Options
If EXE deployment continues to have issues, consider:
1. **Source Code Deployment**: Run directly from Python source
2. **Docker Container**: Package in a containerized environment
3. **Virtual Environment**: Use venv for isolated deployment
4. **Cloud Deployment**: Deploy to cloud platform with proper environment setup
