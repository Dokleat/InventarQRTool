# InventarQRTool

Ein leichtgewichtiges Windows-Desktop-Tool zum Erzeugen von **QR‑Etiketten** und **PDF‑Bögen** für Inventarobjekte. Es speichert Metadaten (z. B. Rechnungs‑Nr., Bestell‑Nr., Garantie, Händler, Inventarnummer) und exportiert druckfertige Etiketten.

## ✨ Funktionen
- QR‑Etiketten mit Metadaten generieren
- PDF‑Export (A4‑Bögen, GoLabel‑kompatibel)
- CSV/Excel Import & Export
- Ein‑Datei‑EXE‑Build für einfache Verteilung

## 📷 Screenshots
_Füge mindestens einen Screenshot unter `assets/screenshots/` hinzu und verlinke ihn hier._

## 🚀 Download
Siehe **Releases** – lade die aktuelle `InventarQRTool.exe` herunter.

## 🖥️ Voraussetzungen (für lokalen Build)
- Windows 10/11
- Python 3.12+

## 🔽 Installation (Entwickler:innen)
```powershell
# Repository klonen
git clone https://github.com/USERNAME/InventarQRTool.git
cd InventarQRTool

# Optionale virtuelle Umgebung
py -3.12 -m venv .venv
. .\.venv\Scripts\Activate.ps1

# Abhängigkeiten
python -m pip install -U pip
python -m pip install -r requirements.txt
```

## ▶️ Start aus dem Quellcode
```powershell
python src/InventarQRTool.py
```

## 🏗️ Portable EXE bauen
```powershell
.uild.ps1
```
Die EXE liegt danach unter `dist/InventarQRTool.exe`.

## 🏷️ Versionierung & Releases
Wir nutzen **SemVer** (MAJOR.MINOR.PATCH).
- Release taggen: `git tag v1.0.0 && git push origin v1.0.0`
- GitHub Actions baut automatisch und lädt die EXE unter **Releases** hoch.

## 📜 Lizenz
MIT – siehe [LICENSE](LICENSE).
