import os
from pathlib import Path
import re
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ---- Optional ReportLab (PDF); kemi edhe fallback pa të ----
try:
    from reportlab.lib.pagesizes import cm
    from reportlab.pdfgen import canvas as rl_canvas
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

# ---- Optional pywin32 (printing) ----
try:
    import win32print, win32ui
    from PIL import ImageWin
    WIN32_OK = True
except Exception:
    WIN32_OK = False

CSV_SPALTEN = [
    "Rechnungsdatum",
    "Rechnungsnummer",
    "Bestellnummer",
    "Garantie",
    "Händler",
    "Inventarnummer",
]

# ================= Helpera për Inventarnummer =================

def _collect_existing_invs_from_db(db_path: Path) -> set:
    if not db_path.exists():
        return set()
    try:
        df = pd.read_excel(db_path, dtype=str).fillna("")
        return set(x.strip() for x in df.get("Inventarnummer", []) if str(x).strip())
    except Exception:
        return set()

def _next_numeric_inv(existing: set, start_num: int) -> str:
    max_exist = start_num - 1
    for s in existing:
        if re.fullmatch(r"\d+", s):
            max_exist = max(max_exist, int(s))
    return str(max_exist + 1)

def _next_year_inv(existing: set, year: str) -> str:
    max_n = 0
    pat = re.compile(rf"INV-{re.escape(year)}-(\d+)$")
    for s in existing:
        m = pat.match(s)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"INV-{year}-{max_n+1:03d}"

def sicher_inventarnummer(df: pd.DataFrame, schema: str, start_num: int, db_path: Path) -> pd.DataFrame:
    from datetime import datetime
    existing = _collect_existing_invs_from_db(db_path)
    if "Inventarnummer" in df.columns:
        for v in df["Inventarnummer"].astype(str):
            v = v.strip()
            if v:
                existing.add(v)

    if schema == "jahr":
        for idx in df.index:
            inv = str(df.at[idx, "Inventarnummer"]).strip() if "Inventarnummer" in df.columns else ""
            if inv:
                continue
            rd = str(df.at[idx, "Rechnungsdatum"]) if "Rechnungsdatum" in df.columns else ""
            m = re.search(r"(20\d{2})", rd or "")
            year = m.group(1) if m else str(datetime.now().year)
            new_inv = _next_year_inv(existing, year)
            df.at[idx, "Inventarnummer"] = new_inv
            existing.add(new_inv)
    else:
        for idx in df.index:
            inv = str(df.at[idx, "Inventarnummer"]).strip() if "Inventarnummer" in df.columns else ""
            if inv:
                continue
            new_inv = _next_numeric_inv(existing, start_num)
            df.at[idx, "Inventarnummer"] = new_inv
            existing.add(new_inv)

    return df

# ================= Lexim/formatim =================

def tabelle_lesen(filepath: Path) -> pd.DataFrame:
    p = Path(filepath)
    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p, dtype=str).fillna("")
    elif p.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(p, dtype=str).fillna("")
    else:
        raise ValueError("Dateiformat muss .csv oder .xlsx sein.")
    df.columns = [c.strip() for c in df.columns]
    return df

def text_zeilen(row: pd.Series) -> list:
    return [
        f"Rechnungsdatum: {row.get('Rechnungsdatum','')}",
        f"Rechnungsnummer: {row.get('Rechnungsnummer','')}",
        f"Bestellnummer: {row.get('Bestellnummer','')}",
        f"Garantie: {row.get('Garantie','')}",
        f"Händler: {row.get('Händler','')}",
        f"Inventarnummer: {row.get('Inventarnummer','')}",
    ]

def qr_erstellen(text: str, box_size: int = 10, rand: int = 2):
    qr = qrcode.QRCode(box_size=box_size, border=rand)
    qr.add_data(text); qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")

# ================= Renderimi i etiketës (PNG/PDF) =================

def _wrap_to_width(draw, text, font, max_w):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        bbox = draw.textbbox((0,0), test, font=font)
        if (bbox[2]-bbox[0]) <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def _auto_fit_label(text_lines, dpi=300, font_name="arial.ttf"):
    width = int(round(5/2.54 * dpi))
    height = int(round(4/2.54 * dpi))
    margin = max(8, int(width * 0.06))
    page = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(page)
    try:
        base = ImageFont.truetype(font_name, 40)
    except:
        base = ImageFont.load_default()

    qr_size = int(height * 0.5)
    qr_y = height - qr_size - margin//3
    qr_x = (width - qr_size)//2

    text_h = qr_y - margin
    text_w = width - 2*margin

    def fits(font):
        lh = int(getattr(font, "size", 18) * 1.12)
        total = 0; wrapped_all = []
        for ln in text_lines:
            wrapped = _wrap_to_width(draw, ln, font, text_w)
            wrapped_all += wrapped
            total += len(wrapped) * lh
        return total <= text_h, wrapped_all, lh

    for size in range(64, 7, -1):
        try: f = ImageFont.truetype("arial.ttf", size)
        except: f = base
        ok, wrapped, lh = fits(f)
        if ok:
            pos = {"wrapped": wrapped, "lh": lh, "tx": margin, "ty": margin,
                   "qr_size": qr_size, "qr_x": qr_x, "qr_y": qr_y}
            return page, draw, f, pos

    pos = {"wrapped": text_lines, "lh": 16, "tx": margin, "ty": margin,
           "qr_size": qr_size, "qr_x": qr_x, "qr_y": qr_y}
    return page, draw, base, pos

def png_label_5x4(text_lines, qr_img, out_path: Path, dpi=300):
    page, draw, font, pos = _auto_fit_label(text_lines, dpi=dpi)
    x, y = pos["tx"], pos["ty"]
    for ln in pos["wrapped"]:
        draw.text((x, y), ln, font=font, fill="black"); y += pos["lh"]
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC
    qr_resized = qr_img.resize((pos["qr_size"], pos["qr_size"]), resample=resample)
    page.paste(qr_resized, (pos["qr_x"], pos["qr_y"]))
    page.save(out_path, dpi=(dpi, dpi))
    return page

def pdf_label_5x4(text_lines, qr_img, out_path: Path, png_page_image=None, dpi=300):
    if REPORTLAB_OK:
        w, h = (5*cm, 4*cm)
        c = rl_canvas.Canvas(str(out_path), pagesize=(w, h))
        left = 6; top = h - 6; bottom = 6
        y = top - 4
        c.setFont("Helvetica", 8.5)
        for ln in text_lines:
            while len(ln) > 64:
                c.drawString(left, y, ln[:64]); y -= 10; ln = ln[64:]
            c.drawString(left, y, ln); y -= 10
        qr_size = 2.0*cm
        x = (w - qr_size)/2; y_qr = bottom + 2
        tmp = str(out_path.with_suffix(".tmp_qr.png"))
        qr_img.save(tmp)
        c.drawImage(tmp, x, y_qr, width=qr_size, height=qr_size, mask='auto')
        try: os.remove(tmp)
        except: pass
        c.showPage(); c.save()
    else:
        # fallback: përdor imazhin
        if png_page_image is None:
            tmp_png = out_path.with_suffix(".tmp.png")
            png_page_image = png_label_5x4(text_lines, qr_img, tmp_png, dpi=dpi)
            try: os.remove(tmp_png)
            except: pass
        png_page_image.save(out_path, "PDF", resolution=dpi)

# ================= Excel DB =================

def append_to_excel_db(out_dir: Path, df_new: pd.DataFrame):
    db_path = out_dir / "Inventar_DB.xlsx"
    if db_path.exists():
        try:
            df_old = pd.read_excel(db_path, dtype=str).fillna("")
        except Exception:
            df_old = pd.DataFrame(columns=CSV_SPALTEN)
    else:
        df_old = pd.DataFrame(columns=CSV_SPALTEN)
    df_all = pd.concat([df_old, df_new], ignore_index=True)
    if "Inventarnummer" in df_all.columns:
        df_all = df_all.drop_duplicates(subset=["Inventarnummer"], keep="last")
    df_all.to_excel(db_path, index=False)
    return db_path

# ================= File naming pa mbishkrim =================

def free_path(base: Path) -> Path:
    if not base.exists():
        return base
    i = 2
    while True:
        cand = base.with_name(f"{base.stem}_v{i}{base.suffix}")
        if not cand.exists():
            return cand
        i += 1

# ================= PRINTING (Windows GDI) =================

def list_printers_text():
    if not WIN32_OK:
        return "(pywin32 nuk është i instaluar)"
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = [p[2] for p in win32print.EnumPrinters(flags)]
    if not printers:
        return "(Nuk u gjet asnjë printer në Windows)"
    return "\n".join(printers)

def print_png_to_printer(printer_name: str, png_path: Path, label_mm=(50,40)):
    if not WIN32_OK:
        raise RuntimeError("Printing kërkon 'pywin32'. Instalo: py -m pip install pywin32")
    # hap imazhin
    img = Image.open(png_path)
    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(printer_name)
    hdc.StartDoc(png_path.name)
    hdc.StartPage()

    # dimensionet e fletës printimi në pixels sipas driverit
    printable_w = hdc.GetDeviceCaps(8)   # HORZRES
    printable_h = hdc.GetDeviceCaps(10)  # VERTRES

    # ruaj raportin – përshtat në qendër
    img_w, img_h = img.size
    scale = min(printable_w / img_w, printable_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    x = (printable_w - new_w) // 2
    y = (printable_h - new_h) // 2

    dib = ImageWin.Dib(img)
    dib.draw(hdc.GetHandleOutput(), (x, y, x+new_w, y+new_h))

    hdc.EndPage()
    hdc.EndDoc()
    hdc.DeleteDC()

# ================= GUI =================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inventar QR & Etiketten Generator (DE)")
        self.geometry("980x700"); self.resizable(False, False)

        self.file_path = tk.StringVar(); self.out_dir = tk.StringVar()
        self.schema = tk.StringVar(value="nummerisch")
        self.start_num = tk.StringVar(value="1000001")
        self.png_dpi = tk.StringVar(value="300")

        # printing options
        self.printer_name = tk.StringVar()  # p.sh. "Label Intent BP730i"
        self.auto_print = tk.BooleanVar(value=False)

        pad = 10; frm = ttk.Frame(self); frm.pack(fill="both", expand=True, padx=pad, pady=pad)

        ttk.Label(frm, text="CSV / Excel auswählen (optional für Batch):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.file_path, width=70).grid(row=0, column=1, sticky="we", padx=(0,6))
        ttk.Button(frm, text="Durchsuchen…", command=self.sel_file).grid(row=0, column=2, sticky="e")

        ttk.Label(frm, text="Zielordner:").grid(row=1, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.out_dir, width=70).grid(row=1, column=1, sticky="we", padx=(0,6))
        ttk.Button(frm, text="Durchsuchen…", command=self.sel_out).grid(row=1, column=2, sticky="e")

        sch = ttk.Frame(frm); sch.grid(row=2, column=0, columnspan=3, sticky="we", pady=(6,6))
        ttk.Radiobutton(sch, text="Inventarnummer nummerisch (Start):", variable=self.schema, value="nummerisch").pack(side="left")
        ttk.Entry(sch, textvariable=self.start_num, width=12).pack(side="left", padx=(6,18))
        ttk.Radiobutton(sch, text="INV-<Jahr>-NNN", variable=self.schema, value="jahr").pack(side="left")
        ttk.Label(sch, text="DPI (PNG):").pack(side="left", padx=(18,2))
        ttk.Combobox(sch, textvariable=self.png_dpi, values=["203","300"], width=6, state="readonly").pack(side="left")

        # Printer settings
        prn = ttk.Labelframe(frm, text="Drucken")
        prn.grid(row=3, column=0, columnspan=3, sticky="we", pady=(8,8))
        ttk.Label(prn, text="Druckername/Adresse (wie in Windows angezeigt):").grid(row=0, column=0, sticky="w")
        ttk.Entry(prn, textvariable=self.printer_name, width=60).grid(row=0, column=1, sticky="we", padx=(6,6))
        ttk.Button(prn, text="Verfügbare Drucker", command=self.show_printers).grid(row=0, column=2, sticky="e")
        ttk.Checkbutton(prn, text="Automatisch drucken nach Erzeugung", variable=self.auto_print).grid(row=1, column=1, sticky="w", pady=(6,0))

        # Manuelle Eingabe
        man = ttk.Labelframe(frm, text="Manuelle Eingabe (ein Gerät hinzufügen)")
        man.grid(row=4, column=0, columnspan=3, sticky="we", pady=(8,8))
        self.e_rd = tk.StringVar(); self.e_rn = tk.StringVar(); self.e_bn = tk.StringVar()
        self.e_ga = tk.StringVar(); self.e_ha = tk.StringVar(); self.e_inv = tk.StringVar()
        labels = ["Rechnungsdatum", "Rechnungsnummer", "Bestellnummer", "Garantie", "Händler", "Inventarnummer (leer = auto)"]
        vars_ = [self.e_rd, self.e_rn, self.e_bn, self.e_ga, self.e_ha, self.e_inv]
        for i, (lab, var) in enumerate(zip(labels, vars_)):
            ttk.Label(man, text=lab + ":").grid(row=i, column=0, sticky="e", padx=(6,6), pady=2)
            ttk.Entry(man, textvariable=var, width=60).grid(row=i, column=1, sticky="we", padx=(0,6), pady=2)
        ttk.Button(man, text="Hinzufügen (PNG + PDF erzeugen)", command=self.add_single).grid(row=len(labels), column=1, sticky="e", pady=(6,2))

        self.status = ttk.Label(frm, text="Bereit.")
        self.status.grid(row=5, column=0, columnspan=2, sticky="w", pady=(6,6))
        ttk.Button(frm, text="Batch aus Datei erzeugen (PNG + PDF)", command=self.run_batch).grid(row=5, column=2, sticky="e")

        for i in range(3): frm.grid_columnconfigure(i, weight=1)

    # ---------- GUI helpers ----------
    def show_printers(self):
        text = list_printers_text()
        messagebox.showinfo("Verfügbare Drucker", text)

    def sel_file(self):
        fp = filedialog.askopenfilename(title="CSV oder Excel wählen", filetypes=[("CSV/Excel","*.csv *.xlsx *.xls")])
        if fp: self.file_path.set(fp)

    def sel_out(self):
        dp = filedialog.askdirectory(title="Zielordner wählen")
        if dp: self.out_dir.set(dp)

    def ensure_out_dir(self):
        dst = self.out_dir.get().strip()
        if not dst:
            messagebox.showwarning("Hinweis","Bitte zuerst Zielordner wählen."); return None
        out_dir = Path(dst); out_dir.mkdir(parents=True, exist_ok=True); return out_dir

    # ---------- core ----------
    def _numbering(self, df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
        schema = "jahr" if self.schema.get()=="jahr" else "nummerisch"
        start = self.start_num.get().strip()
        start_num = int(start) if (schema=="nummerisch" and start.isdigit()) else 1
        db_path = out_dir / "Inventar_DB.xlsx"
        return sicher_inventarnummer(df, schema=schema, start_num=start_num, db_path=db_path)

    def _save_one(self, out_dir: Path, row: pd.Series):
        lines = text_zeilen(row); qr_text = "\n".join(lines)
        inv = str(row["Inventarnummer"]).strip() or "ohneINV"
        self.status.config(text=f"Erzeuge: {inv} …"); self.update_idletasks()

        qr_img = qr_erstellen(qr_text)

        png_base = out_dir / f"Inventar_{inv}.png"
        png_path = free_path(png_base)
        page_img = png_label_5x4(lines, qr_img, png_path, dpi=int(self.png_dpi.get()))

        pdf_base = out_dir / f"Inventar_{inv}.pdf"
        pdf_path = free_path(pdf_base)
        pdf_label_5x4(lines, qr_img, pdf_path, png_page_image=page_img, dpi=int(self.png_dpi.get()))

        # printing (optional)
        if self.auto_print.get():
            if not self.printer_name.get().strip():
                messagebox.showwarning("Hinweis", "Kein Druckername angegeben.")
            else:
                try:
                    print_png_to_printer(self.printer_name.get().strip(), png_path)
                except Exception as e:
                    messagebox.showerror("Druckfehler", str(e))

        return inv

    def add_single(self):
        out_dir = self.ensure_out_dir()
        if out_dir is None: return
        rec = {
            "Rechnungsdatum": self.e_rd.get().strip(),
            "Rechnungsnummer": self.e_rn.get().strip(),
            "Bestellnummer": self.e_bn.get().strip(),
            "Garantie": self.e_ga.get().strip(),
            "Händler": self.e_ha.get().strip(),
            "Inventarnummer": self.e_inv.get().strip(),
        }
        df = pd.DataFrame([rec], columns=CSV_SPALTEN).fillna("")
        df = self._numbering(df, out_dir)
        inv = self._save_one(out_dir, df.iloc[0])
        db_path = append_to_excel_db(out_dir, df[CSV_SPALTEN])
        messagebox.showinfo("Fertig", f"Etikett erzeugt: {inv}\nInventar-DB: {db_path}")

    def run_batch(self):
        src = self.file_path.get().strip()
        if not src:
            messagebox.showwarning("Hinweis","Bitte CSV/Excel wählen oder nutzen Sie oben 'Manuelle Eingabe'."); return
        out_dir = self.ensure_out_dir()
        if out_dir is None: return
        try:
            df = tabelle_lesen(Path(src))
            fehlend = [f for f in CSV_SPALTEN if f not in df.columns]
            if fehlend:
                messagebox.showerror("Fehler","Folgende Spalten fehlen: " + ", ".join(fehlend)); return
            df = self._numbering(df, out_dir)
            for _, row in df.iterrows():
                self._save_one(out_dir, row)
            db_path = append_to_excel_db(out_dir, df[CSV_SPALTEN])
            messagebox.showinfo("Fertig", f"{len(df)} Etiketten erzeugt.\nInventar-DB: {db_path}")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

if __name__ == "__main__":
    app = App()
    app.mainloop()

