# -*- coding: utf-8 -*-
"""
DraveKas - eenvoudig huishoudboek/maandbudget (Dravenlock).
Gedeelde module: als onderdeel in DraveOffice (KasboekWidget) en als losse app (main()).
Je vult je inkomen in (alleen of met partner) en per onderdeel een bedrag;
de app rekent uit wat je overhoudt. Donationware. PyQt6. (c) Dravenlock.
"""
import os
import sys
import json
import csv
import locale

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox, QFrame,
    QScrollArea, QStatusBar, QDialog, QTextBrowser,
    QInputDialog,
)
from PyQt6.QtGui import QIcon, QFont, QColor, QPainter, QBrush, QAction, QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QLocale, QRectF

APP_NAAM = "DraveKas"
APP_VERSIE = "0.5"

# ---- huisstijl ----
BG = "#0e0e11"
PANEEL = "#16161b"
PANEEL2 = "#1c1c22"
TEKST = "#d4d4d4"
MUTED = "#8a8a94"
ACCENT = "#6fa3d6"
LINE = "#23232b"
WARN = "#d68a6f"
GOED = "#7fb069"

def _basis_map():
    # PyInstaller onefile pakt alles uit naar sys._MEIPASS; anders gewoon naast dit bestand.
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.abspath(__file__))


HIER = _basis_map()
ASSETS = os.path.join(HIER, "assets")
KAS_DATA_MAP = os.path.join(os.path.expanduser("~"), "DraveKasboek")
KAS_BESTAND = os.path.join(KAS_DATA_MAP, "huishoudboek.json")
KAS_CONFIG = os.path.join(KAS_DATA_MAP, "instellingen.json")

_TAAL = "nl"

INKOMST_STD = {"nl": ["Jij", "Partner"], "en": ["You", "Partner"]}
UITGAVE_STD = {
    "nl": ["Huur/Hypotheek", "Stroom", "Gas", "Water", "Verzekeringen", "Belasting",
           "Boodschappen", "Internet & telefoon", "Abonnementen", "Vervoer"],
    "en": ["Rent/Mortgage", "Electricity", "Gas", "Water", "Insurance", "Taxes",
           "Groceries", "Internet & phone", "Subscriptions", "Transport"],
}

KAS_TEKSTEN = {
    "nl": {
        "titel": "Huishoudboek", "per_maand": "per maand",
        "inkomsten": "Inkomsten", "uitgaven": "Uitgaven", "overzicht": "Overzicht",
        "naam": "Naam", "bedrag": "Bedrag",
        "voeg_inkomst": "+ Inkomst toevoegen", "voeg_uitgave": "+ Uitgave toevoegen",
        "verwijder_tip": "Deze regel verwijderen",
        "tot_inkomen": "Totaal inkomen", "tot_uitgaven": "Totaal uitgaven",
        "over": "Je houdt over", "tekort": "Tekort",
        "vergelijking": "Inkomen versus uitgaven",
        "menu": "Menu", "nieuw": "Nieuw", "openen": "Openen", "opslaan_als": "Opslaan als...",
        "export_csv": "Export CSV", "export_pdf": "Export PDF",
        "snelgids": "Snelgids", "donatie": "Donatie", "over_app": "Over",
        "opgeslagen": "Opgeslagen", "geexporteerd": "Geexporteerd: {p}",
        "fout": "Fout", "kon_niet": "Kon dit niet uitvoeren:\n{e}",
        "bevestig_nieuw": "Alles leegmaken en opnieuw beginnen?",
        "nieuwe_inkomst": "Naam van de inkomst:", "nieuwe_uitgave": "Naam van de uitgave:",
        "naam_inkomst": "Inkomst toevoegen", "naam_uitgave": "Uitgave toevoegen",
        "sluiten": "Sluiten", "bestand": "Bestand", "help": "Help", "afsluiten": "Afsluiten",
        "taal": "Taal", "taal_auto": "Automatisch (computer)",
        "taal_herstart": "Opgeslagen. Herstart om te wijzigen.",
        "tip_bedrag": "Vul het bedrag per maand in",
        "inkomen_extra": "Overig",
        "rapport_titel": "Huishoudboek - maandoverzicht",
    },
    "en": {
        "titel": "Household budget", "per_maand": "per month",
        "inkomsten": "Income", "uitgaven": "Expenses", "overzicht": "Overview",
        "naam": "Name", "bedrag": "Amount",
        "voeg_inkomst": "+ Add income", "voeg_uitgave": "+ Add expense",
        "verwijder_tip": "Remove this row",
        "tot_inkomen": "Total income", "tot_uitgaven": "Total expenses",
        "over": "You keep", "tekort": "Shortfall",
        "vergelijking": "Income versus expenses",
        "menu": "Menu", "nieuw": "New", "openen": "Open", "opslaan_als": "Save as...",
        "export_csv": "Export CSV", "export_pdf": "Export PDF",
        "snelgids": "Quick guide", "donatie": "Donate", "over_app": "About",
        "opgeslagen": "Saved", "geexporteerd": "Exported: {p}",
        "fout": "Error", "kon_niet": "Could not do this:\n{e}",
        "bevestig_nieuw": "Clear everything and start over?",
        "nieuwe_inkomst": "Name of the income:", "nieuwe_uitgave": "Name of the expense:",
        "naam_inkomst": "Add income", "naam_uitgave": "Add expense",
        "sluiten": "Close", "bestand": "File", "help": "Help", "afsluiten": "Quit",
        "taal": "Language", "taal_auto": "Automatic (computer)",
        "taal_herstart": "Saved. Restart to change.",
        "tip_bedrag": "Enter the monthly amount",
        "inkomen_extra": "Other",
        "rapport_titel": "Household budget - monthly overview",
    },
}


def KT(sleutel, **kw):
    s = KAS_TEKSTEN.get(_TAAL, KAS_TEKSTEN["nl"]).get(sleutel, sleutel)
    return s.format(**kw) if kw else s


def detecteer_taal():
    try:
        naam = QLocale.system().name().lower()
    except Exception:
        naam = ""
    if naam.startswith("nl"):
        return "nl"
    if naam.startswith("en"):
        return "en"
    try:
        code = (locale.getdefaultlocale()[0] or "").lower()
    except Exception:
        code = ""
    return "nl" if code.startswith("nl") else "en"


def euro(x):
    return ("\u20ac %.2f" % x).replace(".", ",")


def fmt_bedrag(x):
    if not x:
        return ""
    return ("%.2f" % x).replace(".", ",")


def parse_bedrag(tekst):
    try:
        return round(float(tekst.replace("\u20ac", "").replace(" ", "").replace(",", ".")), 2)
    except (ValueError, AttributeError):
        return 0.0


def app_icoon():
    p = os.path.join(ASSETS, "logo.png")
    return QIcon(p) if os.path.exists(p) else QIcon()


def centreer(widget, ouder=None):
    widget.adjustSize()
    if ouder is not None and ouder.isVisible():
        midden = ouder.frameGeometry().center()
    else:
        scr = QApplication.primaryScreen()
        midden = scr.availableGeometry().center() if scr else None
    if midden is not None:
        g = widget.frameGeometry(); g.moveCenter(midden); widget.move(g.topLeft())


def STIJL():
    return f"""
    QWidget {{ background:{BG}; color:{TEKST}; font-size:15px; }}
    QMainWindow, QDialog {{ background:{BG}; }}
    QLabel {{ color:{TEKST}; }}
    QToolBar {{ background:{PANEEL}; border:none; spacing:4px; padding:4px; }}
    QStatusBar {{ background:{PANEEL}; color:{MUTED}; }}
    QScrollArea {{ border:none; }}
    QPushButton {{ background:{PANEEL2}; color:{TEKST}; border:1px solid {LINE};
        border-radius:8px; padding:8px 14px; font-size:15px; }}
    QPushButton:hover {{ border-color:{ACCENT}; }}
    QPushButton#primair {{ background:{ACCENT}; color:#0c1116; border:none; font-weight:bold; }}
    QPushButton#menu {{ text-align:left; padding:12px 14px; font-size:16px; }}
    QPushButton#verwijder {{ color:{WARN}; border-color:{LINE}; font-weight:bold;
        padding:6px 10px; max-width:44px; }}
    QPushButton#verwijder:hover {{ border-color:{WARN}; }}
    QLineEdit {{ background:#e9e9e9; color:#111111; border:1px solid #9a9aa2;
        border-radius:6px; padding:9px 12px; font-size:17px; }}
    QLineEdit:focus {{ border:1px solid {ACCENT}; }}
    QTextBrowser {{ background:{PANEEL2}; color:{TEKST}; border:1px solid {LINE};
        border-radius:6px; padding:8px 10px; font-size:16px; }}
    QMenuBar {{ background:{PANEEL}; color:{TEKST}; }}
    QMenuBar::item:selected {{ background:{PANEEL2}; }}
    QMenu {{ background:{PANEEL}; color:{TEKST}; border:1px solid {LINE}; }}
    QMenu::item:selected {{ background:{ACCENT}; color:#0c1116; }}
    QToolTip {{ background:{PANEEL2}; color:#ffffff; border:1px solid {ACCENT};
        padding:6px 8px; font-size:14px; }}
    """


# ======================================================================
# Eenvoudige vergelijkingsbalk (inkomen vs uitgaven)
# ======================================================================
class KasGrafiek(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(120)
        self.inkomen = 0.0
        self.uitgaven = 0.0

    def zet(self, inkomen, uitgaven):
        self.inkomen = inkomen; self.uitgaven = uitgaven; self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(PANEEL))
        maxw = max(self.inkomen, self.uitgaven, 1.0)
        marge = 116
        baan_w = w - marge - 16
        f = QFont(); f.setPointSize(10); p.setFont(f)
        rijen = [(KT("inkomsten"), self.inkomen, GOED),
                 (KT("uitgaven"), self.uitgaven, WARN)]
        bh = 26
        y = (h - (len(rijen) * (bh + 18))) / 2 + 6
        for naam, waarde, kleur in rijen:
            p.setPen(QColor(MUTED))
            p.drawText(QRectF(0, y - 16, marge - 6, 16),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, naam)
            p.fillRect(QRectF(marge, y, baan_w, bh), QBrush(QColor(PANEEL2)))
            bw = (waarde / maxw) * baan_w
            p.fillRect(QRectF(marge, y, bw, bh), QBrush(QColor(kleur)))
            p.setPen(QColor("#ffffff"))
            p.drawText(QRectF(marge + 8, y, baan_w - 8, bh),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, euro(waarde))
            y += bh + 18
        p.end()


# ======================================================================
# Huishoudboek-widget (gedeeld)
# ======================================================================
class KasboekWidget(QWidget):
    status_signaal = pyqtSignal(str)

    def __init__(self, bestand=None):
        super().__init__()
        self.bestand = bestand or KAS_BESTAND
        self.inkomst_rijen = []   # records {naam, bedrag, rij}
        self.uitgave_rijen = []
        self._bouw()
        if not self._laad_stil():
            self._standaard_invullen()
        self._herbereken()

    # ---------- opbouw ----------
    def _bouw(self):
        buiten = QHBoxLayout(self)
        buiten.setContentsMargins(0, 0, 0, 0); buiten.setSpacing(0)
        buiten.addWidget(self._linker_menu())
        # midden: inkomsten + uitgaven (scrollbaar)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        kolom = QWidget(); kolom.setMaximumWidth(720)
        v = QVBoxLayout(kolom); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(16)
        titel = QLabel(KT("titel") + "  \u2014  " + KT("per_maand"))
        titel.setStyleSheet("font-size:22px; font-weight:bold; color:#ffffff;")
        v.addWidget(titel)
        v.addWidget(self._inkomsten_groep())
        v.addWidget(self._uitgaven_groep())
        v.addStretch(1)
        wrap = QWidget()
        hw = QHBoxLayout(wrap); hw.setContentsMargins(20, 16, 12, 28); hw.setSpacing(0)
        hw.addStretch(1); hw.addWidget(kolom); hw.addStretch(1)
        scroll.setWidget(wrap)
        buiten.addWidget(scroll, 1)
        # rechts: vast, compact overzicht (zoals het uitkomstvak van de rekenmachine)
        buiten.addWidget(self._overzicht_paneel())

    def _linker_menu(self):
        paneel = QFrame(); paneel.setFixedWidth(210)
        paneel.setStyleSheet("QFrame{background:%s; border-right:1px solid %s;}" % (PANEEL, LINE))
        v = QVBoxLayout(paneel); v.setContentsMargins(12, 16, 12, 16); v.setSpacing(8)
        logo = QLabel(); from PyQt6.QtGui import QPixmap
        pm = QPixmap(os.path.join(ASSETS, "logo.png"))
        if not pm.isNull():
            logo.setPixmap(pm.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(logo)
        kop = QLabel(KT("menu"))
        kop.setStyleSheet("color:%s; font-size:13px; border:none; padding-left:4px;" % MUTED)
        v.addWidget(kop)
        for naam, fn in (
            (KT("nieuw"), self.nieuw_boek), (KT("openen"), self.openen),
            (KT("opslaan_als"), self.opslaan_als),
            (KT("export_csv"), self.export_csv), (KT("export_pdf"), self.export_pdf),
            (KT("snelgids"), self._snelgids),
        ):
            b = QPushButton(naam); b.setObjectName("menu"); b.setMinimumHeight(44)
            b.setCursor(Qt.CursorShape.PointingHandCursor); b.clicked.connect(fn)
            v.addWidget(b)
        v.addStretch(1)
        d = QPushButton("\u2665 " + KT("donatie")); d.setObjectName("menu"); d.setMinimumHeight(44)
        d.setCursor(Qt.CursorShape.PointingHandCursor); d.clicked.connect(self._donatie)
        v.addWidget(d)
        return paneel

    def _groep(self, titel):
        box = QFrame()
        box.setStyleSheet("QFrame{background:%s; border:1px solid %s; border-radius:12px;}"
                          % (PANEEL, LINE))
        v = QVBoxLayout(box); v.setContentsMargins(16, 14, 16, 16); v.setSpacing(10)
        kop = QLabel(titel)
        kop.setStyleSheet("font-size:19px; font-weight:bold; color:#ffffff; border:none;")
        v.addWidget(kop)
        # kolomkoppen
        kk = QHBoxLayout()
        l1 = QLabel(KT("naam")); l1.setStyleSheet("color:%s; border:none; font-size:13px;" % MUTED)
        l2 = QLabel(KT("bedrag")); l2.setStyleSheet("color:%s; border:none; font-size:13px;" % MUTED)
        l2.setFixedWidth(160); l2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        kk.addWidget(l1, 1); kk.addWidget(l2); kk.addSpacing(52)
        v.addLayout(kk)
        rijen_box = QVBoxLayout(); rijen_box.setSpacing(8)
        v.addLayout(rijen_box)
        return box, v, rijen_box

    def _inkomsten_groep(self):
        box, v, self.ink_box = self._groep(KT("inkomsten"))
        knop = QPushButton(KT("voeg_inkomst")); knop.setMinimumHeight(40)
        knop.clicked.connect(self._vraag_inkomst)
        v.addWidget(knop, alignment=Qt.AlignmentFlag.AlignLeft)
        return box

    def _uitgaven_groep(self):
        box, v, self.uit_box = self._groep(KT("uitgaven"))
        knop = QPushButton(KT("voeg_uitgave")); knop.setMinimumHeight(40)
        knop.clicked.connect(self._vraag_uitgave)
        v.addWidget(knop, alignment=Qt.AlignmentFlag.AlignLeft)
        return box

    def _overzicht_paneel(self):
        paneel = QFrame(); paneel.setFixedWidth(340)
        paneel.setStyleSheet("QFrame{background:%s; border-left:1px solid %s;}" % (PANEEL, LINE))
        v = QVBoxLayout(paneel); v.setContentsMargins(18, 20, 18, 18); v.setSpacing(12)
        kop = QLabel(KT("overzicht"))
        kop.setStyleSheet("font-size:20px; font-weight:bold; color:#ffffff; border:none;")
        v.addWidget(kop)
        g = QGridLayout(); g.setSpacing(8)
        self.lbl_in = self._waarde(GOED); self.lbl_uit = self._waarde(WARN)
        k1 = QLabel(KT("tot_inkomen")); k1.setStyleSheet("border:none; color:%s; font-size:14px;" % MUTED)
        k2 = QLabel(KT("tot_uitgaven")); k2.setStyleSheet("border:none; color:%s; font-size:14px;" % MUTED)
        g.addWidget(k1, 0, 0); g.addWidget(self.lbl_in, 0, 1)
        g.addWidget(k2, 1, 0); g.addWidget(self.lbl_uit, 1, 1)
        v.addLayout(g)
        lijn = QFrame(); lijn.setFrameShape(QFrame.Shape.HLine); lijn.setStyleSheet("color:%s;" % LINE)
        v.addWidget(lijn)
        self.lbl_over_naam = QLabel(KT("over"))
        self.lbl_over_naam.setStyleSheet("font-size:16px; font-weight:bold; color:#fff; border:none;")
        v.addWidget(self.lbl_over_naam)
        self.lbl_over = QLabel("\u20ac 0,00")
        self.lbl_over.setStyleSheet("font-size:30px; font-weight:bold; color:%s; border:none;" % GOED)
        self.lbl_over.setAlignment(Qt.AlignmentFlag.AlignRight)
        v.addWidget(self.lbl_over)
        v.addSpacing(8)
        self.grafiek = KasGrafiek()
        v.addWidget(self.grafiek)
        v.addStretch(1)
        return paneel

    def _waarde(self, kleur):
        lb = QLabel("\u20ac 0,00")
        lb.setStyleSheet("font-size:19px; font-weight:bold; color:%s; border:none;" % kleur)
        lb.setAlignment(Qt.AlignmentFlag.AlignRight)
        return lb

    # ---------- rijen ----------
    def _maak_rij(self, lijst, box_layout, naam, bedrag):
        rij = QWidget()
        h = QHBoxLayout(rij); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(8)
        e_naam = QLineEdit(naam); e_naam.setMinimumHeight(42)
        e_bedrag = QLineEdit(fmt_bedrag(bedrag)); e_bedrag.setMinimumHeight(42)
        e_bedrag.setFixedWidth(160); e_bedrag.setPlaceholderText("0,00")
        e_bedrag.setAlignment(Qt.AlignmentFlag.AlignRight)
        e_bedrag.setToolTip(KT("tip_bedrag"))
        knop = QPushButton("\u2715"); knop.setObjectName("verwijder"); knop.setMinimumHeight(42)
        knop.setToolTip(KT("verwijder_tip")); knop.setCursor(Qt.CursorShape.PointingHandCursor)
        record = {"naam": e_naam, "bedrag": e_bedrag, "rij": rij}
        knop.clicked.connect(lambda: self._verwijder_rij(lijst, record))
        e_naam.textChanged.connect(self._wijzig)
        e_bedrag.textChanged.connect(self._wijzig)
        h.addWidget(e_naam, 1); h.addWidget(e_bedrag); h.addWidget(knop)
        box_layout.addWidget(rij)
        lijst.append(record)
        return record

    def _verwijder_rij(self, lijst, record):
        record["rij"].setParent(None)
        if record in lijst:
            lijst.remove(record)
        self._wijzig()

    def _vraag_inkomst(self):
        naam, ok = QInputDialog.getText(self, KT("naam_inkomst"), KT("nieuwe_inkomst"))
        if ok and naam.strip():
            self._maak_rij(self.inkomst_rijen, self.ink_box, naam.strip(), 0.0)
            self._wijzig()

    def _vraag_uitgave(self):
        naam, ok = QInputDialog.getText(self, KT("naam_uitgave"), KT("nieuwe_uitgave"))
        if ok and naam.strip():
            self._maak_rij(self.uitgave_rijen, self.uit_box, naam.strip(), 0.0)
            self._wijzig()

    # ---------- rekenen ----------
    def _wijzig(self):
        self._herbereken()
        self._opslaan_stil()

    def _herbereken(self):
        ti = sum(parse_bedrag(r["bedrag"].text()) for r in self.inkomst_rijen)
        tu = sum(parse_bedrag(r["bedrag"].text()) for r in self.uitgave_rijen)
        over = ti - tu
        self.lbl_in.setText(euro(ti)); self.lbl_uit.setText(euro(tu))
        self.lbl_over.setText(euro(over))
        if over >= 0:
            self.lbl_over.setStyleSheet("font-size:26px; font-weight:bold; color:%s; border:none;" % GOED)
            self.lbl_over_naam.setText(KT("over"))
        else:
            self.lbl_over.setStyleSheet("font-size:26px; font-weight:bold; color:%s; border:none;" % WARN)
            self.lbl_over_naam.setText(KT("tekort"))
        self.grafiek.zet(ti, tu)

    # ---------- gegevens ----------
    def _standaard_invullen(self):
        for naam in INKOMST_STD.get(_TAAL, INKOMST_STD["nl"]):
            self._maak_rij(self.inkomst_rijen, self.ink_box, naam, 0.0)
        for naam in UITGAVE_STD.get(_TAAL, UITGAVE_STD["nl"]):
            self._maak_rij(self.uitgave_rijen, self.uit_box, naam, 0.0)

    def _verzamel(self):
        return {
            "inkomsten": [{"naam": r["naam"].text(), "bedrag": parse_bedrag(r["bedrag"].text())}
                          for r in self.inkomst_rijen],
            "uitgaven": [{"naam": r["naam"].text(), "bedrag": parse_bedrag(r["bedrag"].text())}
                         for r in self.uitgave_rijen],
        }

    def _wis_rijen(self):
        for r in list(self.inkomst_rijen):
            r["rij"].setParent(None)
        for r in list(self.uitgave_rijen):
            r["rij"].setParent(None)
        self.inkomst_rijen.clear(); self.uitgave_rijen.clear()

    def _vul_uit(self, data):
        self._wis_rijen()
        for d in data.get("inkomsten", []):
            self._maak_rij(self.inkomst_rijen, self.ink_box, d.get("naam", ""), d.get("bedrag", 0.0))
        for d in data.get("uitgaven", []):
            self._maak_rij(self.uitgave_rijen, self.uit_box, d.get("naam", ""), d.get("bedrag", 0.0))

    def _opslaan_stil(self):
        try:
            os.makedirs(os.path.dirname(self.bestand), exist_ok=True)
            with open(self.bestand, "w", encoding="utf-8") as f:
                json.dump(self._verzamel(), f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _laad_stil(self):
        try:
            with open(self.bestand, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "inkomsten" not in data and "uitgaven" not in data:
                return False
            self._vul_uit(data)
            return True
        except Exception:
            return False

    def nieuw_boek(self):
        if QMessageBox.question(self, KT("nieuw"), KT("bevestig_nieuw"),
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) != QMessageBox.StandardButton.Yes:
            return
        self._wis_rijen(); self._standaard_invullen()
        self._wijzig()

    def openen(self):
        pad, _ = QFileDialog.getOpenFileName(self, KT("openen"), KAS_DATA_MAP,
                                             "DraveKas (*.json);;Alle bestanden (*)")
        if not pad:
            return
        try:
            with open(pad, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._vul_uit(data); self.bestand = pad
            self._herbereken(); self.status_signaal.emit(KT("opgeslagen"))
        except Exception as e:
            QMessageBox.critical(self, KT("fout"), KT("kon_niet", e=str(e)))

    def opslaan_als(self):
        pad, _ = QFileDialog.getSaveFileName(self, KT("opslaan_als"), KAS_DATA_MAP, "DraveKas (*.json)")
        if not pad:
            return
        if not pad.lower().endswith(".json"):
            pad += ".json"
        self.bestand = pad; self._opslaan_stil()
        self.status_signaal.emit(KT("opgeslagen"))

    def export_csv(self):
        pad, _ = QFileDialog.getSaveFileName(self, KT("export_csv"), KAS_DATA_MAP, "CSV (*.csv)")
        if not pad:
            return
        if not pad.lower().endswith(".csv"):
            pad += ".csv"
        try:
            d = self._verzamel()
            ti = sum(x["bedrag"] for x in d["inkomsten"])
            tu = sum(x["bedrag"] for x in d["uitgaven"])
            with open(pad, "w", encoding="utf-8-sig", newline="") as f:
                s = csv.writer(f, delimiter=";")
                s.writerow([KT("inkomsten"), KT("bedrag")])
                for x in d["inkomsten"]:
                    s.writerow([x["naam"], fmt_bedrag(x["bedrag"])])
                s.writerow([KT("tot_inkomen"), fmt_bedrag(ti)]); s.writerow([])
                s.writerow([KT("uitgaven"), KT("bedrag")])
                for x in d["uitgaven"]:
                    s.writerow([x["naam"], fmt_bedrag(x["bedrag"])])
                s.writerow([KT("tot_uitgaven"), fmt_bedrag(tu)]); s.writerow([])
                s.writerow([KT("over"), fmt_bedrag(ti - tu)])
            self.status_signaal.emit(KT("geexporteerd", p=os.path.basename(pad)))
        except Exception as e:
            QMessageBox.critical(self, KT("fout"), KT("kon_niet", e=str(e)))

    def export_pdf(self):
        pad, _ = QFileDialog.getSaveFileName(self, KT("export_pdf"), KAS_DATA_MAP, "PDF (*.pdf)")
        if not pad:
            return
        if not pad.lower().endswith(".pdf"):
            pad += ".pdf"
        try:
            from PyQt6.QtGui import QTextDocument
            from PyQt6.QtPrintSupport import QPrinter
            doc = QTextDocument(); doc.setHtml(self._rapport_html())
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(pad)
            doc.print(printer)
            self.status_signaal.emit(KT("geexporteerd", p=os.path.basename(pad)))
        except Exception as e:
            QMessageBox.critical(self, KT("fout"), KT("kon_niet", e=str(e)))

    def _rapport_html(self):
        d = self._verzamel()
        ti = sum(x["bedrag"] for x in d["inkomsten"])
        tu = sum(x["bedrag"] for x in d["uitgaven"])
        over = ti - tu

        def tabel(titel, rijen, totaal_naam, totaal):
            r = "".join("<tr><td>%s</td><td align='right'>%s</td></tr>"
                        % (x["naam"], euro(x["bedrag"])) for x in rijen)
            return ("<h2 style='color:#1a3a5a'>%s</h2>"
                    "<table border='1' cellspacing='0' cellpadding='5' width='60%%'>%s"
                    "<tr style='background:#dde6f0'><td><b>%s</b></td>"
                    "<td align='right'><b>%s</b></td></tr></table><br>"
                    % (titel, r, totaal_naam, euro(totaal)))
        kleur = "#2e7d32" if over >= 0 else "#b5462f"
        naam = KT("over") if over >= 0 else KT("tekort")
        return ("<h1 style='color:#1a3a5a'>%s</h1>%s%s"
                "<h2 style='color:%s'>%s: %s</h2>"
                % (KT("rapport_titel"),
                   tabel(KT("inkomsten"), d["inkomsten"], KT("tot_inkomen"), ti),
                   tabel(KT("uitgaven"), d["uitgaven"], KT("tot_uitgaven"), tu),
                   kleur, naam, euro(over)))

    # ---------- losse acties ----------
    def _snelgids(self):
        SnelgidsDialoog(self).exec()

    def _donatie(self):
        QMessageBox.information(self, KT("donatie"),
                                "DraveKas is donationware.\n\nPayPal: https://paypal.me/roger076\n"
                                "E-mail: service@dravenlock.nl\n\nKira & Dravenlock bedanken je!")


# ======================================================================
# Snelgids
# ======================================================================
SNELGIDS = {
    "nl": """<h2>DraveKas - Snelgids</h2>
<p>Dit is een eenvoudig <b>huishoudboek per maand</b>. Je vult gewoon bedragen in; de app rekent
uit wat je overhoudt.</p>
<p><b>Inkomsten:</b> vul je eigen inkomen in, en eventueel dat van je partner. Ze worden samen
opgeteld. Heb je nog ander inkomen? Klik op <b>+ Inkomst toevoegen</b>.</p>
<p><b>Uitgaven:</b> per onderdeel een vakje: huur, stroom, water, verzekeringen, belasting en zo
verder. Een naam aanpassen mag gewoon. Klik <b>+ Uitgave toevoegen</b> voor een eigen post, of op
het kruisje (x) om een regel weg te halen.</p>
<p><b>Overzicht:</b> onderaan zie je je totale inkomen, je totale uitgaven en wat je <b>overhoudt</b>
(of, als het rood is, je tekort).</p>
<p>Het menu staat links. Je kunt <b>exporteren</b> naar CSV of PDF. Alles wordt automatisch lokaal
bewaard.</p>""",
    "en": """<h2>DraveKas - Quick guide</h2>
<p>This is a simple <b>monthly household budget</b>. You just fill in amounts; the app works out
what you keep.</p>
<p><b>Income:</b> enter your own income and optionally your partner's. They are added together. More
income? Click <b>+ Add income</b>.</p>
<p><b>Expenses:</b> one box per item: rent, electricity, water, insurance, taxes and so on. You can
rename anything. Click <b>+ Add expense</b> for your own item, or the cross (x) to remove a row.</p>
<p><b>Overview:</b> at the bottom you see total income, total expenses and what you <b>keep</b> (or,
in red, your shortfall).</p>
<p>The menu is on the left. You can <b>export</b> to CSV or PDF. Everything is saved locally and
automatically.</p>""",
}
GIDS_STYLE = ("<style>h2{color:#9ecbff;font-size:23px;}p{color:#ededed;font-size:17px;"
              "line-height:1.7;}b{color:#fff;}</style>")


class SnelgidsDialoog(QDialog):
    def __init__(self, ouder):
        super().__init__(ouder)
        self.setWindowTitle(KT("snelgids")); self.setWindowIcon(app_icoon())
        self.resize(680, 560); self.setStyleSheet(STIJL())
        lay = QVBoxLayout(self)
        b = QTextBrowser(); b.setStyleSheet("QTextBrowser{background:%s;border:none;padding:18px;}" % PANEEL)
        b.setHtml(GIDS_STYLE + SNELGIDS.get(_TAAL, SNELGIDS["nl"]))
        lay.addWidget(b)
        k = QPushButton(KT("sluiten")); k.setObjectName("primair"); k.clicked.connect(self.accept)
        lay.addWidget(k)
        QTimer.singleShot(0, lambda: centreer(self, ouder))


# ======================================================================
# Zelfstandige app (DraveKas)
# ======================================================================
def laad_config():
    try:
        with open(KAS_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def bewaar_config(cfg):
    try:
        os.makedirs(KAS_DATA_MAP, exist_ok=True)
        with open(KAS_CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


class KasHoofdvenster(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle("%s  v%s" % (APP_NAAM, APP_VERSIE))
        self.setWindowIcon(app_icoon()); self.setStyleSheet(STIJL())
        self.kas = KasboekWidget()
        self.kas.status_signaal.connect(lambda t: self.statusBar().showMessage(t, 5000))
        self.setCentralWidget(self.kas)
        self.setStatusBar(QStatusBar())
        self._menu()

    def _menu(self):
        b = self.menuBar()
        m = b.addMenu(KT("bestand"))
        a = QAction(KT("afsluiten"), self); a.triggered.connect(self.close)
        a.setShortcut(QKeySequence("Ctrl+Q")); m.addAction(a)
        mt = b.addMenu(KT("taal"))
        huidig = self.cfg.get("taal") or "auto"
        for sleutel, label in (("auto", KT("taal_auto")), ("nl", "Nederlands"), ("en", "English")):
            act = QAction(label, self); act.setCheckable(True); act.setChecked(huidig == sleutel)
            act.triggered.connect(lambda _=False, s=sleutel: self._kies_taal(s))
            mt.addAction(act)
        mh = b.addMenu(KT("help"))
        a = QAction(KT("snelgids"), self); a.setShortcut(QKeySequence("F1"))
        a.triggered.connect(lambda: SnelgidsDialoog(self).exec()); mh.addAction(a)
        a = QAction(KT("over_app"), self); a.triggered.connect(self._over); mh.addAction(a)

    def _kies_taal(self, sleutel):
        if sleutel == "auto":
            self.cfg.pop("taal", None)
        else:
            self.cfg["taal"] = sleutel
        bewaar_config(self.cfg)
        QMessageBox.information(self, KT("taal"), KT("taal_herstart"))

    def _over(self):
        QMessageBox.information(self, KT("over_app"),
                                "%s v%s\n\nEenvoudig huishoudboek/maandbudget.\n"
                                "Donationware. (c) Dravenlock." % (APP_NAAM, APP_VERSIE))


def main():
    global _TAAL
    os.makedirs(KAS_DATA_MAP, exist_ok=True)
    # Windows: zorg dat de taakbalk het app-icoon toont i.p.v. het Python-icoon
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Dravenlock.DraveKas")
        except Exception:
            pass
    cfg = laad_config()
    _TAAL = cfg.get("taal") or detecteer_taal()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAAM); app.setWindowIcon(app_icoon())
    try:
        from PyQt6.QtCore import QTranslator, QLibraryInfo
        if _TAAL == "nl":
            pad = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
            for naam in ("qtbase_nl", "qt_nl"):
                t = QTranslator()
                if t.load(naam, pad):
                    app.installTranslator(t)
                    globals().setdefault("_vertalers", []).append(t)
    except Exception:
        pass
    v = KasHoofdvenster(cfg); v.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
