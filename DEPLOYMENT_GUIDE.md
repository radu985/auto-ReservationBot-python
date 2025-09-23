# VFS Global Automation - Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying the VFS Global automation system as a Windows executable (.exe) file.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10 or later (64-bit)
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free disk space
- **Network**: Internet connection required
- **Permissions**: Administrator privileges recommended for camera access

### Software Dependencies
- Python 3.8+ (for building from source)
- Virtual environment support
- Git (for source code deployment)

## Build Process

### 1. Environment Setup
```bash
# Clone or download the project
cd Guinea_python_autoscript/task

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Build Executable
```bash
# Build desktop application
.\build_desktop.bat

# Build mobile application
.\build_mobile.bat
```

### 3. Post-Build Setup
The build scripts automatically:
- Install Playwright browsers
- Create required data directories
- Copy configuration files
- Set up OpenCV cascade files

## Deployment Options

### Option 1: Standalone EXE (Recommended)
**Best for**: Single-user deployment, simple distribution

**Steps**:
1. Run the build script: `.\build_desktop.bat`
2. Copy the entire `dist/` folder to target machine
3. Run `VFS-Desktop.exe` from the dist folder

**Advantages**:
- No Python installation required
- Self-contained with all dependencies
- Easy to distribute

**Disadvantages**:
- Large file size (~140MB)
- Slower startup time
- Limited customization

### Option 2: Source Code Deployment
**Best for**: Development, customization, multiple users

**Steps**:
1. Copy entire project folder to target machine
2. Install Python 3.8+ on target machine
3. Run setup script: `python setup.py install`
4. Run application: `python -m app.main`

**Advantages**:
- Smaller deployment size
- Faster startup
- Easy to modify and update
- Better debugging capabilities

**Disadvantages**:
- Requires Python installation
- More complex setup
- Dependency management needed

### Option 3: Virtual Environment Deployment
**Best for**: Controlled environments, enterprise deployment

**Steps**:
1. Create virtual environment on target machine
2. Copy project files
3. Install dependencies in virtual environment
4. Run from virtual environment

**Advantages**:
- Isolated dependencies
- Consistent environment
- Easy updates

**Disadvantages**:
- Requires Python on target machine
- More complex setup

## Configuration

### 1. Initial Setup
After first run, the application creates:
```
VFS-Desktop/
├── VFS-Desktop.exe
├── clients.csv          # Client data
├── proxies.txt          # Proxy configuration
├── config.py            # Application settings
├── info/                # Image capture data
├── documents/           # Uploaded documents
└── logs/                # Application logs
```

### 2. Proxy Configuration
Edit `proxies.txt` to add working proxies:
```
host1:port1:username1:password1
host2:port2:username2:password2
```

### 3. Client Data
The `clients.csv` file stores client information:
- First Name, Last Name
- Email, Password
- Mobile number, Date of birth
- Visa type, Application details

## Usage Instructions

### 1. First Run
1. Run `VFS-Desktop.exe`
2. Grant camera permissions if prompted
3. Wait for Playwright browser download (first run only)
4. Configure proxy settings if needed

### 2. Basic Operation
1. **Account Tab**: Register new clients
2. **Order Tab**: Configure visa application details
3. **Application Tab**: Enter personal information
4. **Image Tab**: Capture passport photos
5. **Service Tab**: Upload required documents
6. **Review & Payment**: Complete booking process

### 3. Bot Operation
1. Enter target URL in the URL field
2. Configure headless/visible browser mode
3. Click "Start Bot" to begin automation
4. Monitor status light for operation status

## Troubleshooting

### Common Issues

#### 1. Bot Won't Start
**Symptoms**: Status light turns yellow, then off
**Solutions**:
- Check internet connection
- Verify proxy configuration
- Run as administrator
- Check antivirus settings

#### 2. Camera Access Denied
**Symptoms**: Camera preview shows error
**Solutions**:
- Grant camera permissions
- Close other applications using camera
- Run as administrator
- Check camera hardware

#### 3. Data Not Saving
**Symptoms**: Changes not persisted between sessions
**Solutions**:
- Check write permissions to EXE directory
- Run as administrator
- Verify disk space
- Check antivirus interference

#### 4. Application Crashes
**Symptoms**: EXE stops unexpectedly
**Solutions**:
- Check Windows Event Viewer
- Run from command line for error details
- Verify all files present in EXE directory
- Check system requirements

### Advanced Troubleshooting

#### 1. Debug Mode
Run from command line to see detailed errors:
```bash
cd dist
VFS-Desktop.exe --debug
```

#### 2. Log Analysis
Check logs in the `logs/` directory for detailed error information.

#### 3. Dependency Issues
If modules are missing:
1. Rebuild with updated spec files
2. Check hiddenimports in PyInstaller spec
3. Verify all dependencies in requirements.txt

## Security Considerations

### 1. Data Protection
- Client data is stored locally in CSV format
- No data is transmitted to external servers
- Use encryption for sensitive deployments

### 2. Network Security
- Proxy credentials are stored in plain text
- Use secure proxies for production
- Consider VPN for additional security

### 3. Access Control
- Run with minimal required permissions
- Use Windows user accounts for access control
- Regular security updates

## Performance Optimization

### 1. System Optimization
- Close unnecessary applications
- Ensure adequate RAM available
- Use SSD storage for better performance

### 2. Network Optimization
- Use fast, reliable internet connection
- Configure working proxies
- Monitor bandwidth usage

### 3. Application Optimization
- Use headless mode for better performance
- Limit concurrent operations
- Regular cleanup of log files

## Maintenance

### 1. Regular Updates
- Update proxy lists regularly
- Monitor for VFS Global website changes
- Update application as needed

### 2. Data Backup
- Regular backup of `clients.csv`
- Backup uploaded documents
- Archive log files

### 3. Monitoring
- Monitor application logs
- Check system performance
- Verify automation success rates

## Support and Documentation

### 1. Documentation Files
- `EXE_TROUBLESHOOTING_GUIDE.md`: Detailed troubleshooting
- `README.md`: Project overview
- `requirements.txt`: Dependencies list

### 2. Getting Help
1. Check troubleshooting guide first
2. Review application logs
3. Test with minimal configuration
4. Verify system requirements

### 3. Reporting Issues
When reporting issues, include:
- Operating system version
- Application version
- Error messages from logs
- Steps to reproduce
- System configuration

## Conclusion

The VFS Global automation system can be deployed in multiple ways depending on your needs. The standalone EXE deployment is recommended for most users due to its simplicity and self-contained nature. For development or customization needs, source code deployment provides more flexibility.

Always test the deployment in a controlled environment before production use, and maintain regular backups of important data.
