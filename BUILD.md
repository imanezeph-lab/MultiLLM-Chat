# MultiLLM Chat — Build Instructions

## Quick method: GitHub Actions (no Mac needed)

Push a version tag — GitHub auto-builds Windows `.exe` and macOS `.dmg`:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Download the finished installers from **Releases** or the **Actions** tab.

---

## Manual build

### Windows
```
build_windows.bat
```
Produces `installer/MultiLLM-Chat.exe`

### macOS (run on a Mac)
```bash
chmod +x build_macos.sh
./build_macos.sh
```
Produces `installer/MultiLLM-Chat.dmg`

---

## Stack
- **PyQt6** — UI framework (exact ChatGPT dark-mode QSS)
- **PyInstaller** — packaging into single executable
- **Inno Setup** (Windows) / **create-dmg** (macOS) — installer

## Data locations
- Config: `%APPDATA%\MultiLLM-Chat\config.json` (Win) / `~/Library/Application Support/MultiLLM-Chat/config.json` (Mac)
- Screenshots: `~/Pictures/MultiLLM-Chat_Screenshots/`
