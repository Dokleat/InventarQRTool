# InventarQRTool

Mjet i lehtë për Windows për krijimin e **etiketave QR** dhe **PDF** për inventarin. Ruana metadatat (p.sh. numri i faturës, porosisë, garancia, shitësi, inventari) dhe gjeneron etiketa të printueshme.

## Veçori
- Gjenerim etiketash QR me metadata
- Eksport në PDF (fletë A4, kompatibile me GoLabel)
- Import/Eksport CSV dhe Excel
- Ndërtim një‑skedar EXE për shpërndarje të thjeshtë

## Instalimi për zhvillues
```powershell
git clone https://github.com/USERNAME/InventarQRTool.git
cd InventarQRTool
py -3.12 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

## Ekzekutimi nga kodi
```powershell
python src/InventarQRTool.py
```

## Ndërtimi i EXE
```powershell
.uild.ps1
```

## Licenca
MIT – shihni [LICENSE](LICENSE).
