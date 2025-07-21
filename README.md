# OneDrive Custom Backup Tool

A Windows utility that moves folders to OneDrive and creates junction links for seamless access.

## ✨ Features

- **🔗 Junction Links**: Automatically creates junction links after moving folders to OneDrive
- **🎨 GUI & CLI**: Both graphical interface and command-line support
- **🛡️ Safe Operations**: Built-in validation and rollback functionality
- **📋 Junction Management**: List and manage existing junction links

## 🚀 Quick Start

### Download
Download the latest release: [Releases](https://github.com/newfebriwisnu/OneDrive-Custom-Backup-Tool/releases)

### Usage

#### GUI Mode
1. Run `OneDriveBackupTool.exe`
2. Select source folder and OneDrive target
3. Click "Execute Backup"

#### CLI Mode
```powershell
# Basic backup
.\OneDriveBackupTool-Console.exe --source "C:\MyFolder" --target "C:\Users\YourName\OneDrive\MyFolder"

# List junction links
.\OneDriveBackupTool-Console.exe --list-junctions

# Validate only
.\OneDriveBackupTool-Console.exe --source "C:\MyFolder" --target "C:\Users\YourName\OneDrive\MyFolder" --validate-only
```

## 🔧 How It Works

1. **Move**: Relocates your folder to OneDrive using PowerShell
2. **Link**: Creates junction link in original location  
3. **Sync**: OneDrive syncs your data to cloud
4. **Access**: Applications work normally, data stays protected

**Example:**
```
Before: C:\MyProject\ (local folder)
After:  C:\MyProject\ → C:\Users\You\OneDrive\MyProject\ (junction link)
```

## 💻 System Requirements

- Windows 10/11 (x64)
- PowerShell 5.1+
- OneDrive installed and configured
- Administrator rights (for junction creation)

## 🔍 Troubleshooting

**Access Denied?** → Run as Administrator using `Run-Debug.bat`
**PowerShell Issues?** → Automatically handled with base64 encoding
**Path Problems?** → Use `--verbose` flag for detailed errors

## 📁 File Sizes
- **OneDriveBackupTool.exe**: 11.22 MB (GUI version)
- **OneDriveBackupTool-Console.exe**: 11.23 MB (Console version)

## ⚠️ Important Notes

- Always backup important data before using
- Test with non-critical folders first
- Ensure OneDrive is syncing properly
- Some operations require administrator privileges

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

Made with ❤️ for seamless OneDrive integration
