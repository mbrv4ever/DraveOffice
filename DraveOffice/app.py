# -*- coding: utf-8 -*-
"""
DraveOffice - lokale, offline office-suite (Dravenlock).
Een portaal met onderdelen: Tekstverwerker (DraveWriter) en Rekenmachine.
Donationware. PyQt6. (c) Dravenlock.
"""
import os
import sys
import json
import base64
import math
import ast
import locale
import kasboek
from kasboek import KasboekWidget

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QComboBox, QFileDialog,
    QMessageBox, QDialog, QToolBar, QStatusBar, QColorDialog, QListWidget, QSlider, QInputDialog,
    QSizePolicy, QCheckBox, QStackedWidget, QTextBrowser, QLayout, QFrame, QFontComboBox,
    QCompleter, QTableWidget, QTableWidgetItem, QStyledItemDelegate,
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QFont, QAction, QTextCharFormat, QTextListFormat,
    QTextCursor, QColor, QTextDocumentWriter, QKeySequence, QImage, QTextBlockFormat,
    QPainter, QPen,
)
from PyQt6.QtCore import (Qt, QSize, pyqtSignal, QRect, QPoint, QTimer, QLocale,
                          QTranslator, QLibraryInfo, QUrl)
from PyQt6.QtPrintSupport import QPrinter

APP_NAAM = "DraveOffice"
APP_VERSIE = "0.5.1"
ORG = "Dravenlock"

# ---- huisstijl kleuren ----
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
    # PyInstaller onefile pakt alles uit naar sys._MEIPASS; anders naast dit bestand.
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.abspath(__file__))


HIER = _basis_map()
ASSETS = os.path.join(HIER, "assets")
DATA_MAP = os.path.join(os.path.expanduser("~"), "DraveOffice-data")
CONFIG_BESTAND = os.path.join(DATA_MAP, "instellingen.json")

_TAAL = "nl"


class FlowLayout(QLayout):
    """Layout die widgets naast elkaar zet en netjes doorloopt naar een nieuwe rij."""
    def __init__(self, ouder=None, marge=0, tussen=8):
        super().__init__(ouder)
        if ouder is not None:
            self.setContentsMargins(marge, marge, marge, marge)
        self._tussen = tussen
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, breedte):
        return self._doe_layout(QRect(0, 0, breedte, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doe_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        m = self.contentsMargins()
        s += QSize(m.left() + m.right(), m.top() + m.bottom())
        return s

    def _doe_layout(self, rect, alleen_test):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        rij_hoog = 0
        rechts = rect.right() - m.right()
        for it in self._items:
            w = it.sizeHint().width()
            h = it.sizeHint().height()
            if x + w > rechts and rij_hoog > 0:
                x = rect.x() + m.left()
                y = y + rij_hoog + self._tussen
                rij_hoog = 0
            if not alleen_test:
                it.setGeometry(QRect(QPoint(x, y), QSize(w, h)))
            x += w + self._tussen
            rij_hoog = max(rij_hoog, h)
        return y + rij_hoog - rect.y() + m.bottom()


# ======================================================================
# Taal
# ======================================================================
TEKSTEN = {
    "nl": {
        "portaal": "Portaal", "welkom": "Welkom bij DraveOffice",
        "kies_onderdeel": "Kies een onderdeel om te beginnen",
        "tekstverwerker": "Tekstverwerker", "tekst_uitleg": "Documenten schrijven en opmaken",
        "rekenmachine": "Rekenmachine", "reken_uitleg": "Berekeningen maken en invoegen",
        "rekenblad": "Rekenblad", "blad_uitleg": "Tabellen en formules",
        "kasboek": "Kasboek", "kas_uitleg": "Inkomsten en uitgaven bijhouden",
        "presentatie": "Presentatie", "pres_uitleg": "Diavoorstellingen",
        "export_pdf": "Export PDF", "opgeslagen_als": "Opgeslagen: {p}",
        "tip_nieuw_pres": "Nieuwe, lege presentatie", "tip_openen_pres": "Een presentatie openen (.json)",
        "tip_opslaan_pres": "Presentatie opslaan (.json)", "tip_export_pdf_pres": "Alle dia's als PDF opslaan",
        "diavoorstelling": "Diavoorstelling",
        "tip_diavoorstelling": "Start de diavoorstelling op volledig scherm (F5)",
        "dias": "Dia's", "dia": "Dia", "tip_nieuwe_dia": "Een nieuwe dia toevoegen na de huidige",
        "tip_verwijder_dia": "De huidige dia verwijderen", "tip_omhoog": "Dia omhoog verplaatsen",
        "tip_omlaag": "Dia omlaag verplaatsen", "dia_titel_hint": "Titel van de dia",
        "dia_inhoud_hint": "Inhoud - typ een punt per regel", "dia_zonder_titel": "(zonder titel)",
        "dia_voorbeeld_titel": "Welkom bij DraveOffice",
        "dia_voorbeeld_inhoud": "Dit is je eerste dia\nTyp hier je punten, een per regel\nKlik op Diavoorstelling (F5) om te presenteren",
        "presenteer_hint": "Pijltjes of spatie = bladeren   |   Esc = sluiten",
        "pres_gewijzigd": "Presentatie gewijzigd",
        "afb_toevoegen": "Afbeelding toevoegen", "afb_vervangen": "Afbeelding vervangen",
        "afb_verwijderen": "Afbeelding verwijderen",
        "tip_afb_toevoegen": "Een afbeelding aan deze dia toevoegen (png, jpg)",
        "tip_afb_verwijderen": "De afbeelding van deze dia verwijderen",
        "quote": "Quote", "tip_quote": "De geselecteerde regel(s) als citaat opmaken",
        "tip_sleep_afb": "Sleep de afbeelding naar de gewenste plek",
        "tip_sleep_tekst": "Sleep dit tekstvak naar de gewenste plek",
        "link": "Link", "tip_link": "Maak van de geselecteerde tekst een link",
        "link_vraag": "Webadres (URL):",
        "sleep_tip": "Tip: sleep titel, tekst en afbeelding met het handvat",
        "afb_grootte": "Grootte afbeelding", "tip_afb_grootte": "Maak de afbeelding groter of kleiner",
        "dia_vb1": "Dit is je eerste dia", "dia_vb2": "Typ je punten en maak ze op",
        "dia_vb3": "Sleep een afbeelding waar je wilt",
        "tekenen": "Tekenen", "teken_uitleg": "Vormen en schema's",
        "database": "Database", "db_uitleg": "Gegevens beheren",
        "pen": "Pen", "lijn": "Lijn", "rechthoek": "Rechthoek", "ovaal": "Ovaal", "gum": "Gum",
        "dikte": "Dikte", "wissen": "Wissen", "teken_opslaan": "Opslaan (PNG)",
        "tip_pen": "Vrije lijn tekenen", "tip_lijn": "Rechte lijn trekken",
        "tip_rechthoek": "Rechthoek tekenen", "tip_ovaal": "Ovaal of cirkel tekenen",
        "tip_gum": "Gummen (wit overschilderen)", "tip_teken_kleur": "Kies een tekenkleur",
        "tip_dikte": "Lijndikte kiezen", "tip_wissen": "De hele tekening wissen",
        "tip_teken_ongedaan": "Laatste actie ongedaan maken",
        "tip_teken_opslaan": "De tekening opslaan als PNG", "tip_teken_openen": "Een afbeelding openen",
        "teken_wis_vraag": "De hele tekening wissen?", "teken_gewijzigd": "Tekening gewijzigd",
        "db_rij": "Rij", "db_kolom": "Kolom", "db_hernoem": "Kolom hernoemen",
        "tip_db_rij": "Een rij toevoegen", "tip_db_rij_weg": "De geselecteerde rij verwijderen",
        "tip_db_kolom": "Een kolom toevoegen", "tip_db_kolom_weg": "De geselecteerde kolom verwijderen",
        "tip_db_hernoem": "De geselecteerde kolom hernoemen", "tip_db_nieuw": "Nieuwe, lege tabel",
        "tip_db_openen": "Een tabel openen (.csv)", "tip_db_opslaan": "De tabel opslaan (.csv)",
        "db_kol1": "Naam", "db_kol2": "E-mail", "db_kol3": "Notitie",
        "db_kolom_naam": "Naam van de kolom:", "db_nieuw_vraag": "Nieuwe, lege tabel beginnen?",
        "db_gewijzigd": "Tabel gewijzigd",
        "binnenkort": "Binnenkort", "terug_portaal": "Portaal",
        "tip_nieuw_blad": "Nieuw, leeg rekenblad",
        "tip_openen_blad": "Een rekenblad openen (.csv of .xlsx)",
        "tip_opslaan_blad": "Rekenblad opslaan (.csv met formules of .xlsx met uitkomsten)",
        "formule_hint": "Typ een waarde of een formule, bv. =SOM(A1:A5)",
        "tip_formule": "Formule of waarde voor de geselecteerde cel. Functies: SOM, GEMIDDELDE, MIN, MAX, AANTAL, PRODUCT. Verwijzingen zoals A1 en bereiken zoals A1:A5.",
        "blad_gewijzigd": "Rekenblad gewijzigd",
        "voorbeeld": "Voorbeeld", "tip_voorbeeld": "Zet een ingevuld voorbeeld neer om mee te oefenen",
        "voorbeeld_vraag": "Het rekenblad wordt vervangen door een voorbeeld. Doorgaan?",
        "voorbeeld_klaar": "Voorbeeld ingevuld - speel er gerust mee!",
        "vb_product": "Product", "vb_aantal": "Aantal", "vb_prijs": "Prijs", "vb_totaal": "Totaal",
        "vb_appels": "Appels", "vb_brood": "Brood", "vb_melk": "Melk", "vb_totaal_rij": "Totaal",
        "formule_maken": "Formule maken", "tip_formule_maken": "Hulp: bouw een formule door te kiezen wat je wilt en welke cellen",
        "fh_in_cel": "De formule komt in cel {c}. Kies hieronder wat je wilt uitrekenen.",
        "fh_watdoen": "Wat wil je doen?",
        "fh_som": "Optellen van een reeks (SOM)", "fh_gem": "Gemiddelde van een reeks",
        "fh_min": "Kleinste waarde (MIN)", "fh_max": "Grootste waarde (MAX)",
        "fh_aantal": "Aantal getallen tellen", "fh_plus": "Twee cellen optellen",
        "fh_min2": "Twee cellen aftrekken", "fh_keer": "Twee cellen vermenigvuldigen",
        "fh_deel": "Twee cellen delen",
        "fh_van": "Van cel", "fh_tot": "Tot cel", "fh_cel1": "Cel 1", "fh_cel2": "Cel 2",
        "fh_wordt": "Dit wordt je formule:",
        "fh_uitleg_reeks": "Alle cellen van de eerste t/m de laatste worden meegerekend, bv. A1:A5.",
        "fh_uitleg_paar": "De twee cellen worden met elkaar verrekend, bv. A1 en B1.",
        "fh_zetin": "Zet in cel {c}", "fh_annuleren": "Annuleren",
        "fh_ongeldig": "Vul geldige celnamen in, zoals A1 of B5 (een letter gevolgd door een getal).",
        "nieuw": "Nieuw", "openen": "Openen", "opslaan": "Opslaan",
        "opslaan_als": "Opslaan als...", "afsluiten": "Afsluiten", "ongedaan": "Ongedaan", "opnieuw": "Opnieuw",
        "bestand": "Bestand", "beeld": "Beeld", "help": "Help",
        "snelgids": "Snelgids", "over": "Over DraveOffice", "sluiten": "Sluiten",
        "vet": "Vet", "cursief": "Cursief", "onderstreept": "Onderstreept",
        "lettertype": "Lettertype", "grootte": "Grootte", "kleur": "Tekstkleur",
        "links": "Links", "midden": "Midden", "rechts": "Rechts", "uitvullen": "Uitvullen",
        "opsomming": "Opsomming", "genummerd": "Genummerd",
        "kop1": "Kop 1", "kop2": "Kop 2", "normaal": "Normaal",
        "woorden": "Woorden: {w}   Tekens: {t}",
        "opgeslagen": "Opgeslagen: {p}", "geopend": "Geopend: {p}",
        "niet_opgeslagen": "Niet-opgeslagen wijzigingen",
        "bewaren_vraag": "Wil je de wijzigingen bewaren voor je verdergaat?",
        "fout": "Fout", "kon_niet_openen": "Kon bestand niet openen:\n{e}",
        "kon_niet_opslaan": "Kon bestand niet opslaan:\n{e}",
        "naamloos": "Naamloos",
        "wis": "Wis", "invoegen_doc": "Invoegen in document",
        "wetenschappelijk": "Wetenschappelijk", "standaard": "Standaard", "geschiedenis": "Geschiedenis",
        "reken_fout": "Ongeldige berekening",
        "ingevoegd": "Resultaat ingevoegd in het document",
        "geen_doc": "Open eerst de tekstverwerker om in te voegen",
        "donatie": "Donatie", "taal": "Taal", "taal_auto": "Automatisch (computer)", "taal_herstart": "De taal is opgeslagen. Herstart DraveOffice om de wijziging te zien.", "toon_welkom": "Dit scherm tonen bij opstarten",
        "start": "Aan de slag",
        "tip_nieuw": "Nieuw, leeg document beginnen",
        "tip_openen": "Een bestaand document openen (.txt .html .docx .odt)",
        "tip_opslaan": "Document opslaan",
        "tip_opslaan_als": "Opslaan onder een nieuwe naam of ander type (.txt .html .odt .docx .pdf)",
        "tip_ongedaan": "Maak de laatste wijziging ongedaan", "tip_opnieuw": "Herstel de ongedaan gemaakte wijziging",
        "tip_vet": "Tekst vet maken",
        "tip_cursief": "Tekst schuin (cursief) maken",
        "tip_onderstreept": "Tekst onderstrepen",
        "tip_lettertype": "Kies of zoek een lettertype (typ om te filteren)", "zoek_font": "Zoek lettertype...",
        "tip_grootte": "Kies de lettergrootte (in punten)",
        "tip_kleur": "Kies een tekstkleur",
        "tip_links": "Tekst links uitlijnen",
        "tip_midden": "Tekst in het midden zetten",
        "tip_rechts": "Tekst rechts uitlijnen",
        "tip_uitvullen": "Tekst aan beide kanten recht maken (uitvullen)",
        "tip_opsomming": "Opsomming met bolletjes maken",
        "tip_genummerd": "Genummerde lijst maken",
        "tip_kop": "Kop-stijl: gewone tekst of een titel",
        "tt_sin": "Sinus - goniometrie (hoek in radialen). Bijv. sin(0) = 0",
        "tt_cos": "Cosinus - goniometrie (hoek in radialen). Bijv. cos(0) = 1",
        "tt_tan": "Tangens - goniometrie (hoek in radialen)",
        "tt_sqrt": "Wortel (vierkantswortel). Bijv. wortel 16 = 4",
        "tt_ln": "Natuurlijke logaritme (grondtal e)",
        "tt_log": "Logaritme met grondtal 10. Bijv. log(1000) = 3",
        "tt_pow": "Macht: het getal tot een bepaalde macht. Bijv. 2^10 = 1024",
        "tt_pi": "Pi = 3,14159... (cirkelgetal)",
        "tt_haak_open": "Haakje openen - om de volgorde te bepalen",
        "tt_haak_dicht": "Haakje sluiten",
        "tt_kwad": "Kwadraat: het getal maal zichzelf. Bijv. 5 wordt 25",
        "tt_e": "Het getal e = 2,71828... (grondtal natuurlijke logaritme)",
        "tt_delen": "Delen",
        "tt_keer": "Vermenigvuldigen (keer)",
        "tt_min": "Aftrekken (min)",
        "tt_plus": "Optellen (plus)",
        "tt_komma": "Decimaalteken (punt)",
        "tt_procent": "Procent / rest bij deling",
        "tt_wis": "Alles wissen",
        "tt_backspace": "Laatste teken weghalen",
        "tt_isgelijk": "Bereken de uitkomst (= toets ook met Enter)",
        "kies_reken": "Kies:",
        "lengte": "Lengte", "oppervlakte": "Oppervlakte", "volume": "Volume (cup/liter)",
        "gewicht": "Gewicht", "temperatuur": "Temperatuur", "snelheid": "Snelheid",
        "tijd": "Tijd", "data": "Data (KB/MB/GB)", "btw": "BTW", "procent": "Procent",
        "waarde": "Waarde", "van": "Van", "naar": "Naar", "wissel": "Wisselen",
        "tip_wissel": "Wissel 'van' en 'naar' om",
        "bedrag": "Bedrag", "btw_tarief": "BTW-tarief (%)", "bedrag_is": "Bedrag is",
        "excl_btw": "Excl. BTW", "incl_btw": "Incl. BTW", "totaal_incl": "Totaal (incl. BTW)",
        "p_van_1": "Hoeveel is", "p_van_2": "% van",
        "p_welk_1": "", "p_welk_2": "is welk % van",
        "p_groei_1": "Verandering van", "p_groei_2": "naar",
        "energie": "Energie", "druk": "Druk", "vermogen": "Vermogen", "hoek": "Hoek",
        "getalstelsel": "Getalstelsel (binair/hex)", "valuta": "Valuta (internet)",
        "decimaal": "Decimaal", "binair": "Binair", "hex": "Hexadecimaal", "octaal": "Octaal",
        "ongeldig_getal": "Ongeldig getal voor dit stelsel",
        "internet_waarschuwing": "Let op: valuta-koersen worden van internet gehaald. Hiervoor heb je een internetverbinding nodig.",
        "koersen_ophalen": "Koersen ophalen", "bezig_ophalen": "Bezig met ophalen...",
        "nog_geen_koersen": "Nog geen koersen opgehaald.",
        "koersen_van": "Koersen van: {d}", "geen_internet": "Geen internet of koersen niet beschikbaar.",
    },
    "en": {
        "portaal": "Portal", "welkom": "Welcome to DraveOffice",
        "kies_onderdeel": "Pick a part to get started",
        "tekstverwerker": "Word processor", "tekst_uitleg": "Write and format documents",
        "rekenmachine": "Calculator", "reken_uitleg": "Make calculations and insert them",
        "rekenblad": "Spreadsheet", "blad_uitleg": "Tables and formulas",
        "kasboek": "Cash book", "kas_uitleg": "Track income and expenses",
        "presentatie": "Presentation", "pres_uitleg": "Slide shows",
        "export_pdf": "Export PDF", "opgeslagen_als": "Saved: {p}",
        "tip_nieuw_pres": "New, empty presentation", "tip_openen_pres": "Open a presentation (.json)",
        "tip_opslaan_pres": "Save presentation (.json)", "tip_export_pdf_pres": "Save all slides as PDF",
        "diavoorstelling": "Slide show",
        "tip_diavoorstelling": "Start the full-screen slide show (F5)",
        "dias": "Slides", "dia": "Slide", "tip_nieuwe_dia": "Add a new slide after the current one",
        "tip_verwijder_dia": "Delete the current slide", "tip_omhoog": "Move slide up",
        "tip_omlaag": "Move slide down", "dia_titel_hint": "Slide title",
        "dia_inhoud_hint": "Content - one point per line", "dia_zonder_titel": "(no title)",
        "dia_voorbeeld_titel": "Welcome to DraveOffice",
        "dia_voorbeeld_inhoud": "This is your first slide\nType your points here, one per line\nClick Slide show (F5) to present",
        "presenteer_hint": "Arrows or space = navigate   |   Esc = close",
        "pres_gewijzigd": "Presentation changed",
        "afb_toevoegen": "Add image", "afb_vervangen": "Replace image",
        "afb_verwijderen": "Remove image",
        "tip_afb_toevoegen": "Add an image to this slide (png, jpg)",
        "tip_afb_verwijderen": "Remove the image from this slide",
        "quote": "Quote", "tip_quote": "Format the selected line(s) as a quote",
        "tip_sleep_afb": "Drag the image to where you want it",
        "tip_sleep_tekst": "Drag this text box where you want it",
        "link": "Link", "tip_link": "Turn the selected text into a link",
        "link_vraag": "Web address (URL):",
        "sleep_tip": "Tip: drag title, text and image with the handle",
        "afb_grootte": "Image size", "tip_afb_grootte": "Make the image larger or smaller",
        "dia_vb1": "This is your first slide", "dia_vb2": "Type your points and format them",
        "dia_vb3": "Drag an image wherever you like",
        "tekenen": "Draw", "teken_uitleg": "Shapes and diagrams",
        "database": "Database", "db_uitleg": "Manage data",
        "pen": "Pen", "lijn": "Line", "rechthoek": "Rectangle", "ovaal": "Oval", "gum": "Eraser",
        "dikte": "Width", "wissen": "Clear", "teken_opslaan": "Save (PNG)",
        "tip_pen": "Draw a free line", "tip_lijn": "Draw a straight line",
        "tip_rechthoek": "Draw a rectangle", "tip_ovaal": "Draw an oval or circle",
        "tip_gum": "Erase (paint white)", "tip_teken_kleur": "Pick a drawing colour",
        "tip_dikte": "Choose line width", "tip_wissen": "Clear the whole drawing",
        "tip_teken_ongedaan": "Undo the last action",
        "tip_teken_opslaan": "Save the drawing as PNG", "tip_teken_openen": "Open an image",
        "teken_wis_vraag": "Clear the whole drawing?", "teken_gewijzigd": "Drawing changed",
        "db_rij": "Row", "db_kolom": "Column", "db_hernoem": "Rename column",
        "tip_db_rij": "Add a row", "tip_db_rij_weg": "Delete the selected row",
        "tip_db_kolom": "Add a column", "tip_db_kolom_weg": "Delete the selected column",
        "tip_db_hernoem": "Rename the selected column", "tip_db_nieuw": "New, empty table",
        "tip_db_openen": "Open a table (.csv)", "tip_db_opslaan": "Save the table (.csv)",
        "db_kol1": "Name", "db_kol2": "E-mail", "db_kol3": "Note",
        "db_kolom_naam": "Column name:", "db_nieuw_vraag": "Start a new, empty table?",
        "db_gewijzigd": "Table changed",
        "binnenkort": "Soon", "terug_portaal": "Portal",
        "tip_nieuw_blad": "New, empty spreadsheet",
        "tip_openen_blad": "Open a spreadsheet (.csv or .xlsx)",
        "tip_opslaan_blad": "Save spreadsheet (.csv with formulas or .xlsx with results)",
        "formule_hint": "Type a value or a formula, e.g. =SUM(A1:A5)",
        "tip_formule": "Formula or value for the selected cell. Functions: SUM, AVERAGE, MIN, MAX, COUNT, PRODUCT. References like A1 and ranges like A1:A5.",
        "blad_gewijzigd": "Spreadsheet changed",
        "voorbeeld": "Example", "tip_voorbeeld": "Drop in a filled example to practise with",
        "voorbeeld_vraag": "The spreadsheet will be replaced by an example. Continue?",
        "voorbeeld_klaar": "Example filled in - feel free to play with it!",
        "vb_product": "Product", "vb_aantal": "Quantity", "vb_prijs": "Price", "vb_totaal": "Total",
        "vb_appels": "Apples", "vb_brood": "Bread", "vb_melk": "Milk", "vb_totaal_rij": "Total",
        "formule_maken": "Make a formula", "tip_formule_maken": "Help: build a formula by choosing what you want and which cells",
        "fh_in_cel": "The formula will go in cell {c}. Choose below what to calculate.",
        "fh_watdoen": "What do you want to do?",
        "fh_som": "Add up a range (SUM)", "fh_gem": "Average of a range",
        "fh_min": "Smallest value (MIN)", "fh_max": "Largest value (MAX)",
        "fh_aantal": "Count the numbers", "fh_plus": "Add two cells",
        "fh_min2": "Subtract two cells", "fh_keer": "Multiply two cells",
        "fh_deel": "Divide two cells",
        "fh_van": "From cell", "fh_tot": "To cell", "fh_cel1": "Cell 1", "fh_cel2": "Cell 2",
        "fh_wordt": "This is your formula:",
        "fh_uitleg_reeks": "All cells from the first to the last are included, e.g. A1:A5.",
        "fh_uitleg_paar": "The two cells are combined, e.g. A1 and B1.",
        "fh_zetin": "Put in cell {c}", "fh_annuleren": "Cancel",
        "fh_ongeldig": "Enter valid cell names, like A1 or B5 (a letter followed by a number).",
        "nieuw": "New", "openen": "Open", "opslaan": "Save",
        "opslaan_als": "Save as...", "afsluiten": "Quit", "ongedaan": "Undo", "opnieuw": "Redo",
        "bestand": "File", "beeld": "View", "help": "Help",
        "snelgids": "Quick guide", "over": "About DraveOffice", "sluiten": "Close",
        "vet": "Bold", "cursief": "Italic", "onderstreept": "Underline",
        "lettertype": "Font", "grootte": "Size", "kleur": "Text colour",
        "links": "Left", "midden": "Center", "rechts": "Right", "uitvullen": "Justify",
        "opsomming": "Bullets", "genummerd": "Numbered",
        "kop1": "Heading 1", "kop2": "Heading 2", "normaal": "Normal",
        "woorden": "Words: {w}   Characters: {t}",
        "opgeslagen": "Saved: {p}", "geopend": "Opened: {p}",
        "niet_opgeslagen": "Unsaved changes",
        "bewaren_vraag": "Do you want to save your changes first?",
        "fout": "Error", "kon_niet_openen": "Could not open file:\n{e}",
        "kon_niet_opslaan": "Could not save file:\n{e}",
        "naamloos": "Untitled",
        "wis": "Clear", "invoegen_doc": "Insert into document",
        "wetenschappelijk": "Scientific", "standaard": "Standard", "geschiedenis": "History",
        "reken_fout": "Invalid calculation",
        "ingevoegd": "Result inserted into the document",
        "geen_doc": "Open the word processor first to insert",
        "donatie": "Donate", "taal": "Language", "taal_auto": "Automatic (computer)", "taal_herstart": "The language has been saved. Restart DraveOffice to see the change.", "toon_welkom": "Show this screen at startup",
        "start": "Get started",
        "tip_nieuw": "Start a new, empty document",
        "tip_openen": "Open an existing document (.txt .html .docx .odt)",
        "tip_opslaan": "Save the document",
        "tip_opslaan_als": "Save under a new name or type (.txt .html .odt .docx .pdf)",
        "tip_ongedaan": "Undo the last change", "tip_opnieuw": "Redo the undone change",
        "tip_vet": "Make text bold",
        "tip_cursief": "Make text italic (slanted)",
        "tip_onderstreept": "Underline text",
        "tip_lettertype": "Pick or search a font (type to filter)", "zoek_font": "Search font...",
        "tip_grootte": "Choose the font size (in points)",
        "tip_kleur": "Choose a text colour",
        "tip_links": "Align text left",
        "tip_midden": "Center the text",
        "tip_rechts": "Align text right",
        "tip_uitvullen": "Make text flush on both sides (justify)",
        "tip_opsomming": "Make a bulleted list",
        "tip_genummerd": "Make a numbered list",
        "tip_kop": "Heading style: normal text or a title",
        "tt_sin": "Sine - trigonometry (angle in radians). E.g. sin(0) = 0",
        "tt_cos": "Cosine - trigonometry (angle in radians). E.g. cos(0) = 1",
        "tt_tan": "Tangent - trigonometry (angle in radians)",
        "tt_sqrt": "Square root. E.g. root of 16 = 4",
        "tt_ln": "Natural logarithm (base e)",
        "tt_log": "Logarithm base 10. E.g. log(1000) = 3",
        "tt_pow": "Power: a number to a power. E.g. 2^10 = 1024",
        "tt_pi": "Pi = 3.14159... (circle constant)",
        "tt_haak_open": "Open bracket - to set the order",
        "tt_haak_dicht": "Close bracket",
        "tt_kwad": "Square: the number times itself. E.g. 5 becomes 25",
        "tt_e": "The number e = 2.71828... (base of natural log)",
        "tt_delen": "Divide",
        "tt_keer": "Multiply",
        "tt_min": "Subtract",
        "tt_plus": "Add",
        "tt_komma": "Decimal point",
        "tt_procent": "Percent / remainder",
        "tt_wis": "Clear everything",
        "tt_backspace": "Remove the last character",
        "tt_isgelijk": "Calculate the result (= also Enter)",
        "kies_reken": "Choose:",
        "lengte": "Length", "oppervlakte": "Area", "volume": "Volume (cup/litre)",
        "gewicht": "Weight", "temperatuur": "Temperature", "snelheid": "Speed",
        "tijd": "Time", "data": "Data (KB/MB/GB)", "btw": "VAT", "procent": "Percent",
        "waarde": "Value", "van": "From", "naar": "To", "wissel": "Swap",
        "tip_wissel": "Swap 'from' and 'to'",
        "bedrag": "Amount", "btw_tarief": "VAT rate (%)", "bedrag_is": "Amount is",
        "excl_btw": "Excl. VAT", "incl_btw": "Incl. VAT", "totaal_incl": "Total (incl. VAT)",
        "p_van_1": "How much is", "p_van_2": "% of",
        "p_welk_1": "", "p_welk_2": "is what % of",
        "p_groei_1": "Change from", "p_groei_2": "to",
        "energie": "Energy", "druk": "Pressure", "vermogen": "Power", "hoek": "Angle",
        "getalstelsel": "Number base (binary/hex)", "valuta": "Currency (internet)",
        "decimaal": "Decimal", "binair": "Binary", "hex": "Hexadecimal", "octaal": "Octal",
        "ongeldig_getal": "Invalid number for this base",
        "internet_waarschuwing": "Note: currency rates are fetched from the internet. This needs an internet connection.",
        "koersen_ophalen": "Fetch rates", "bezig_ophalen": "Fetching...",
        "nog_geen_koersen": "No rates fetched yet.",
        "koersen_van": "Rates from: {d}", "geen_internet": "No internet or rates unavailable.",
    },
}


def T(sleutel, **kw):
    s = TEKSTEN.get(_TAAL, TEKSTEN["nl"]).get(sleutel, sleutel)
    return s.format(**kw) if kw else s


def detecteer_taal():
    # Qt's QLocale pakt de Windows-systeemtaal betrouwbaar (bv. "nl_NL")
    try:
        naam = QLocale.system().name().lower()   # bv "nl_nl", "en_us"
    except Exception:
        naam = ""
    if naam.startswith("nl"):
        return "nl"
    if naam.startswith("en"):
        return "en"
    # terugval op Python-locale
    try:
        code = (locale.getdefaultlocale()[0] or "").lower()
    except Exception:
        code = ""
    return "nl" if code.startswith("nl") else "en"


# ======================================================================
# Config
# ======================================================================
def zorg_voor_mappen():
    os.makedirs(DATA_MAP, exist_ok=True)


def laad_config():
    try:
        with open(CONFIG_BESTAND, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def bewaar_config(cfg):
    try:
        zorg_voor_mappen()
        with open(CONFIG_BESTAND, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def app_icoon():
    p = os.path.join(ASSETS, "logo.png")
    if os.path.exists(p):
        return QIcon(p)
    return QIcon()


def centreer(widget, ouder=None):
    widget.adjustSize()
    if ouder is not None and ouder.isVisible():
        midden = ouder.frameGeometry().center()
    else:
        from PyQt6.QtWidgets import QApplication as _QA
        scr = _QA.primaryScreen()
        midden = scr.availableGeometry().center() if scr else QPoint(600, 400)
    g = widget.frameGeometry(); g.moveCenter(midden); widget.move(g.topLeft())


def STIJL():
    return f"""
    QWidget {{ background:{BG}; color:{TEKST}; font-size:15px; }}
    QMainWindow, QDialog {{ background:{BG}; }}
    QLabel {{ color:{TEKST}; }}
    QToolBar {{ background:{PANEEL}; border:none; spacing:4px; padding:4px; }}
    QStatusBar {{ background:{PANEEL}; color:{MUTED}; }}
    QPushButton {{
        background:{PANEEL2}; color:{TEKST}; border:1px solid {LINE};
        border-radius:8px; padding:8px 12px; font-size:15px;
    }}
    QPushButton:hover {{ border-color:{ACCENT}; }}
    QPushButton:pressed {{ background:{PANEEL}; }}
    QPushButton:disabled {{ color:{MUTED}; border-color:{LINE}; }}
    QPushButton#primair {{ background:{ACCENT}; color:#0c1116; border:none; font-weight:bold; }}
    QPushButton#gevaar {{ color:{WARN}; border-color:{WARN}; }}
    QPushButton#tegel {{ background:{PANEEL}; border:1px solid {LINE}; border-radius:14px; }}
    QPushButton#tegel:hover {{ border-color:{ACCENT}; background:{PANEEL2}; }}
    QTextEdit, QLineEdit, QListWidget, QTextBrowser {{
        background:{PANEEL}; color:{TEKST}; border:1px solid {LINE};
        border-radius:8px; selection-background-color:{ACCENT};
    }}
    QComboBox, QSpinBox {{
        background:{PANEEL2}; color:{TEKST}; border:1px solid {LINE};
        border-radius:6px; padding:5px 8px; font-size:15px;
    }}
    QComboBox QAbstractItemView {{ background:{PANEEL2}; color:{TEKST};
        selection-background-color:{ACCENT}; }}
    QCheckBox {{ color:{TEKST}; font-size:15px; }}
    QMenuBar {{ background:{PANEEL}; color:{TEKST}; }}
    QMenuBar::item:selected {{ background:{PANEEL2}; }}
    QMenu {{ background:{PANEEL}; color:{TEKST}; border:1px solid {LINE}; }}
    QMenu::item:selected {{ background:{ACCENT}; color:#0c1116; }}
    QToolTip {{ background:{PANEEL2}; color:#ffffff; border:1px solid {ACCENT};
        padding:8px 10px; font-size:15px; }}
    """


# ======================================================================
# Snelgids
# ======================================================================
GIDS_STYLE = ("<style>"
              "h2{color:#9ecbff;font-size:23px;}"
              "h3{color:#9ecbff;font-size:19px;margin-top:16px;}"
              "p{color:#ededed;font-size:17px;line-height:1.7;}"
              "b{color:#ffffff;}"
              "</style>")

SNELGIDS_NL = """
<h2>DraveOffice - Snelgids</h2>
<p>DraveOffice is een verzameling kantoor-onderdelen in een portaal. Je opent een onderdeel
vanuit het portaal en gaat met de knop <b>Portaal</b> weer terug.</p>
<h3>Tekstverwerker</h3>
<p>Schrijf en maak documenten op: <b>vet</b>, cursief, onderstreept, lettertype, grootte, kleur,
uitlijning en opsommingen. Opslaan kan in <b>.txt, .html, .odt en .docx</b>, en exporteren naar
<b>.pdf</b>. Openen kan van .txt, .html, .docx en .odt.</p>
<h3>Rekenmachine</h3>
<p>De rekenmachine opent in een <b>eigen venster</b>. De cijfers staan in het vak <b>Standaard</b> en de wetenschappelijke functies in een apart vak <b>Wetenschappelijk</b>, zodat je niet snel misklikt. Bovenaan staat een <b>keuzemenu</b>. Kies <b>Rekenmachine</b> voor gewone en wetenschappelijke
berekeningen, of kies een <b>omrekenmodule</b>: Lengte, Oppervlakte, Volume (cup/liter), Gewicht,
Temperatuur, Snelheid, Tijd, Data, <b>BTW</b> en <b>Procent</b>. Beweeg de muis over een knop voor
uitleg. Met <b>Invoegen in document</b> zet je elke uitkomst zo in je open tekstdocument.</p>
<h3>Rekenblad</h3>
<p>Werk met tabellen en formules. Typ in een cel een waarde of een <b>formule</b> die met = begint,
bijvoorbeeld <b>=A1+A2</b> of <b>=SOM(A1:A5)</b>. Functies: SOM, GEMIDDELDE, MIN, MAX, AANTAL, PRODUCT.
Je kunt verwijzen naar cellen (A1) en bereiken (A1:A5). Opslaan kan als <b>.csv</b> (met je formules) of
<b>.xlsx</b> (met de uitkomsten, voor Excel).</p>
<p><b>Nieuw hiermee?</b> Klik op <b>Voorbeeld</b> voor een ingevuld blad om mee te spelen, of op
<b>Formule maken</b>: dan kies je wat je wilt uitrekenen en welke cellen, en de app bouwt de formule.</p>
<h3>Presentatie</h3>
<p>Maak <b>dia's</b>. Links staat de lijst met dia's (met knoppen om een dia toe te voegen, te
verwijderen of te verplaatsen). In het midden geef je de dia een <b>titel</b> en <b>inhoud</b>
(typ een punt per regel). Met de <b>opmaakbalk</b> bovenaan kies je een <b>lettertype</b> en geef je de tekst een andere <b>grootte</b>, <b>kleur</b>, <b>vet/cursief</b>, een <b>opsomming</b>, een <b>quote</b> of een <b>link</b>. Je kunt ook een <b>afbeelding</b> toevoegen, die je vrij kunt <b>verslepen</b> en met de schuif groter of kleiner maakt. Ook de <b>titel</b> en de <b>tekst</b> sleep je met het handvat (☰) naar elke plek op de dia.
Klik op <b>Diavoorstelling</b> (of F5) om op het volledige scherm te
presenteren: blader met de pijltjes of spatie, en sluit met Esc. Je kunt opslaan en als PDF
exporteren.</p>
<h3>Tekenen</h3>
<p>Teken met de muis. Kies een gereedschap (<b>Pen</b>, <b>Lijn</b>, <b>Rechthoek</b>, <b>Ovaal</b>
of <b>Gum</b>), een <b>kleur</b> en een <b>dikte</b>. Met <b>Ongedaan</b> draai je je laatste actie
terug en met <b>Wissen</b> maak je het blad leeg. Je kunt een afbeelding <b>openen</b> en je tekening
<b>opslaan als PNG</b>.</p>
<h3>Database</h3>
<p>Beheer gegevens in een <b>tabel</b>. Voeg <b>rijen</b> en <b>kolommen</b> toe of verwijder ze,
en <b>hernoem</b> een kolom. Typ gewoon in de vakjes. Je tabel <b>open je en bewaar je als CSV</b>
(handig voor het rekenblad).</p>
"""

SNELGIDS_EN = """
<h2>DraveOffice - Quick guide</h2>
<p>DraveOffice is a set of office parts in one portal. Open a part from the portal and return with
the <b>Portal</b> button. <b>Tip:</b> hover the mouse over a button to see an explanation (a tooltip).</p>
<h3>Word processor</h3>
<p>Write and format documents: <b>bold</b>, italic, underline, font, size, colour, alignment and
lists. Save as <b>.txt, .html, .odt and .docx</b>, and export to <b>.pdf</b>. Open .txt, .html,
.docx and .odt.</p>
<h3>Calculator</h3>
<p>The calculator opens in its <b>own window</b>. Digits are in the <b>Standard</b> box and the scientific functions in a separate <b>Scientific</b> box, so you are less likely to misclick. At the top there is a <b>menu</b>. Choose <b>Calculator</b> for ordinary and scientific
calculations, or pick a <b>converter</b>: Length, Area, Volume (cup/litre), Weight, Temperature,
Speed, Time, Data, <b>VAT</b> and <b>Percent</b>. Hover a button for an explanation. Use
<b>Insert into document</b> to drop any result into your open document.</p>
<h3>Spreadsheet</h3>
<p>Work with tables and formulas. In a cell type a value or a <b>formula</b> starting with =, e.g.
<b>=A1+A2</b> or <b>=SUM(A1:A5)</b>. Functions: SUM, AVERAGE, MIN, MAX, COUNT, PRODUCT. Reference cells
(A1) and ranges (A1:A5). Save as <b>.csv</b> (keeps your formulas) or <b>.xlsx</b> (with the results,
for Excel).</p>
<p><b>New to this?</b> Click <b>Example</b> for a filled sheet to play with, or
<b>Make a formula</b>: choose what to calculate and which cells, and the app builds the formula.</p>
<h3>Presentation</h3>
<p>Create <b>slides</b>. The slide list is on the left (with buttons to add, delete or move a
slide). In the middle you give the slide a <b>title</b> and <b>content</b> (type one point per
line). Use the <b>formatting bar</b> at the top to pick a <b>font</b> and change the text <b>size</b>, <b>colour</b>, <b>bold/italic</b>, add a <b>bullet list</b>, a <b>quote</b> or a <b>link</b>. You can also add an <b>image</b> that you can freely <b>drag</b> and resize with the slider. The <b>title</b> and <b>text</b> can also be dragged with the handle (☰) anywhere on the slide.
Click <b>Slide show</b> (or F5) to present full screen: navigate with the arrows or space,
close with Esc. You can save and export to PDF.</p>
<h3>Draw</h3>
<p>Draw with the mouse. Pick a tool (<b>Pen</b>, <b>Line</b>, <b>Rectangle</b>, <b>Oval</b> or
<b>Eraser</b>), a <b>colour</b> and a <b>width</b>. <b>Undo</b> reverts your last action and
<b>Clear</b> empties the sheet. You can <b>open</b> an image and <b>save as PNG</b>.</p>
<h3>Database</h3>
<p>Manage data in a <b>table</b>. Add or remove <b>rows</b> and <b>columns</b>, and <b>rename</b> a
column. Just type in the cells. <b>Open and save as CSV</b>.</p>
"""


class SnelgidsDialoog(QDialog):
    def __init__(self, ouder, inhoud=None, titel=None):
        super().__init__(ouder)
        self.setWindowTitle(titel or T("snelgids")); self.setWindowIcon(app_icoon())
        self.resize(720, 640); self.setStyleSheet(STIJL())
        lay = QVBoxLayout(self)
        b = QTextBrowser(); b.setOpenExternalLinks(True)
        b.setStyleSheet("QTextBrowser{background:%s;color:#ededed;border:none;padding:18px;}" % PANEEL)
        b.setHtml(GIDS_STYLE + (inhoud or (SNELGIDS_NL if _TAAL == "nl" else SNELGIDS_EN)))
        lay.addWidget(b)
        k = QPushButton(T("sluiten")); k.setObjectName("primair")
        k.clicked.connect(self.accept); lay.addWidget(k)
        QTimer.singleShot(0, lambda: centreer(self, ouder))


# ======================================================================
# Portaal
# ======================================================================
class Portaal(QWidget):
    onderdeel_gekozen = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        buiten = QVBoxLayout(self)
        buiten.setContentsMargins(40, 30, 40, 30); buiten.setSpacing(14)
        kop = QLabel(T("welkom"))
        kop.setStyleSheet("font-size:30px; font-weight:bold; color:#ffffff;")
        kop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel(T("kies_onderdeel"))
        sub.setStyleSheet("font-size:17px; color:%s;" % MUTED)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buiten.addWidget(kop); buiten.addWidget(sub)
        buiten.addSpacing(10)
        rooster = QGridLayout(); rooster.setSpacing(18)
        tegels = [
            ("tekstverwerker", "tekst_uitleg", "writer", True),
            ("rekenmachine", "reken_uitleg", "calc", True),
            ("rekenblad", "blad_uitleg", "sheet", True),
            ("kasboek", "kas_uitleg", "kas", True),
            ("presentatie", "pres_uitleg", "slides", True),
            ("tekenen", "teken_uitleg", "draw", True),
            ("database", "db_uitleg", "db", True),
        ]
        for i, (titel, uitleg, sleutel, actief) in enumerate(tegels):
            rooster.addWidget(self._tegel(titel, uitleg, sleutel, actief), i // 3, i % 3)
        buiten.addLayout(rooster, 1)

    def _tegel(self, titel, uitleg, sleutel, actief):
        knop = QPushButton(); knop.setObjectName("tegel")
        knop.setMinimumSize(QSize(260, 150))
        knop.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lay = QVBoxLayout(knop); lay.setContentsMargins(18, 16, 18, 16); lay.setSpacing(6)
        t = QLabel(T(titel)); t.setStyleSheet("font-size:21px; font-weight:bold; color:#ffffff;")
        u = QLabel(T(uitleg)); u.setStyleSheet("font-size:14px; color:%s;" % MUTED)
        u.setWordWrap(True)
        lay.addWidget(t); lay.addWidget(u); lay.addStretch(1)
        if not actief:
            badge = QLabel(T("binnenkort"))
            badge.setStyleSheet("font-size:13px; color:%s; font-weight:bold;" % WARN)
            lay.addWidget(badge)
            knop.setEnabled(False)
        else:
            knop.clicked.connect(lambda: self.onderdeel_gekozen.emit(sleutel))
        return knop


# ======================================================================
# Tekstverwerker
# ======================================================================
LETTERGROOTTES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 40, 48]


class WriterWidget(QWidget):
    status_signaal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.huidig_pad = None
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        f = QFont("Arial", 14); self.editor.setFont(f)
        self.editor.document().setDefaultFont(f)
        self.editor.setStyleSheet(
            "QTextEdit{ background:#d6d6d6; color:#111111; border:none; padding:18px;"
            " font-size:16px; selection-background-color:%s; selection-color:#ffffff; }" % ACCENT)
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        lay.addWidget(self._maak_balk())
        lay.addWidget(self._maak_opmaakbalk())
        lay.addWidget(self.editor, 1)
        self.tel_label = QLabel("")
        self.tel_label.setStyleSheet("color:%s; padding:4px 8px;" % MUTED)
        lay.addWidget(self.tel_label)
        self.editor.textChanged.connect(self._tel)
        self.editor.currentCharFormatChanged.connect(self._sync_opmaak)
        self._tel()

    # ---- balken ----
    def _tb_knop(self, tekst, tip, fn, checkbaar=False, sneltoets=None):
        b = QPushButton(tekst)
        b.setMinimumHeight(42)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet("font-size:16px; padding:6px 14px;")
        volle_tip = tip + (("   (%s)" % sneltoets) if sneltoets else "")
        b.setToolTip(volle_tip)
        b.setStatusTip(volle_tip)
        if checkbaar:
            b.setCheckable(True)
        if fn:
            b.clicked.connect(fn)
        if sneltoets:
            b.setShortcut(QKeySequence(sneltoets))
        return b

    def _maak_balk(self):
        bar = QWidget(); bar.setStyleSheet("background:%s;" % PANEEL)
        h = QHBoxLayout(bar); h.setContentsMargins(8, 6, 8, 6); h.setSpacing(8)
        for tekst, tip, fn, st in (
            (T("nieuw"), T("tip_nieuw"), self.nieuw, "Ctrl+N"),
            (T("openen"), T("tip_openen"), self.openen, "Ctrl+O"),
            (T("opslaan"), T("tip_opslaan"), self.opslaan, "Ctrl+S"),
            (T("opslaan_als"), T("tip_opslaan_als"), self.opslaan_als, "Ctrl+Shift+S"),
        ):
            h.addWidget(self._tb_knop(tekst, tip, fn, sneltoets=st))
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color:%s;" % LINE)
        h.addWidget(sep)
        # ongedaan / opnieuw (sneltoets in de tip; QTextEdit doet Ctrl+Z/Ctrl+Y zelf al)
        self.b_ongedaan = self._tb_knop(T("ongedaan"), T("tip_ongedaan") + "   (Ctrl+Z)",
                                        self.editor.undo)
        self.b_opnieuw = self._tb_knop(T("opnieuw"), T("tip_opnieuw") + "   (Ctrl+Y)",
                                       self.editor.redo)
        self.b_ongedaan.setEnabled(False); self.b_opnieuw.setEnabled(False)
        self.editor.undoAvailable.connect(self.b_ongedaan.setEnabled)
        self.editor.redoAvailable.connect(self.b_opnieuw.setEnabled)
        h.addWidget(self.b_ongedaan); h.addWidget(self.b_opnieuw)
        h.addStretch(1)
        return bar

    def _maak_opmaakbalk(self):
        bar = QWidget(); bar.setStyleSheet("background:%s;" % PANEEL2)
        h = FlowLayout(bar, marge=8, tussen=8)
        self.b_vet = self._tb_knop(T("vet"), T("tip_vet"), self._vet,
                                   checkbaar=True, sneltoets="Ctrl+B")
        self.b_cur = self._tb_knop(T("cursief"), T("tip_cursief"), self._cursief,
                                   checkbaar=True, sneltoets="Ctrl+I")
        self.b_ond = self._tb_knop(T("onderstreept"), T("tip_onderstreept"), self._onderstreept,
                                   checkbaar=True, sneltoets="Ctrl+U")
        h.addWidget(self.b_vet); h.addWidget(self.b_cur); h.addWidget(self.b_ond)
        # lettertype - laadt alle op het systeem (Windows) geinstalleerde fonts, doorzoekbaar
        self.font_combo = QFontComboBox()
        self.font_combo.setMinimumWidth(210); self.font_combo.setMinimumHeight(42)
        self.font_combo.setToolTip(T("tip_lettertype"))
        self.font_combo.setEditable(True)
        self.font_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.font_combo.lineEdit().setPlaceholderText(T("zoek_font"))
        comp = self.font_combo.completer()
        if comp is not None:
            comp.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            comp.setFilterMode(Qt.MatchFlag.MatchContains)
            comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            comp.activated[str].connect(self._zet_font)
        self.font_combo.setCurrentFont(QFont("Arial"))
        # alleen toepassen als de gebruiker echt een font kiest/bevestigt (niet bij elke toetsaanslag)
        self.font_combo.textActivated.connect(self._zet_font)
        h.addWidget(self.font_combo)
        # grootte
        self.size_combo = QComboBox()
        self.size_combo.addItems([str(s) for s in LETTERGROOTTES])
        self.size_combo.setCurrentText("14")
        self.size_combo.setMinimumWidth(72); self.size_combo.setMinimumHeight(42)
        self.size_combo.setToolTip(T("tip_grootte"))
        self.size_combo.currentTextChanged.connect(self._zet_grootte)
        h.addWidget(self.size_combo)
        # kleur
        h.addWidget(self._tb_knop(T("kleur"), T("tip_kleur"), self._kleur))
        # uitlijning
        h.addWidget(self._tb_knop(T("links"), T("tip_links"),
                                  lambda: self._uitlijn(Qt.AlignmentFlag.AlignLeft)))
        h.addWidget(self._tb_knop(T("midden"), T("tip_midden"),
                                  lambda: self._uitlijn(Qt.AlignmentFlag.AlignCenter)))
        h.addWidget(self._tb_knop(T("rechts"), T("tip_rechts"),
                                  lambda: self._uitlijn(Qt.AlignmentFlag.AlignRight)))
        h.addWidget(self._tb_knop(T("uitvullen"), T("tip_uitvullen"),
                                  lambda: self._uitlijn(Qt.AlignmentFlag.AlignJustify)))
        # lijsten
        h.addWidget(self._tb_knop(T("opsomming"), T("tip_opsomming"),
                                  lambda: self._lijst(QTextListFormat.Style.ListDisc)))
        h.addWidget(self._tb_knop(T("genummerd"), T("tip_genummerd"),
                                  lambda: self._lijst(QTextListFormat.Style.ListDecimal)))
        # koppen
        kop = QComboBox(); kop.addItems([T("normaal"), T("kop1"), T("kop2")])
        kop.currentIndexChanged.connect(self._zet_kop)
        kop.setMinimumWidth(120); kop.setMinimumHeight(42)
        kop.setToolTip(T("tip_kop"))
        self.kop_combo = kop
        h.addWidget(kop)
        bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        return bar

    # ---- opmaak ----
    def _merge(self, fmt):
        cur = self.editor.textCursor()
        if not cur.hasSelection():
            cur.select(QTextCursor.SelectionType.WordUnderCursor)
        cur.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def _vet(self):
        f = QTextCharFormat()
        f.setFontWeight(QFont.Weight.Bold if self.b_vet.isChecked() else QFont.Weight.Normal)
        self._merge(f)

    def _cursief(self):
        f = QTextCharFormat(); f.setFontItalic(self.b_cur.isChecked()); self._merge(f)

    def _onderstreept(self):
        f = QTextCharFormat(); f.setFontUnderline(self.b_ond.isChecked()); self._merge(f)

    def _zet_font(self, naam):
        f = QTextCharFormat(); f.setFontFamily(naam); self._merge(f)

    def _zet_grootte(self, tekst):
        try:
            pt = float(tekst)
        except ValueError:
            return
        f = QTextCharFormat(); f.setFontPointSize(pt); self._merge(f)

    def _kleur(self):
        c = QColorDialog.getColor(QColor("#d4d4d4"), self, T("kleur"))
        if c.isValid():
            f = QTextCharFormat(); f.setForeground(c); self._merge(f)

    def _uitlijn(self, vlag):
        self.editor.setAlignment(vlag); self.editor.setFocus()

    def _lijst(self, stijl):
        cur = self.editor.textCursor()
        lf = QTextListFormat(); lf.setStyle(stijl)
        cur.createList(lf); self.editor.setFocus()

    def _zet_kop(self, idx):
        groottes = {0: 12, 1: 24, 2: 18}
        vet = idx in (1, 2)
        f = QTextCharFormat()
        f.setFontPointSize(groottes.get(idx, 12))
        f.setFontWeight(QFont.Weight.Bold if vet else QFont.Weight.Normal)
        cur = self.editor.textCursor()
        cur.select(QTextCursor.SelectionType.LineUnderCursor)
        cur.mergeCharFormat(f)
        self.editor.setFocus()

    def _sync_opmaak(self, fmt):
        self.b_vet.setChecked(fmt.fontWeight() >= QFont.Weight.Bold)
        self.b_cur.setChecked(fmt.fontItalic())
        self.b_ond.setChecked(fmt.fontUnderline())
        fam = fmt.font().family()
        if fam:
            self.font_combo.blockSignals(True)
            self.font_combo.setCurrentFont(QFont(fam))
            self.font_combo.blockSignals(False)
        pt = fmt.fontPointSize()
        if pt and pt > 0:
            self.size_combo.blockSignals(True)
            self.size_combo.setCurrentText(str(int(pt)))
            self.size_combo.blockSignals(False)

    def _tel(self):
        tekst = self.editor.toPlainText()
        woorden = len([w for w in tekst.split() if w.strip()])
        self.tel_label.setText(T("woorden", w=woorden, t=len(tekst)))

    # ---- invoegen vanuit rekenmachine ----
    def voeg_tekst_in(self, tekst):
        cur = self.editor.textCursor()
        cur.insertText(tekst)
        self.editor.setFocus()

    # ---- bestand ----
    def _bevestig_verlies(self):
        if not self.editor.document().isModified():
            return True
        vr = QMessageBox(self)
        vr.setWindowTitle(T("niet_opgeslagen")); vr.setText(T("bewaren_vraag"))
        vr.setIcon(QMessageBox.Icon.Question)
        vr.setStandardButtons(QMessageBox.StandardButton.Save |
                              QMessageBox.StandardButton.Discard |
                              QMessageBox.StandardButton.Cancel)
        keuze = vr.exec()
        if keuze == QMessageBox.StandardButton.Save:
            return self.opslaan()
        return keuze == QMessageBox.StandardButton.Discard

    def nieuw(self):
        if not self._bevestig_verlies():
            return
        self.editor.clear()
        self.huidig_pad = None
        self.editor.document().setModified(False)
        self.status_signaal.emit(T("naamloos"))

    def openen(self):
        if not self._bevestig_verlies():
            return
        filter_ = ("Documenten (*.txt *.html *.htm *.docx *.odt);;"
                   "Tekst (*.txt);;HTML (*.html *.htm);;Word (*.docx);;"
                   "OpenDocument (*.odt);;Alle bestanden (*)")
        pad, _ = QFileDialog.getOpenFileName(self, T("openen"), DATA_MAP, filter_)
        if not pad:
            return
        try:
            self._laad(pad)
            self.huidig_pad = pad
            self.editor.document().setModified(False)
            self.status_signaal.emit(T("geopend", p=os.path.basename(pad)))
        except Exception as e:
            QMessageBox.critical(self, T("fout"), T("kon_niet_openen", e=str(e)))

    def _laad(self, pad):
        ext = os.path.splitext(pad)[1].lower()
        if ext in (".txt",):
            with open(pad, "r", encoding="utf-8", errors="replace") as f:
                self.editor.setPlainText(f.read())
        elif ext in (".html", ".htm"):
            with open(pad, "r", encoding="utf-8", errors="replace") as f:
                self.editor.setHtml(f.read())
        elif ext == ".docx":
            self.editor.setHtml(docx_naar_html(pad))
        elif ext == ".odt":
            self.editor.setHtml(odt_naar_html(pad))
        else:
            with open(pad, "r", encoding="utf-8", errors="replace") as f:
                self.editor.setPlainText(f.read())

    def opslaan(self):
        if self.huidig_pad is None:
            return self.opslaan_als()
        return self._bewaar(self.huidig_pad)

    def opslaan_als(self):
        filter_ = ("Tekst (*.txt);;HTML (*.html);;OpenDocument (*.odt);;"
                   "Word (*.docx);;PDF (*.pdf)")
        pad, gekozen = QFileDialog.getSaveFileName(self, T("opslaan_als"), DATA_MAP, filter_)
        if not pad:
            return False
        if "." not in os.path.basename(pad):
            ext = {"Tekst (*.txt)": ".txt", "HTML (*.html)": ".html",
                   "OpenDocument (*.odt)": ".odt", "Word (*.docx)": ".docx",
                   "PDF (*.pdf)": ".pdf"}.get(gekozen, ".txt")
            pad += ext
        ok = self._bewaar(pad)
        if ok:
            self.huidig_pad = pad
        return ok

    def _bewaar(self, pad):
        ext = os.path.splitext(pad)[1].lower()
        try:
            if ext == ".txt":
                with open(pad, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
            elif ext in (".html", ".htm"):
                with open(pad, "w", encoding="utf-8") as f:
                    f.write(self.editor.toHtml())
            elif ext == ".odt":
                schrijver = QTextDocumentWriter(pad)
                schrijver.setFormat(b"ODF")
                schrijver.write(self.editor.document())
            elif ext == ".pdf":
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(pad)
                self.editor.document().print(printer)
            elif ext == ".docx":
                html_naar_docx(self.editor.document(), pad)
            else:
                with open(pad, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
            self.editor.document().setModified(False)
            self.status_signaal.emit(T("opgeslagen", p=os.path.basename(pad)))
            return True
        except Exception as e:
            QMessageBox.critical(self, T("fout"), T("kon_niet_opslaan", e=str(e)))
            return False


# ---- formaat-helpers ----
def docx_naar_html(pad):
    import docx
    d = docx.Document(pad)
    delen = ["<html><body>"]
    for p in d.paragraphs:
        stukjes = []
        for run in p.runs:
            t = (run.text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if not t:
                continue
            if run.bold:
                t = "<b>%s</b>" % t
            if run.italic:
                t = "<i>%s</i>" % t
            if run.underline:
                t = "<u>%s</u>" % t
            stukjes.append(t)
        regel = "".join(stukjes) or "&nbsp;"
        uitlijn = ""
        try:
            al = p.alignment
            if al is not None:
                uitlijn = {0: "left", 1: "center", 2: "right", 3: "justify"}.get(int(al), "")
        except Exception:
            uitlijn = ""
        stijl = (' style="text-align:%s;"' % uitlijn) if uitlijn else ""
        delen.append("<p%s>%s</p>" % (stijl, regel))
    delen.append("</body></html>")
    return "".join(delen)


def odt_naar_html(pad):
    from odf.opendocument import load
    from odf import text as odftext, teletype
    doc = load(pad)
    delen = ["<html><body>"]
    for para in doc.getElementsByType(odftext.P):
        inhoud = teletype.extractText(para)
        inhoud = inhoud.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        delen.append("<p>%s</p>" % (inhoud or "&nbsp;"))
    delen.append("</body></html>")
    return "".join(delen)


def html_naar_docx(qdoc, pad):
    import docx
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    # 1) lees alles uit Qt in gewone waarden (geen Qt-aanroepen meer tijdens docx-bouw)
    blokken = []
    blok = qdoc.begin()
    while blok.isValid():
        al = int(blok.blockFormat().alignment())
        runs = []
        it = blok.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                cf = frag.charFormat()
                kleur = None
                br = cf.foreground()
                if br.style() != Qt.BrushStyle.NoBrush:
                    c = br.color(); kleur = (c.red(), c.green(), c.blue())
                runs.append({
                    "t": frag.text(),
                    "b": cf.fontWeight() >= QFont.Weight.Bold,
                    "i": cf.fontItalic(),
                    "u": cf.fontUnderline(),
                    "fam": cf.font().family(),
                    "pt": cf.fontPointSize(),
                    "kl": kleur,
                })
            it += 1
        if not runs:
            runs = [{"t": blok.text(), "b": False, "i": False, "u": False,
                     "fam": "", "pt": 0, "kl": None}]
        blokken.append((al, runs))
        blok = blok.next()
    # 2) bouw het docx-document
    amap = {1: WD_ALIGN_PARAGRAPH.LEFT, 2: WD_ALIGN_PARAGRAPH.RIGHT,
            4: WD_ALIGN_PARAGRAPH.CENTER, 8: WD_ALIGN_PARAGRAPH.JUSTIFY}
    out = docx.Document()
    for al, runs in blokken:
        para = out.add_paragraph()
        for vlag, waarde in amap.items():
            if al & vlag:
                para.alignment = waarde
                break
        for r in runs:
            run = para.add_run(r["t"])
            run.bold = r["b"]; run.italic = r["i"]; run.underline = r["u"]
            if r["fam"]:
                run.font.name = r["fam"]
            if r["pt"] and r["pt"] > 0:
                run.font.size = Pt(r["pt"])
            if r["kl"]:
                run.font.color.rgb = RGBColor(*r["kl"])
    out.save(pad)


# ======================================================================
# Rekenmachine
# ======================================================================
TOEGESTANE_FUNCS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sqrt": math.sqrt, "log": math.log10, "ln": math.log,
    "exp": math.exp, "abs": abs, "round": round,
    "floor": math.floor, "ceil": math.ceil, "fact": math.factorial,
    "rad": math.radians, "deg": math.degrees, "pow": math.pow,
}
TOEGESTANE_NAMEN = {"pi": math.pi, "e": math.e, "tau": math.tau}


def veilig_eval(expr):
    expr = (expr.replace("\u00d7", "*").replace("\u00f7", "/")
            .replace("\u2212", "-").replace("^", "**").replace(",", "."))
    knoop = ast.parse(expr, mode="eval")

    def loop(n):
        if isinstance(n, ast.Expression):
            return loop(n.body)
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, float)):
                return n.value
            raise ValueError("ongeldig")
        if isinstance(n, ast.BinOp):
            a, b = loop(n.left), loop(n.right)
            op = n.op
            if isinstance(op, ast.Add): return a + b
            if isinstance(op, ast.Sub): return a - b
            if isinstance(op, ast.Mult): return a * b
            if isinstance(op, ast.Div): return a / b
            if isinstance(op, ast.Pow): return a ** b
            if isinstance(op, ast.Mod): return a % b
            if isinstance(op, ast.FloorDiv): return a // b
            raise ValueError("operator")
        if isinstance(n, ast.UnaryOp):
            v = loop(n.operand)
            if isinstance(n.op, ast.UAdd): return +v
            if isinstance(n.op, ast.USub): return -v
            raise ValueError("unair")
        if isinstance(n, ast.Call):
            if not isinstance(n.func, ast.Name) or n.func.id not in TOEGESTANE_FUNCS:
                raise ValueError("functie")
            args = [loop(a) for a in n.args]
            return TOEGESTANE_FUNCS[n.func.id](*args)
        if isinstance(n, ast.Name):
            if n.id in TOEGESTANE_NAMEN:
                return TOEGESTANE_NAMEN[n.id]
            raise ValueError("naam")
        raise ValueError("ongeldig")
    return loop(knoop)


class Rekenmachine(QWidget):
    invoegen = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._net_gelijk = False
        buiten = QVBoxLayout(self)
        buiten.setContentsMargins(14, 12, 14, 12); buiten.setSpacing(8)
        # ---- scherm ----
        self.overzicht = QLabel("")
        self.overzicht.setStyleSheet("font-size:16px; color:%s; padding:1px 6px;" % MUTED)
        self.overzicht.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.overzicht.setMinimumHeight(22)
        self.invoer = QLineEdit(); self.invoer.setPlaceholderText("0")
        self.invoer.setStyleSheet("font-size:30px; padding:10px; font-weight:bold;")
        self.invoer.setMinimumHeight(58)
        self.invoer.returnPressed.connect(self._isgelijk)
        self.invoer.textChanged.connect(self._preview)
        self.invoer.textEdited.connect(self._handmatig)
        self.uitkomst = QLabel("")
        self.uitkomst.setStyleSheet("font-size:16px; color:%s; padding:1px 6px;" % MUTED)
        self.uitkomst.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.uitkomst.setMinimumHeight(22)
        buiten.addWidget(self.overzicht)
        buiten.addWidget(self.invoer)
        buiten.addWidget(self.uitkomst)
        # ---- knoppen: twee aparte vakken ----
        vakken = QHBoxLayout(); vakken.setSpacing(12)
        vakken.addWidget(self._standaard_vak())
        vakken.addWidget(self._wet_vak())
        buiten.addLayout(vakken)
        # ---- invoegen ----
        invoeg = QPushButton(T("invoegen_doc")); invoeg.setObjectName("primair")
        invoeg.setMinimumHeight(42); invoeg.clicked.connect(self._invoegen)
        buiten.addWidget(invoeg)
        # ---- geschiedenis (compact) ----
        gl = QLabel(T("geschiedenis")); gl.setStyleSheet("font-weight:bold; font-size:13px;")
        self.hist = QListWidget(); self.hist.setMaximumHeight(90)
        self.hist.itemClicked.connect(self._uit_geschiedenis)
        buiten.addWidget(gl); buiten.addWidget(self.hist)

    def _vak(self, titel):
        box = QFrame(); box.setObjectName("vak")
        box.setStyleSheet("QFrame#vak{background:%s; border:1px solid %s; border-radius:10px;}"
                          % (PANEEL, LINE))
        v = QVBoxLayout(box); v.setContentsMargins(10, 8, 10, 10); v.setSpacing(6)
        kop = QLabel(titel)
        kop.setStyleSheet("font-size:13px; font-weight:bold; color:%s; border:none;" % MUTED)
        v.addWidget(kop)
        g = QGridLayout(); g.setSpacing(6); v.addLayout(g)
        return box, g

    def _standaard_vak(self):
        box, g = self._vak(T("standaard"))
        rijen = [
            [("1", "1", None), ("2", "2", None), ("3", "3", None), ("\u00f7", "\u00f7", T("tt_delen"))],
            [("4", "4", None), ("5", "5", None), ("6", "6", None), ("\u00d7", "\u00d7", T("tt_keer"))],
            [("7", "7", None), ("8", "8", None), ("9", "9", None), ("\u2212", "\u2212", T("tt_min"))],
            [("0", "0", None), (".", ".", T("tt_komma")), ("%", "%", T("tt_procent")),
             ("+", "+", T("tt_plus"))],
        ]
        for r, rij in enumerate(rijen):
            for c, (lbl, ins, tip) in enumerate(rij):
                g.addWidget(self._kb(lbl, (lambda s=ins: self._voeg(s)), tip=tip), r, c)
        g.addWidget(self._kb(T("wis"), self._wis, "gevaar", T("tt_wis")), 4, 0)
        g.addWidget(self._kb("\u232b", self._backspace, tip=T("tt_backspace")), 4, 1)
        g.addWidget(self._kb("=", self._isgelijk, "primair", T("tt_isgelijk")), 4, 2, 1, 2)
        return box

    def _wet_vak(self):
        box, g = self._vak(T("wetenschappelijk"))
        wet = [
            ("sin", "sin(", T("tt_sin")), ("cos", "cos(", T("tt_cos")), ("tan", "tan(", T("tt_tan")),
            ("\u221a", "sqrt(", T("tt_sqrt")), ("ln", "ln(", T("tt_ln")), ("log", "log(", T("tt_log")),
            ("x\u02b8", "^", T("tt_pow")), ("x\u00b2", "^2", T("tt_kwad")), ("\u03c0", "pi", T("tt_pi")),
            ("(", "(", T("tt_haak_open")), (")", ")", T("tt_haak_dicht")), ("e", "e", T("tt_e")),
        ]
        for i, (lbl, ins, tip) in enumerate(wet):
            g.addWidget(self._kb(lbl, (lambda s=ins: self._voeg(s)), tip=tip), i // 3, i % 3)
        return box

    def _kb(self, tekst, fn=None, obj=None, tip=None):
        b = QPushButton(tekst); b.setMinimumSize(QSize(58, 48))
        b.setStyleSheet("font-size:18px;")
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        if tip:
            b.setToolTip(tip); b.setStatusTip(tip)
        if obj:
            b.setObjectName(obj)
        actie = fn or (lambda: self._voeg(tekst))
        b.clicked.connect(lambda *_a, a=actie: a())
        return b

    def _uit_geschiedenis(self, it):
        self._net_gelijk = False
        self.overzicht.setText("")
        self.invoer.setText(it.text().split("=")[0].strip())

    def _voeg(self, s):
        if self._net_gelijk:
            self._net_gelijk = False
            self.overzicht.setText("")
            if s[:1] not in "+-\u00d7\u00f7*/^%)":
                self.invoer.blockSignals(True); self.invoer.clear(); self.invoer.blockSignals(False)
        self.invoer.setText(self.invoer.text() + s)
        self.invoer.setFocus()

    def _wis(self):
        self._net_gelijk = False
        self.invoer.clear(); self.uitkomst.clear(); self.overzicht.clear()

    def _backspace(self):
        self._net_gelijk = False
        self.invoer.setText(self.invoer.text()[:-1])

    def _handmatig(self, _tekst):
        self._net_gelijk = False
        self.overzicht.setText("")

    def _preview(self, _tekst=None):
        if self._net_gelijk:
            return
        expr = self.invoer.text().strip()
        if not expr:
            self.uitkomst.setText(""); return
        try:
            res = veilig_eval(expr)
            self.uitkomst.setText("= " + self._fmt_uitkomst(res))
        except Exception:
            self.uitkomst.setText("")

    def _isgelijk(self):
        expr = self.invoer.text().strip()
        if not expr:
            return
        try:
            res = veilig_eval(expr)
            tekst = self._fmt_uitkomst(res)
            self.overzicht.setText("%s = %s" % (expr, tekst))
            self.hist.insertItem(0, "%s = %s" % (expr, tekst))
            self._laatste = tekst
            self.invoer.blockSignals(True)
            self.invoer.setText(tekst)
            self.invoer.blockSignals(False)
            self.uitkomst.setText("")
            self._net_gelijk = True
        except Exception:
            self.uitkomst.setText(T("reken_fout"))

    def _fmt_uitkomst(self, res):
        if isinstance(res, float):
            if res.is_integer():
                return str(int(res))
            # max ~10 betekenisvolle cijfers, geen lange staart, komma als decimaalteken
            return ("%.10g" % res).replace(".", ",")
        return str(res)

    def _invoegen(self):
        expr = self.invoer.text().strip()
        res = getattr(self, "_laatste", None)
        if not expr:
            return
        if res is None:
            try:
                res = self._fmt_uitkomst(veilig_eval(expr))
            except Exception:
                self.uitkomst.setText(T("reken_fout")); return
        self.invoegen.emit("%s = %s" % (expr, res))


# ======================================================================
# Omrekenen (maten, gewichten, BTW, procent...)
# ======================================================================
CONV = {
    "lengte": {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
               "inch": 0.0254, "voet": 0.3048, "yard": 0.9144, "mijl": 1609.344},
    "oppervlakte": {"mm2": 1e-6, "cm2": 1e-4, "m2": 1.0, "km2": 1e6,
                    "are": 100.0, "hectare": 10000.0, "voet2": 0.092903,
                    "acre": 4046.8564},
    "volume": {"ml": 0.001, "cl": 0.01, "dl": 0.1, "liter": 1.0, "m3": 1000.0,
               "theelepel": 0.00492892, "eetlepel": 0.0147868, "cup": 0.236588,
               "pint": 0.473176, "gallon": 3.785412, "fl oz": 0.0295735},
    "gewicht": {"mg": 1e-6, "g": 0.001, "kg": 1.0, "ton": 1000.0,
                "ounce": 0.0283495, "pound": 0.453592, "stone": 6.35029},
    "snelheid": {"m/s": 1.0, "km/h": 0.277778, "mph": 0.44704, "knoop": 0.514444},
    "tijd": {"seconde": 1.0, "minuut": 60.0, "uur": 3600.0, "dag": 86400.0, "week": 604800.0},
    "data": {"byte": 1.0, "KB": 1024.0, "MB": 1048576.0, "GB": 1073741824.0,
             "TB": 1099511627776.0},
    "energie": {"J": 1.0, "kJ": 1000.0, "cal": 4.184, "kcal": 4184.0,
                "Wh": 3600.0, "kWh": 3600000.0, "BTU": 1055.06},
    "druk": {"Pa": 1.0, "hPa": 100.0, "kPa": 1000.0, "bar": 100000.0,
             "atm": 101325.0, "psi": 6894.757, "mmHg": 133.322},
    "vermogen": {"W": 1.0, "kW": 1000.0, "pk": 735.499, "hp": 745.7},
    "hoek": {"graden": 0.0174533, "radiaal": 1.0, "gon": 0.015708},
}
TEMP_EENHEDEN = ["Celsius", "Fahrenheit", "Kelvin"]


def fmt_getal(x):
    if isinstance(x, float):
        if x.is_integer():
            return str(int(x))
        s = ("%.6g" % x)
        return s
    return str(x)


def euro(x):
    return ("%.2f" % x).replace(".", ",")


def reken_temp(van, naar, w):
    if van == "Celsius":
        c = w
    elif van == "Fahrenheit":
        c = (w - 32) * 5.0 / 9.0
    else:
        c = w - 273.15
    if naar == "Celsius":
        return c
    if naar == "Fahrenheit":
        return c * 9.0 / 5.0 + 32
    return c + 273.15


class Omrekenen(QWidget):
    """Algemene omrekenmodule: kies een categorie, van/naar eenheid en waarde."""
    invoegen = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.categorie = "lengte"
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(12)
        self.titel = QLabel(""); self.titel.setStyleSheet("font-size:20px; font-weight:bold;")
        lay.addWidget(self.titel)
        # waarde
        rij1 = QHBoxLayout()
        lbl = QLabel(T("waarde")); lbl.setStyleSheet("font-size:16px;"); lbl.setMinimumWidth(90)
        self.waarde = QLineEdit("1"); self.waarde.setStyleSheet("font-size:20px; padding:10px;")
        self.waarde.setMinimumHeight(48)
        self.waarde.textChanged.connect(self._reken)
        rij1.addWidget(lbl); rij1.addWidget(self.waarde, 1)
        lay.addLayout(rij1)
        # van
        rij2 = QHBoxLayout()
        lv = QLabel(T("van")); lv.setStyleSheet("font-size:16px;"); lv.setMinimumWidth(90)
        self.van = QComboBox(); self.van.setMinimumHeight(46)
        self.van.setStyleSheet("font-size:17px;")
        self.van.currentIndexChanged.connect(self._reken)
        rij2.addWidget(lv); rij2.addWidget(self.van, 1)
        lay.addLayout(rij2)
        # wissel
        wissel = QPushButton("\u21c5  " + T("wissel"))
        wissel.setMinimumHeight(40); wissel.setToolTip(T("tip_wissel"))
        wissel.setCursor(Qt.CursorShape.PointingHandCursor)
        wissel.clicked.connect(self._wissel)
        lay.addWidget(wissel)
        # naar
        rij3 = QHBoxLayout()
        ln = QLabel(T("naar")); ln.setStyleSheet("font-size:16px;"); ln.setMinimumWidth(90)
        self.naar = QComboBox(); self.naar.setMinimumHeight(46)
        self.naar.setStyleSheet("font-size:17px;")
        self.naar.currentIndexChanged.connect(self._reken)
        rij3.addWidget(ln); rij3.addWidget(self.naar, 1)
        lay.addLayout(rij3)
        # resultaat
        self.resultaat = QLabel("")
        self.resultaat.setStyleSheet("font-size:26px; font-weight:bold; color:%s; padding:10px;" % ACCENT)
        self.resultaat.setMinimumHeight(56)
        lay.addWidget(self.resultaat)
        invoeg = QPushButton(T("invoegen_doc")); invoeg.setObjectName("primair")
        invoeg.setMinimumHeight(44); invoeg.clicked.connect(self._invoeg)
        lay.addWidget(invoeg)
        lay.addStretch(1)

    def zet_categorie(self, cat, titel):
        self.categorie = cat
        self.titel.setText(titel)
        if cat == "temperatuur":
            eenheden = TEMP_EENHEDEN
        else:
            eenheden = list(CONV[cat].keys())
        for combo in (self.van, self.naar):
            combo.blockSignals(True); combo.clear(); combo.addItems(eenheden)
            combo.blockSignals(False)
        self.van.setCurrentIndex(0)
        self.naar.setCurrentIndex(min(1, len(eenheden) - 1))
        self._reken()

    def _wissel(self):
        a, b = self.van.currentIndex(), self.naar.currentIndex()
        self.van.setCurrentIndex(b); self.naar.setCurrentIndex(a)

    def _huidige(self):
        try:
            w = float(self.waarde.text().replace(",", "."))
        except ValueError:
            return None
        van = self.van.currentText(); naar = self.naar.currentText()
        if not van or not naar:
            return None
        if self.categorie == "temperatuur":
            res = reken_temp(van, naar, w)
        else:
            f = CONV[self.categorie]
            res = w * f[van] / f[naar]
        return w, van, naar, res

    def _reken(self):
        h = self._huidige()
        if h is None:
            self.resultaat.setText("-"); return
        w, van, naar, res = h
        self.resultaat.setText("%s %s  =  %s %s" % (fmt_getal(w), van, fmt_getal(res), naar))

    def _invoeg(self):
        h = self._huidige()
        if h is None:
            return
        w, van, naar, res = h
        self.invoegen.emit("%s %s = %s %s" % (fmt_getal(w), van, fmt_getal(res), naar))


class BtwModule(QWidget):
    invoegen = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(12)
        t = QLabel(T("btw")); t.setStyleSheet("font-size:20px; font-weight:bold;")
        lay.addWidget(t)
        rij1 = QHBoxLayout()
        l1 = QLabel(T("bedrag")); l1.setMinimumWidth(120); l1.setStyleSheet("font-size:16px;")
        self.bedrag = QLineEdit("100"); self.bedrag.setMinimumHeight(48)
        self.bedrag.setStyleSheet("font-size:20px; padding:10px;")
        self.bedrag.textChanged.connect(self._reken)
        rij1.addWidget(l1); rij1.addWidget(self.bedrag, 1)
        lay.addLayout(rij1)
        rij2 = QHBoxLayout()
        l2 = QLabel(T("btw_tarief")); l2.setMinimumWidth(120); l2.setStyleSheet("font-size:16px;")
        self.tarief = QComboBox(); self.tarief.addItems(["21", "9", "0", "6", "19", "25"])
        self.tarief.setEditable(True); self.tarief.setMinimumHeight(46)
        self.tarief.setStyleSheet("font-size:17px;")
        self.tarief.currentTextChanged.connect(self._reken)
        rij2.addWidget(l2); rij2.addWidget(self.tarief, 1)
        lay.addLayout(rij2)
        rij3 = QHBoxLayout()
        l3 = QLabel(T("bedrag_is")); l3.setMinimumWidth(120); l3.setStyleSheet("font-size:16px;")
        self.soort = QComboBox(); self.soort.addItems([T("excl_btw"), T("incl_btw")])
        self.soort.setMinimumHeight(46); self.soort.setStyleSheet("font-size:17px;")
        self.soort.currentIndexChanged.connect(self._reken)
        rij3.addWidget(l3); rij3.addWidget(self.soort, 1)
        lay.addLayout(rij3)
        # uitsplitsing (excl + btw)
        self.uit = QLabel("")
        self.uit.setStyleSheet("font-size:17px; color:%s; padding:6px 4px; line-height:1.6;" % TEKST)
        self.uit.setWordWrap(True)
        lay.addWidget(self.uit)
        # totaal groot en duidelijk
        self.totaal = QLabel("")
        self.totaal.setStyleSheet("font-size:26px; font-weight:bold; color:%s; "
                                  "padding:10px; background:%s; border-radius:8px;" % (ACCENT, PANEEL))
        self.totaal.setMinimumHeight(56); self.totaal.setWordWrap(True)
        lay.addWidget(self.totaal)
        invoeg = QPushButton(T("invoegen_doc")); invoeg.setObjectName("primair")
        invoeg.setMinimumHeight(44); invoeg.clicked.connect(self._invoeg)
        lay.addWidget(invoeg)
        lay.addStretch(1)
        self._reken()

    def _bereken(self):
        try:
            bedrag = float(self.bedrag.text().replace(",", "."))
            tarief = float(self.tarief.currentText().replace(",", "."))
        except ValueError:
            return None
        if self.soort.currentIndex() == 0:  # excl
            excl = bedrag
            btw = excl * tarief / 100.0
            incl = excl + btw
        else:  # incl
            incl = bedrag
            excl = incl / (1 + tarief / 100.0)
            btw = incl - excl
        return excl, btw, incl, tarief

    def _reken(self):
        r = self._bereken()
        if r is None:
            self.uit.setText("-"); self.totaal.setText(""); return
        excl, btw, incl, tarief = r
        self.uit.setText("%s: \u20ac %s\n%s (%s%%): \u20ac %s" % (
            T("excl_btw"), euro(excl), T("btw"), fmt_getal(tarief), euro(btw)))
        self.totaal.setText("%s: \u20ac %s" % (T("totaal_incl"), euro(incl)))

    def _invoeg(self):
        r = self._bereken()
        if r is None:
            return
        excl, btw, incl, tarief = r
        self.invoegen.emit("%s: \u20ac %s  |  %s %s%%: \u20ac %s  |  %s: \u20ac %s" % (
            T("excl_btw"), euro(excl), T("btw"), fmt_getal(tarief), euro(btw),
            T("totaal_incl"), euro(incl)))


class ProcentModule(QWidget):
    invoegen = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(10)
        t = QLabel(T("procent")); t.setStyleSheet("font-size:20px; font-weight:bold;")
        lay.addWidget(t)
        # X% van Y
        self.a1 = QLineEdit("10"); self.a2 = QLineEdit("250")
        self._rij(lay, T("p_van_1"), self.a1, T("p_van_2"), self.a2)
        self.r1 = self._res(lay)
        # X is welk % van Y
        self.b1 = QLineEdit("30"); self.b2 = QLineEdit("120")
        self._rij(lay, T("p_welk_1"), self.b1, T("p_welk_2"), self.b2)
        self.r2 = self._res(lay)
        # toename/afname van X naar Y
        self.c1 = QLineEdit("80"); self.c2 = QLineEdit("100")
        self._rij(lay, T("p_groei_1"), self.c1, T("p_groei_2"), self.c2)
        self.r3 = self._res(lay)
        for e in (self.a1, self.a2, self.b1, self.b2, self.c1, self.c2):
            e.textChanged.connect(self._reken)
        lay.addStretch(1)
        self._reken()

    def _rij(self, lay, t1, e1, t2, e2):
        rij = QHBoxLayout()
        l1 = QLabel(t1); l1.setStyleSheet("font-size:16px;")
        e1.setMinimumHeight(42); e1.setStyleSheet("font-size:17px; padding:6px;"); e1.setMaximumWidth(120)
        l2 = QLabel(t2); l2.setStyleSheet("font-size:16px;")
        e2.setMinimumHeight(42); e2.setStyleSheet("font-size:17px; padding:6px;"); e2.setMaximumWidth(120)
        rij.addWidget(l1); rij.addWidget(e1); rij.addWidget(l2); rij.addWidget(e2); rij.addStretch(1)
        lay.addLayout(rij)

    def _res(self, lay):
        lb = QLabel("")
        lb.setStyleSheet("font-size:20px; font-weight:bold; color:%s; padding:2px 4px;" % ACCENT)
        lay.addWidget(lb)
        return lb

    def _f(self, e):
        try:
            return float(e.text().replace(",", "."))
        except ValueError:
            return None

    def _reken(self):
        a1, a2 = self._f(self.a1), self._f(self.a2)
        if a1 is not None and a2 is not None:
            self.r1.setText("= %s" % fmt_getal(a1 * a2 / 100.0))
        b1, b2 = self._f(self.b1), self._f(self.b2)
        if b1 is not None and b2 not in (None, 0):
            self.r2.setText("= %s%%" % fmt_getal(b1 / b2 * 100.0))
        c1, c2 = self._f(self.c1), self._f(self.c2)
        if c1 not in (None, 0) and c2 is not None:
            self.r3.setText("= %s%%" % fmt_getal((c2 - c1) / c1 * 100.0))


class RekenCentrum(QWidget):
    """Rekenmachine + omrekenmodules onder een keuzemenu."""
    invoegen = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 12, 16, 12); lay.setSpacing(10)
        boven = QHBoxLayout()
        kies = QLabel(T("kies_reken")); kies.setStyleSheet("font-size:16px;")
        self.modus = QComboBox(); self.modus.setMinimumHeight(46)
        self.modus.setStyleSheet("font-size:17px; padding:4px 10px;")
        self._modi = [
            ("rekenmachine", None), ("lengte", "lengte"), ("oppervlakte", "oppervlakte"),
            ("volume", "volume"), ("gewicht", "gewicht"), ("temperatuur", "temperatuur"),
            ("snelheid", "snelheid"), ("tijd", "tijd"), ("data", "data"),
            ("energie", "energie"), ("druk", "druk"), ("vermogen", "vermogen"),
            ("hoek", "hoek"), ("btw", "btw"), ("procent", "procent"),
            ("getalstelsel", "getalstelsel"), ("valuta", "valuta"),
        ]
        self.modus.addItems([T(s) for s, _ in self._modi])
        self.modus.currentIndexChanged.connect(self._wissel_modus)
        boven.addWidget(kies); boven.addWidget(self.modus, 1)
        lay.addLayout(boven)

        self.stack = QStackedWidget()
        self.calc = Rekenmachine()
        self.omreken = Omrekenen()
        self.btw = BtwModule()
        self.procent = ProcentModule()
        self.getalstelsel = GetalstelselModule()
        self.valuta = ValutaModule()
        for w in (self.calc, self.omreken, self.btw, self.procent,
                  self.getalstelsel, self.valuta):
            self.stack.addWidget(w)
            w.invoegen.connect(self.invoegen)
        lay.addWidget(self.stack, 1)

    def _wissel_modus(self, idx):
        sleutel, cat = self._modi[idx]
        if sleutel == "rekenmachine":
            self.stack.setCurrentWidget(self.calc)
        elif sleutel == "btw":
            self.stack.setCurrentWidget(self.btw)
        elif sleutel == "procent":
            self.stack.setCurrentWidget(self.procent)
        elif sleutel == "getalstelsel":
            self.stack.setCurrentWidget(self.getalstelsel)
        elif sleutel == "valuta":
            self.stack.setCurrentWidget(self.valuta)
        else:
            self.omreken.zet_categorie(cat, T(sleutel))
            self.stack.setCurrentWidget(self.omreken)


class GetalstelselModule(QWidget):
    invoegen = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(12)
        t = QLabel(T("getalstelsel")); t.setStyleSheet("font-size:20px; font-weight:bold;")
        lay.addWidget(t)
        rij = QHBoxLayout()
        lw = QLabel(T("waarde")); lw.setMinimumWidth(90); lw.setStyleSheet("font-size:16px;")
        self.waarde = QLineEdit("255"); self.waarde.setMinimumHeight(48)
        self.waarde.setStyleSheet("font-size:20px; padding:10px;")
        self.waarde.textChanged.connect(self._reken)
        rij.addWidget(lw); rij.addWidget(self.waarde, 1)
        lay.addLayout(rij)
        rij2 = QHBoxLayout()
        lv = QLabel(T("van")); lv.setMinimumWidth(90); lv.setStyleSheet("font-size:16px;")
        self.van = QComboBox(); self.van.addItems([T("decimaal"), T("binair"),
                                                   T("hex"), T("octaal")])
        self.van.setMinimumHeight(46); self.van.setStyleSheet("font-size:17px;")
        self.van.currentIndexChanged.connect(self._reken)
        rij2.addWidget(lv); rij2.addWidget(self.van, 1)
        lay.addLayout(rij2)
        self.uit = QLabel("")
        self.uit.setStyleSheet("font-size:19px; color:%s; padding:10px; line-height:1.7;" % ACCENT)
        self.uit.setMinimumHeight(140); self.uit.setWordWrap(True)
        lay.addWidget(self.uit)
        invoeg = QPushButton(T("invoegen_doc")); invoeg.setObjectName("primair")
        invoeg.setMinimumHeight(44); invoeg.clicked.connect(self._invoeg)
        lay.addWidget(invoeg); lay.addStretch(1)
        self._reken()

    def _waarde(self):
        grondtal = {0: 10, 1: 2, 2: 16, 3: 8}[self.van.currentIndex()]
        try:
            return int(self.waarde.text().strip(), grondtal)
        except ValueError:
            return None

    def _reken(self):
        n = self._waarde()
        if n is None:
            self.uit.setText(T("ongeldig_getal")); return
        self.uit.setText("%s: %d\n%s: %s\n%s: %s\n%s: %s" % (
            T("decimaal"), n, T("binair"), bin(n)[2:],
            T("hex"), hex(n)[2:].upper(), T("octaal"), oct(n)[2:]))

    def _invoeg(self):
        n = self._waarde()
        if n is None:
            return
        self.invoegen.emit("%d (dec) = %s (bin) = %s (hex)" % (n, bin(n)[2:], hex(n)[2:].upper()))


class ValutaModule(QWidget):
    invoegen = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.koersen = {}
        self.koers_datum = None
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(12)
        t = QLabel(T("valuta")); t.setStyleSheet("font-size:20px; font-weight:bold;")
        lay.addWidget(t)
        waarschuw = QLabel("\u26a0  " + T("internet_waarschuwing"))
        waarschuw.setStyleSheet("background:%s; color:#1a1a1a; font-weight:bold; "
                                "padding:10px; border-radius:8px; font-size:15px;" % WARN)
        waarschuw.setWordWrap(True)
        lay.addWidget(waarschuw)
        self.ophaal = QPushButton(T("koersen_ophalen"))
        self.ophaal.setMinimumHeight(44); self.ophaal.clicked.connect(self._ophalen)
        lay.addWidget(self.ophaal)
        self.koers_label = QLabel(T("nog_geen_koersen"))
        self.koers_label.setStyleSheet("color:%s; font-size:14px;" % MUTED)
        lay.addWidget(self.koers_label)
        rij = QHBoxLayout()
        lw = QLabel(T("bedrag")); lw.setMinimumWidth(90); lw.setStyleSheet("font-size:16px;")
        self.bedrag = QLineEdit("100"); self.bedrag.setMinimumHeight(48)
        self.bedrag.setStyleSheet("font-size:20px; padding:10px;")
        self.bedrag.textChanged.connect(self._reken)
        rij.addWidget(lw); rij.addWidget(self.bedrag, 1)
        lay.addLayout(rij)
        rij2 = QHBoxLayout()
        lv = QLabel(T("van")); lv.setMinimumWidth(90); lv.setStyleSheet("font-size:16px;")
        self.van = QComboBox(); self.naar = QComboBox()
        for c in (self.van, self.naar):
            c.setMinimumHeight(46); c.setStyleSheet("font-size:17px;")
            c.currentIndexChanged.connect(self._reken)
        rij2.addWidget(lv); rij2.addWidget(self.van, 1)
        lay.addLayout(rij2)
        rij3 = QHBoxLayout()
        ln = QLabel(T("naar")); ln.setMinimumWidth(90); ln.setStyleSheet("font-size:16px;")
        rij3.addWidget(ln); rij3.addWidget(self.naar, 1)
        lay.addLayout(rij3)
        self.uit = QLabel("")
        self.uit.setStyleSheet("font-size:24px; font-weight:bold; color:%s; padding:10px;" % ACCENT)
        self.uit.setMinimumHeight(48)
        lay.addWidget(self.uit)
        self.invoeg = QPushButton(T("invoegen_doc")); self.invoeg.setObjectName("primair")
        self.invoeg.setMinimumHeight(44); self.invoeg.clicked.connect(self._invoeg)
        self.invoeg.setEnabled(False)
        lay.addWidget(self.invoeg); lay.addStretch(1)

    def _ophalen(self):
        self.ophaal.setText(T("bezig_ophalen")); self.ophaal.setEnabled(False)
        QApplication.processEvents()
        try:
            import urllib.request
            import json as _json
            url = "https://open.er-api.com/v6/latest/EUR"
            with urllib.request.urlopen(url, timeout=8) as r:
                data = _json.loads(r.read().decode("utf-8"))
            koersen = data.get("rates") or {}
            if not koersen:
                raise ValueError("geen koersen")
            self.koersen = koersen
            self.koers_datum = data.get("time_last_update_utc", "")
            valutas = sorted(koersen.keys())
            for c in (self.van, self.naar):
                c.blockSignals(True); c.clear(); c.addItems(valutas); c.blockSignals(False)
            self.van.setCurrentText("EUR"); self.naar.setCurrentText("USD")
            self.koers_label.setText(T("koersen_van", d=self.koers_datum))
            self.invoeg.setEnabled(True)
            self._reken()
        except Exception:
            self.koers_label.setText("\u26a0  " + T("geen_internet"))
        finally:
            self.ophaal.setText(T("koersen_ophalen")); self.ophaal.setEnabled(True)

    def _huidig(self):
        if not self.koersen:
            return None
        try:
            bedrag = float(self.bedrag.text().replace(",", "."))
        except ValueError:
            return None
        van = self.van.currentText(); naar = self.naar.currentText()
        if van not in self.koersen or naar not in self.koersen:
            return None
        # koersen zijn t.o.v. EUR
        eur = bedrag / self.koersen[van]
        res = eur * self.koersen[naar]
        return bedrag, van, naar, res

    def _reken(self):
        h = self._huidig()
        if h is None:
            self.uit.setText("-"); return
        bedrag, van, naar, res = h
        self.uit.setText("%s %s = %s %s" % (fmt_getal(bedrag), van,
                                            fmt_getal(round(res, 2)), naar))

    def _invoeg(self):
        h = self._huidig()
        if h is None:
            return
        bedrag, van, naar, res = h
        self.invoegen.emit("%s %s = %s %s" % (fmt_getal(bedrag), van,
                                              fmt_getal(round(res, 2)), naar))


# ======================================================================
# Rekenmachine in eigen venster
# ======================================================================
class RekenVenster(QDialog):
    def __init__(self, ouder, centrum):
        super().__init__(ouder)
        self.setWindowTitle(T("rekenmachine")); self.setWindowIcon(app_icoon())
        self.setStyleSheet(STIJL())
        # eigen venster met eigen knoppen, niet-blokkerend
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setModal(False)
        self.setSizeGripEnabled(True)
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(centrum)
        self.resize(560, 600)
        self._eerste = True

    def toon(self):
        self.show()
        if self._eerste:
            centreer(self, self.parent()); self._eerste = False
        self.raise_(); self.activateWindow()


# ======================================================================
# Rekenblad (spreadsheet)
# ======================================================================
import re as _re

CEL_RE = _re.compile(r'\b([A-Z]+)(\d+)\b')
BEREIK_RE = _re.compile(r'^([A-Z]+)(\d+):([A-Z]+)(\d+)$')
AGG_RE = _re.compile(
    r'(SUM|SOM|AVERAGE|GEMIDDELDE|GEM|MIN|MAX|COUNT|AANTAL|PRODUCT)\s*\(([^()]*)\)', _re.I)


def kol_index(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def kol_letter(i):
    s = ""; i += 1
    while i > 0:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


class RekenbladKring(Exception):
    pass


class Blad:
    """Rekenkern: cellen met rauwe inhoud (tekst, getal of =formule)."""
    def __init__(self):
        self.cellen = {}
        self._cache = {}

    def zet(self, ref, raw):
        raw = raw if raw is not None else ""
        if raw.strip() == "":
            self.cellen.pop(ref, None)
        else:
            self.cellen[ref] = raw

    def leeg_cache(self):
        self._cache = {}

    def waarde(self, ref, bezig=frozenset()):
        if ref in self._cache:
            return self._cache[ref]
        if ref in bezig:
            raise RekenbladKring(ref)
        raw = self.cellen.get(ref, "").strip()
        if raw == "":
            v = ""
        elif raw.startswith("="):
            v = self._eval(raw[1:], bezig | {ref})
        else:
            v = self._als_getal(raw)
        self._cache[ref] = v
        return v

    def _als_getal(self, raw):
        try:
            return float(raw.replace(" ", "").replace(",", "."))
        except ValueError:
            return raw

    def _num(self, ref, bezig):
        v = self.waarde(ref, bezig)
        return v if isinstance(v, (int, float)) else 0.0

    def _eval(self, expr, bezig):
        # functies met bereiken (SOM, GEMIDDELDE, ...) eerst
        while True:
            m = AGG_RE.search(expr)
            if not m:
                break
            res = self._agg(m.group(1).upper(), m.group(2), bezig)
            expr = expr[:m.start()] + repr(float(res)) + expr[m.end():]
        # celverwijzingen -> getal
        expr = CEL_RE.sub(lambda mm: repr(self._num(mm.group(0), bezig)), expr)
        return veilig_eval(expr)

    def _waarden(self, args, bezig):
        vals = []
        for deel in args.split(","):
            deel = deel.strip()
            if not deel:
                continue
            b = BEREIK_RE.match(deel)
            if b:
                c1, r1 = kol_index(b.group(1)), int(b.group(2))
                c2, r2 = kol_index(b.group(3)), int(b.group(4))
                for r in range(min(r1, r2), max(r1, r2) + 1):
                    for c in range(min(c1, c2), max(c1, c2) + 1):
                        vals.append(self.waarde(kol_letter(c) + str(r), bezig))
            elif _re.match(r'^[A-Z]+\d+$', deel):
                vals.append(self.waarde(deel, bezig))
            else:
                try:
                    vals.append(self._eval(deel, bezig))
                except Exception:
                    pass
        return vals

    def _agg(self, naam, args, bezig):
        vals = self._waarden(args, bezig)
        getallen = [v for v in vals if isinstance(v, (int, float))]
        if naam in ("SUM", "SOM"):
            return sum(getallen)
        if naam in ("AVERAGE", "GEMIDDELDE", "GEM"):
            return sum(getallen) / len(getallen) if getallen else 0.0
        if naam == "MIN":
            return min(getallen) if getallen else 0.0
        if naam == "MAX":
            return max(getallen) if getallen else 0.0
        if naam in ("COUNT", "AANTAL"):
            return float(len(getallen))
        if naam == "PRODUCT":
            p = 1.0
            for g in getallen:
                p *= g
            return p
        return 0.0

    def display(self, ref):
        try:
            v = self.waarde(ref)
        except RekenbladKring:
            return "#KRING"
        except Exception:
            return "#FOUT"
        if isinstance(v, float):
            if v.is_integer():
                return str(int(v))
            return ("%.10g" % v).replace(".", ",")
        return str(v)


class FormuleDelegate(QStyledItemDelegate):
    """Laat bij bewerken de rauwe formule zien i.p.v. de berekende waarde."""
    def __init__(self, rb):
        super().__init__(rb); self.rb = rb

    def setEditorData(self, editor, index):
        ref = self.rb._ref(index.row(), index.column())
        editor.setText(self.rb.blad.cellen.get(ref, ""))

    def setModelData(self, editor, model, index):
        self.rb.zet_cel(index.row(), index.column(), editor.text())


class Rekenblad(QWidget):
    status_signaal = pyqtSignal(str)
    RIJEN = 60
    KOLOMMEN = 26

    def __init__(self):
        super().__init__()
        self.huidig_pad = None
        self.blad = Blad()
        self._verversen = False
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        lay.addWidget(self._maak_balk())
        lay.addWidget(self._maak_formulebalk())
        self.tabel = QTableWidget(self.RIJEN, self.KOLOMMEN)
        self.tabel.setHorizontalHeaderLabels([kol_letter(i) for i in range(self.KOLOMMEN)])
        self.tabel.setVerticalHeaderLabels([str(i + 1) for i in range(self.RIJEN)])
        self.tabel.setItemDelegate(FormuleDelegate(self))
        self.tabel.verticalHeader().setDefaultSectionSize(32)
        self.tabel.setStyleSheet(
            "QTableWidget{ background:#d6d6d6; color:#111111; gridline-color:#aaaaaa;"
            " font-size:15px; }"
            "QTableWidget::item:selected{ background:%s; color:#ffffff; }"
            "QHeaderView::section{ background:%s; color:#9ecbff; padding:6px;"
            " border:1px solid %s; font-weight:bold; }"
            "QTableCornerButton::section{ background:%s; border:1px solid %s; }"
            % (ACCENT, PANEEL, LINE, PANEEL, LINE))
        self.tabel.currentCellChanged.connect(self._cel_geselecteerd)
        lay.addWidget(self.tabel, 1)
        self._init_items()

    def _ref(self, rij, kol):
        return kol_letter(kol) + str(rij + 1)

    def _init_items(self):
        self._verversen = True
        for r in range(self.RIJEN):
            for c in range(self.KOLOMMEN):
                self.tabel.setItem(r, c, QTableWidgetItem(""))
        self._verversen = False

    # ---- balken ----
    def _tb(self, tekst, tip, fn, sneltoets=None):
        b = QPushButton(tekst); b.setMinimumHeight(42)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet("font-size:16px; padding:6px 14px;")
        b.setToolTip(tip + (("   (%s)" % sneltoets) if sneltoets else "")); b.setStatusTip(tip)
        b.clicked.connect(fn)
        if sneltoets:
            b.setShortcut(QKeySequence(sneltoets))
        return b

    def _maak_balk(self):
        bar = QWidget(); bar.setStyleSheet("background:%s;" % PANEEL)
        h = QHBoxLayout(bar); h.setContentsMargins(8, 6, 8, 6); h.setSpacing(8)
        for tekst, tip, fn, st in (
            (T("nieuw"), T("tip_nieuw_blad"), self.nieuw, "Ctrl+N"),
            (T("openen"), T("tip_openen_blad"), self.openen, "Ctrl+O"),
            (T("opslaan"), T("tip_opslaan_blad"), self.opslaan, "Ctrl+S"),
            (T("opslaan_als"), T("tip_opslaan_blad"), self.opslaan_als, "Ctrl+Shift+S"),
        ):
            h.addWidget(self._tb(tekst, tip, fn, st))
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setStyleSheet("color:%s;" % LINE)
        h.addWidget(sep)
        b_hulp = self._tb(T("formule_maken"), T("tip_formule_maken"), self.formule_hulp)
        b_hulp.setObjectName("primair")
        b_hulp.setStyleSheet("font-size:16px; padding:6px 14px; background:%s; color:#0c1116; "
                             "font-weight:bold; border:none; border-radius:8px;" % ACCENT)
        h.addWidget(b_hulp)
        h.addWidget(self._tb(T("voorbeeld"), T("tip_voorbeeld"), self.voorbeeld))
        h.addStretch(1)
        return bar

    def voorbeeld(self):
        if self.blad.cellen:
            vr = QMessageBox.question(self, T("voorbeeld"), T("voorbeeld_vraag"),
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if vr != QMessageBox.StandardButton.Yes:
                return
        self.blad = Blad()
        data = {
            "A1": T("vb_product"), "B1": T("vb_aantal"), "C1": T("vb_prijs"), "D1": T("vb_totaal"),
            "A2": T("vb_appels"), "B2": "3", "C2": "0,50", "D2": "=B2*C2",
            "A3": T("vb_brood"), "B3": "2", "C3": "1,25", "D3": "=B3*C3",
            "A4": T("vb_melk"), "B4": "4", "C4": "0,90", "D4": "=B4*C4",
            "A6": T("vb_totaal_rij"), "D6": "=SOM(D2:D4)",
        }
        for ref, val in data.items():
            self.blad.zet(ref, val)
        self.huidig_pad = None
        self.herbereken()
        self.tabel.setCurrentCell(5, 3)
        self.status_signaal.emit(T("voorbeeld_klaar"))

    def formule_hulp(self):
        FormuleHulp(self, self).exec()

    def _maak_formulebalk(self):
        bar = QWidget(); bar.setStyleSheet("background:%s;" % PANEEL2)
        h = QHBoxLayout(bar); h.setContentsMargins(8, 6, 8, 6); h.setSpacing(8)
        self.cel_naam = QLabel("A1")
        self.cel_naam.setStyleSheet("font-weight:bold; font-size:16px; min-width:48px;")
        fx = QLabel("=")
        fx.setStyleSheet("font-style:italic; color:%s; font-size:16px;" % MUTED)
        self.formule = QLineEdit()
        self.formule.setStyleSheet("font-size:16px; padding:6px;")
        self.formule.setMinimumHeight(38)
        self.formule.setPlaceholderText(T("formule_hint"))
        self.formule.setToolTip(T("tip_formule"))
        self.formule.returnPressed.connect(self._formule_toegepast)
        h.addWidget(self.cel_naam); h.addWidget(fx); h.addWidget(self.formule, 1)
        return bar

    # ---- bewerken ----
    def zet_cel(self, rij, kol, raw):
        ref = self._ref(rij, kol)
        self.blad.zet(ref, raw)
        self.herbereken()
        if self.tabel.currentRow() == rij and self.tabel.currentColumn() == kol:
            self.formule.setText(self.blad.cellen.get(ref, ""))
        self.status_signaal.emit(T("blad_gewijzigd"))

    def herbereken(self):
        self._verversen = True
        self.blad.leeg_cache()
        for r in range(self.RIJEN):
            for c in range(self.KOLOMMEN):
                ref = self._ref(r, c)
                it = self.tabel.item(r, c)
                if it is None:
                    it = QTableWidgetItem(""); self.tabel.setItem(r, c, it)
                it.setText(self.blad.display(ref) if ref in self.blad.cellen else "")
        self._verversen = False

    def _cel_geselecteerd(self, rij, kol, *_):
        if rij < 0 or kol < 0:
            return
        ref = self._ref(rij, kol)
        self.cel_naam.setText(ref)
        self.formule.setText(self.blad.cellen.get(ref, ""))

    def _formule_toegepast(self):
        rij, kol = self.tabel.currentRow(), self.tabel.currentColumn()
        if rij < 0 or kol < 0:
            return
        self.zet_cel(rij, kol, self.formule.text())
        self.tabel.setFocus()

    # ---- bestand ----
    def nieuw(self):
        self.blad = Blad()
        self.huidig_pad = None
        self.herbereken()
        self.formule.clear()
        self.status_signaal.emit(T("naamloos"))

    def openen(self):
        filter_ = "Rekenblad (*.csv *.xlsx);;CSV (*.csv);;Excel (*.xlsx);;Alle bestanden (*)"
        pad, _ = QFileDialog.getOpenFileName(self, T("openen"), DATA_MAP, filter_)
        if not pad:
            return
        try:
            if pad.lower().endswith(".xlsx"):
                self._laad_xlsx(pad)
            else:
                self._laad_csv(pad)
            self.huidig_pad = pad
            self.herbereken()
            self.status_signaal.emit(T("geopend", p=os.path.basename(pad)))
        except Exception as e:
            QMessageBox.critical(self, T("fout"), T("kon_niet_openen", e=str(e)))

    def _laad_csv(self, pad):
        import csv
        self.blad = Blad()
        with open(pad, "r", encoding="utf-8-sig", newline="") as f:
            for r, rij in enumerate(csv.reader(f)):
                for c, waarde in enumerate(rij):
                    if waarde != "" and r < self.RIJEN and c < self.KOLOMMEN:
                        self.blad.zet(self._ref(r, c), waarde)

    def _laad_xlsx(self, pad):
        import openpyxl
        self.blad = Blad()
        wb = openpyxl.load_workbook(pad, data_only=False)
        ws = wb.active
        for rij in ws.iter_rows():
            for cel in rij:
                if cel.value is None:
                    continue
                r, c = cel.row - 1, cel.column - 1
                if r < self.RIJEN and c < self.KOLOMMEN:
                    self.blad.zet(self._ref(r, c), str(cel.value))

    def opslaan(self):
        if self.huidig_pad is None:
            return self.opslaan_als()
        return self._bewaar(self.huidig_pad)

    def opslaan_als(self):
        filter_ = "CSV - met formules (*.csv);;Excel - met uitkomsten (*.xlsx)"
        pad, gekozen = QFileDialog.getSaveFileName(self, T("opslaan_als"), DATA_MAP, filter_)
        if not pad:
            return False
        if "." not in os.path.basename(pad):
            pad += ".xlsx" if "xlsx" in gekozen else ".csv"
        ok = self._bewaar(pad)
        if ok:
            self.huidig_pad = pad
        return ok

    def _gebruikt_gebied(self):
        max_r = max_c = 0
        for ref in self.blad.cellen:
            m = _re.match(r'^([A-Z]+)(\d+)$', ref)
            if m:
                max_c = max(max_c, kol_index(m.group(1)))
                max_r = max(max_r, int(m.group(2)) - 1)
        return max_r, max_c

    def _bewaar(self, pad):
        try:
            if pad.lower().endswith(".xlsx"):
                self._bewaar_xlsx(pad)
            else:
                self._bewaar_csv(pad)
            self.status_signaal.emit(T("opgeslagen", p=os.path.basename(pad)))
            return True
        except Exception as e:
            QMessageBox.critical(self, T("fout"), T("kon_niet_opslaan", e=str(e)))
            return False

    def _bewaar_csv(self, pad):
        import csv
        max_r, max_c = self._gebruikt_gebied()
        with open(pad, "w", encoding="utf-8", newline="") as f:
            schrijver = csv.writer(f)
            for r in range(max_r + 1):
                rij = [self.blad.cellen.get(self._ref(r, c), "") for c in range(max_c + 1)]
                schrijver.writerow(rij)

    def _bewaar_xlsx(self, pad):
        import openpyxl
        self.blad.leeg_cache()
        max_r, max_c = self._gebruikt_gebied()
        wb = openpyxl.Workbook(); ws = wb.active
        for r in range(max_r + 1):
            for c in range(max_c + 1):
                ref = self._ref(r, c)
                if ref not in self.blad.cellen:
                    continue
                try:
                    waarde = self.blad.waarde(ref)
                except Exception:
                    waarde = self.blad.cellen[ref]
                ws.cell(row=r + 1, column=c + 1, value=waarde)
        wb.save(pad)


class FormuleHulp(QDialog):
    """Beginnershulp: kies wat je wilt en welke cellen; de formule wordt opgebouwd."""
    def __init__(self, ouder, rekenblad):
        super().__init__(ouder)
        self.rb = rekenblad
        self.setWindowTitle(T("formule_maken")); self.setWindowIcon(app_icoon())
        self.setStyleSheet(STIJL()); self.resize(540, 460)
        # soorten: (sleutel, type 'reeks'/'paar', functie-of-operator)
        self.soorten = [
            ("fh_som", "reeks", "SOM"), ("fh_gem", "reeks", "GEMIDDELDE"),
            ("fh_min", "reeks", "MIN"), ("fh_max", "reeks", "MAX"),
            ("fh_aantal", "reeks", "AANTAL"),
            ("fh_plus", "paar", "+"), ("fh_min2", "paar", "-"),
            ("fh_keer", "paar", "*"), ("fh_deel", "paar", "/"),
        ]
        lay = QVBoxLayout(self); lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(14)
        rij, kol = self.rb.tabel.currentRow(), self.rb.tabel.currentColumn()
        if rij < 0 or kol < 0:
            rij, kol = 0, 0
        self.doel_ref = self.rb._ref(rij, kol)
        info = QLabel(T("fh_in_cel", c=self.doel_ref))
        info.setStyleSheet("font-size:16px; color:%s;" % MUTED); info.setWordWrap(True)
        lay.addWidget(info)
        # wat wil je doen
        lay.addWidget(self._kop(T("fh_watdoen")))
        self.soort = QComboBox(); self.soort.setMinimumHeight(44)
        self.soort.setStyleSheet("font-size:16px; padding:4px 10px;")
        self.soort.addItems([T(s[0]) for s in self.soorten])
        self.soort.currentIndexChanged.connect(self._ververs)
        lay.addWidget(self.soort)
        # cel-invoer
        velden = QHBoxLayout(); velden.setSpacing(12)
        self.lbl1 = QLabel(""); self.lbl1.setStyleSheet("font-size:16px;")
        self.in1 = QLineEdit("A1"); self.in1.setMinimumHeight(42)
        self.in1.setStyleSheet("font-size:18px; padding:6px;"); self.in1.setMaximumWidth(110)
        self.lbl2 = QLabel(""); self.lbl2.setStyleSheet("font-size:16px;")
        self.in2 = QLineEdit("A5"); self.in2.setMinimumHeight(42)
        self.in2.setStyleSheet("font-size:18px; padding:6px;"); self.in2.setMaximumWidth(110)
        for w in (self.lbl1, self.in1, self.lbl2, self.in2):
            velden.addWidget(w)
        velden.addStretch(1)
        lay.addLayout(velden)
        self.in1.textChanged.connect(self._ververs); self.in2.textChanged.connect(self._ververs)
        # voorbeeld/preview
        lay.addWidget(self._kop(T("fh_wordt")))
        self.preview = QLabel("")
        self.preview.setStyleSheet("font-size:24px; font-weight:bold; color:%s; padding:10px;"
                                   " background:%s; border-radius:8px;" % (ACCENT, PANEEL))
        self.preview.setMinimumHeight(52)
        lay.addWidget(self.preview)
        self.uitleg = QLabel(""); self.uitleg.setStyleSheet("font-size:14px; color:%s;" % MUTED)
        self.uitleg.setWordWrap(True)
        lay.addWidget(self.uitleg)
        lay.addStretch(1)
        # knoppen
        knoppen = QHBoxLayout()
        annul = QPushButton(T("annuleren") if False else T("fh_annuleren"))
        annul.setMinimumHeight(44); annul.clicked.connect(self.reject)
        invoeg = QPushButton(T("fh_zetin", c=self.doel_ref)); invoeg.setObjectName("primair")
        invoeg.setMinimumHeight(44); invoeg.clicked.connect(self._invoegen)
        knoppen.addWidget(annul); knoppen.addWidget(invoeg, 1)
        lay.addLayout(knoppen)
        QTimer.singleShot(0, lambda: centreer(self, ouder))
        self._ververs()

    def _kop(self, tekst):
        lb = QLabel(tekst); lb.setStyleSheet("font-size:15px; font-weight:bold; color:#ffffff;")
        return lb

    def _huidige(self):
        return self.soorten[self.soort.currentIndex()]

    def _formule(self):
        _sleutel, soort, fo = self._huidige()
        c1 = self.in1.text().strip().upper().replace(" ", "")
        c2 = self.in2.text().strip().upper().replace(" ", "")
        geldig = bool(_re.match(r'^[A-Z]+\d+$', c1) and _re.match(r'^[A-Z]+\d+$', c2))
        if soort == "reeks":
            return ("=%s(%s:%s)" % (fo, c1, c2)), geldig
        return ("=%s%s%s" % (c1, fo, c2)), geldig

    def _ververs(self, *_):
        _sleutel, soort, fo = self._huidige()
        if soort == "reeks":
            self.lbl1.setText(T("fh_van")); self.lbl2.setText(T("fh_tot"))
            self.uitleg.setText(T("fh_uitleg_reeks"))
        else:
            self.lbl1.setText(T("fh_cel1")); self.lbl2.setText(T("fh_cel2"))
            self.uitleg.setText(T("fh_uitleg_paar"))
        formule, _ = self._formule()
        self.preview.setText(formule)

    def _invoegen(self):
        formule, geldig = self._formule()
        if not geldig:
            QMessageBox.warning(self, T("formule_maken"), T("fh_ongeldig"))
            return
        rij, kol = self.rb.tabel.currentRow(), self.rb.tabel.currentColumn()
        if rij < 0 or kol < 0:
            rij = kol = 0
        self.rb.zet_cel(rij, kol, formule)
        self.rb.tabel.setFocus()
        self.accept()


# ======================================================================
# Presentatie (dia's)
# ======================================================================


class _SleepLabel(QLabel):
    """Afbeelding die je met de muis kunt verslepen binnen de dia."""
    def __init__(self, ouder, bij_verplaatst):
        super().__init__(ouder)
        self._bij = bij_verplaatst
        self._sleep = False
        self._g0 = QPoint(); self._p0 = QPoint()
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setScaledContents(True)
        self.setToolTip(T("tip_sleep_afb"))

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._sleep = True
            self._g0 = ev.globalPosition().toPoint(); self._p0 = self.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, ev):
        if self._sleep and self.parent() is not None:
            par = self.parent()
            np = self._p0 + (ev.globalPosition().toPoint() - self._g0)
            x = max(0, min(np.x(), par.width() - self.width()))
            y = max(0, min(np.y(), par.height() - self.height()))
            self.move(int(x), int(y))

    def mouseReleaseEvent(self, ev):
        if self._sleep:
            self._sleep = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            if self._bij:
                self._bij()


class _Grip(QLabel):
    """Handvat om een tekstvak te verslepen."""
    def __init__(self, vak, bij_verplaatst):
        super().__init__("\u2630")
        self.vak = vak; self._bij = bij_verplaatst
        self._sleep = False; self._g0 = QPoint(); self._p0 = QPoint()
        self.setFixedSize(38, 22); self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("color:#555; background:#dcdcdc; border:1px solid #b4b4b4;"
                           " border-radius:4px; font-size:14px;")
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setToolTip(T("tip_sleep_tekst"))

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._sleep = True
            self._g0 = ev.globalPosition().toPoint(); self._p0 = self.vak.pos()

    def mouseMoveEvent(self, ev):
        if self._sleep and self.vak.parent() is not None:
            canvas = self.vak.parent()
            np = self._p0 + (ev.globalPosition().toPoint() - self._g0)
            x = max(0, min(np.x(), canvas.width() - self.vak.width()))
            y = max(0, min(np.y(), canvas.height() - self.vak.height()))
            self.vak.move(int(x), int(y))

    def mouseReleaseEvent(self, ev):
        if self._sleep:
            self._sleep = False
            if self._bij:
                self._bij()


class _SleepVak(QFrame):
    """Een verplaatsbaar tekstvak (handvat + invoerwidget) op de dia."""
    def __init__(self, canvas, sleutel, bij_verplaatst):
        super().__init__(canvas)
        self.sleutel = sleutel
        self.setStyleSheet("QFrame{background:transparent; border:none;}")
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(3)
        self.grip = _Grip(self, lambda: bij_verplaatst(sleutel, self))
        rij = QHBoxLayout(); rij.setContentsMargins(0, 0, 0, 0)
        rij.addWidget(self.grip); rij.addStretch(1)
        lay.addLayout(rij)
        self._lay = lay

    def zet_inhoud(self, w):
        self._lay.addWidget(w, 1)


class _DiaCanvas(QFrame):
    """Het 'vel' van de dia; meldt als de grootte verandert."""
    def __init__(self, bij_resize):
        super().__init__()
        self._bij_resize = bij_resize

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if self._bij_resize:
            self._bij_resize()


def _html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def dia_inhoud_html(d):
    """Geeft de inhoud van een dia als HTML (met migratie van oude platte tekst)."""
    if d.get("inhoud_html"):
        return d["inhoud_html"]
    plat = d.get("inhoud", "")
    if plat.strip():
        items = "".join("<li>%s</li>" % _html_escape(r) for r in plat.split("\n") if r.strip())
        return "<ul>%s</ul>" % items
    return ""


def _dia_standaard():
    return {"titel": "", "inhoud_html": "", "afbeelding": "",
            "t_x": 0.06, "t_y": 0.06, "t_w": 0.84,
            "i_x": 0.06, "i_y": 0.26, "i_w": 0.84, "i_h": 0.46,
            "afb_x": 0.72, "afb_y": 0.66, "afb_b": 0.32}


def _vul_standaard(d):
    for k, v in _dia_standaard().items():
        d.setdefault(k, v)
    return d


class Diavoorstelling(QWidget):
    """Volledig scherm: dia's tonen, bladeren met pijltjes/spatie, Esc om te sluiten."""
    def __init__(self, dias, start=0):
        super().__init__()
        self.dias = dias
        self.idx = max(0, min(start, len(dias) - 1)) if dias else 0
        self.setStyleSheet("background:#f4f4f2;")
        self.titel = QLabel(self)
        self.titel.setStyleSheet("color:#161616; font-size:50px; font-weight:bold; background:transparent;")
        self.titel.setWordWrap(True)
        self.inhoud = QLabel(self)
        self.inhoud.setTextFormat(Qt.TextFormat.RichText)
        self.inhoud.setStyleSheet("color:#222222; font-size:30px; background:transparent;")
        self.inhoud.setWordWrap(True)
        self.inhoud.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.inhoud.setOpenExternalLinks(True)
        self.inhoud.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.afb_label = QLabel(self); self.afb_label.setScaledContents(True)
        self.afb_label.setStyleSheet("background:transparent;")
        self.hint = QLabel(T("presenteer_hint"), self)
        self.hint.setStyleSheet("color:#8a8a8a; font-size:16px; background:transparent;")
        self.teller = QLabel("", self)
        self.teller.setStyleSheet("color:#8a8a8a; font-size:18px; background:transparent;")
        self._toon()

    def _toon(self):
        if not self.dias:
            return
        d = _vul_standaard(self.dias[self.idx])
        self.titel.setText(d.get("titel", ""))
        self.inhoud.setText(dia_inhoud_html(d))
        self._huidige_pm = PresentatieWidget._pixmap_van_b64(d.get("afbeelding", ""))
        self.teller.setText("%d / %d" % (self.idx + 1, len(self.dias)))
        self._herplaats()

    def _herplaats(self):
        if not self.dias:
            return
        d = self.dias[self.idx]; W, H = self.width(), self.height()
        tw = int(d.get("t_w", 0.84) * W)
        self.titel.setFixedWidth(tw); self.titel.adjustSize()
        self.titel.move(int(d.get("t_x", 0.06) * W), int(d.get("t_y", 0.06) * H))
        iw = int(d.get("i_w", 0.84) * W)
        self.inhoud.setFixedWidth(iw); self.inhoud.adjustSize()
        self.inhoud.move(int(d.get("i_x", 0.06) * W), int(d.get("i_y", 0.26) * H))
        pm = getattr(self, "_huidige_pm", None)
        if pm is not None and not pm.isNull():
            w = max(40, int(d.get("afb_b", 0.32) * W))
            h = int(w * pm.height() / pm.width()) if pm.width() else w
            self.afb_label.setPixmap(pm); self.afb_label.resize(w, h)
            self.afb_label.move(int(d.get("afb_x", 0.72) * W - w / 2),
                                int(d.get("afb_y", 0.66) * H - h / 2))
            self.afb_label.show()
        else:
            self.afb_label.hide()
        self.hint.adjustSize(); self.hint.move(50, H - 44)
        self.teller.adjustSize(); self.teller.move(W - self.teller.width() - 50, H - 44)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._herplaats()

    def _volgende(self):
        if self.idx < len(self.dias) - 1:
            self.idx += 1; self._toon()
        else:
            self.close()

    def _vorige(self):
        if self.idx > 0:
            self.idx -= 1; self._toon()

    def keyPressEvent(self, ev):
        k = ev.key()
        if k in (Qt.Key.Key_Right, Qt.Key.Key_Space, Qt.Key.Key_PageDown, Qt.Key.Key_Down):
            self._volgende()
        elif k in (Qt.Key.Key_Left, Qt.Key.Key_PageUp, Qt.Key.Key_Up):
            self._vorige()
        elif k in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self.close()
        elif k == Qt.Key.Key_Home:
            self.idx = 0; self._toon()
        elif k == Qt.Key.Key_End:
            self.idx = len(self.dias) - 1; self._toon()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._volgende()
        elif ev.button() == Qt.MouseButton.RightButton:
            self._vorige()


class PresentatieWidget(QWidget):
    status_signaal = pyqtSignal(str)
    GROOTTES = ["16", "20", "24", "28", "32", "40", "48"]

    def __init__(self):
        super().__init__()
        self.huidig_pad = None
        d = _dia_standaard()
        d["titel"] = T("dia_voorbeeld_titel")
        d["inhoud_html"] = "<ul><li>%s</li><li>%s</li><li>%s</li></ul>" % (
            T("dia_vb1"), T("dia_vb2"), T("dia_vb3"))
        self.dias = [d]
        self.huidige = 0
        self._laden = False
        self._bouw()
        self._vul_lijst(); self._toon_dia(0)

    def _bouw(self):
        buiten = QVBoxLayout(self); buiten.setContentsMargins(0, 0, 0, 0); buiten.setSpacing(0)
        buiten.addWidget(self._maak_balk())
        midden = QHBoxLayout(); midden.setContentsMargins(0, 0, 0, 0); midden.setSpacing(0)
        midden.addWidget(self._dia_lijst_paneel())
        midden.addWidget(self._editor(), 1)
        houder = QWidget(); houder.setLayout(midden)
        buiten.addWidget(houder, 1)

    def _tb(self, tekst, tip, fn, obj=None, sneltoets=None):
        b = QPushButton(tekst); b.setMinimumHeight(42)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet("font-size:16px; padding:6px 14px;")
        b.setToolTip(tip + (("   (%s)" % sneltoets) if sneltoets else "")); b.setStatusTip(tip)
        if obj:
            b.setObjectName(obj)
            b.setStyleSheet("font-size:16px; padding:6px 14px; background:%s; color:#0c1116;"
                            " font-weight:bold; border:none; border-radius:8px;" % ACCENT)
        b.clicked.connect(fn)
        if sneltoets:
            b.setShortcut(QKeySequence(sneltoets))
        return b

    def _maak_balk(self):
        bar = QWidget(); bar.setStyleSheet("background:%s;" % PANEEL)
        h = QHBoxLayout(bar); h.setContentsMargins(8, 6, 8, 6); h.setSpacing(8)
        for tekst, tip, fn, st in (
            (T("nieuw"), T("tip_nieuw_pres"), self.nieuw, "Ctrl+N"),
            (T("openen"), T("tip_openen_pres"), self.openen, "Ctrl+O"),
            (T("opslaan"), T("tip_opslaan_pres"), self.opslaan, "Ctrl+S"),
            (T("opslaan_als"), T("tip_opslaan_pres"), self.opslaan_als, "Ctrl+Shift+S"),
        ):
            h.addWidget(self._tb(tekst, tip, fn, sneltoets=st))
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setStyleSheet("color:%s;" % LINE)
        h.addWidget(sep)
        h.addWidget(self._tb(T("diavoorstelling"), T("tip_diavoorstelling"),
                             self.presenteren, obj="primair", sneltoets="F5"))
        h.addWidget(self._tb(T("export_pdf"), T("tip_export_pdf_pres"), self.export_pdf))
        h.addStretch(1)
        return bar

    def _dia_lijst_paneel(self):
        paneel = QFrame(); paneel.setFixedWidth(240)
        paneel.setStyleSheet("QFrame{background:%s; border-right:1px solid %s;}" % (PANEEL, LINE))
        v = QVBoxLayout(paneel); v.setContentsMargins(10, 10, 10, 10); v.setSpacing(8)
        kop = QLabel(T("dias")); kop.setStyleSheet("font-weight:bold; border:none; font-size:15px;")
        v.addWidget(kop)
        self.lijst = QListWidget()
        self.lijst.setStyleSheet("QListWidget{font-size:15px;} QListWidget::item{padding:8px;}")
        self.lijst.currentRowChanged.connect(self._kies_dia)
        v.addWidget(self.lijst, 1)
        knoppen = QGridLayout(); knoppen.setSpacing(6)
        b_nieuw = QPushButton("+ " + T("dia")); b_nieuw.setMinimumHeight(40)
        b_nieuw.setToolTip(T("tip_nieuwe_dia")); b_nieuw.clicked.connect(self.nieuwe_dia)
        b_verw = QPushButton("\u2715"); b_verw.setObjectName("gevaar"); b_verw.setMinimumHeight(40)
        b_verw.setToolTip(T("tip_verwijder_dia")); b_verw.clicked.connect(self.verwijder_dia)
        b_op = QPushButton("\u2191"); b_op.setMinimumHeight(40)
        b_op.setToolTip(T("tip_omhoog")); b_op.clicked.connect(lambda: self._verplaats(-1))
        b_neer = QPushButton("\u2193"); b_neer.setMinimumHeight(40)
        b_neer.setToolTip(T("tip_omlaag")); b_neer.clicked.connect(lambda: self._verplaats(1))
        knoppen.addWidget(b_nieuw, 0, 0, 1, 2); knoppen.addWidget(b_verw, 0, 2)
        knoppen.addWidget(b_op, 1, 0); knoppen.addWidget(b_neer, 1, 1, 1, 2)
        v.addLayout(knoppen)
        return paneel

    def _opmaakbalk(self):
        bar = QWidget(); bar.setStyleSheet("background:%s;" % PANEEL2)
        h = QHBoxLayout(bar); h.setContentsMargins(8, 6, 8, 6); h.setSpacing(8)
        self.cb_font = QFontComboBox(); self.cb_font.setMinimumWidth(190); self.cb_font.setMinimumHeight(38)
        self.cb_font.setToolTip(T("tip_lettertype")); self.cb_font.setEditable(True)
        self.cb_font.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cb_font.lineEdit().setPlaceholderText(T("zoek_font"))
        comp = self.cb_font.completer()
        if comp is not None:
            comp.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            comp.setFilterMode(Qt.MatchFlag.MatchContains)
            comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            comp.activated[str].connect(self._zet_font)
        self.cb_font.textActivated.connect(self._zet_font)
        h.addWidget(self.cb_font)
        lab = QLabel(T("grootte")); lab.setStyleSheet("border:none; color:%s;" % MUTED)
        h.addWidget(lab)
        self.cb_grootte = QComboBox(); self.cb_grootte.addItems(self.GROOTTES)
        self.cb_grootte.setCurrentText("20"); self.cb_grootte.setMinimumHeight(38)
        self.cb_grootte.setToolTip(T("tip_grootte"))
        self.cb_grootte.textActivated.connect(self._zet_grootte)
        h.addWidget(self.cb_grootte)
        for tekst, tip, fn in (
            (T("kleur"), T("tip_kleur"), self._zet_kleur),
            ("\U0001d401", T("vet"), self._vet),
            ("\U0001d456", T("cursief"), self._cursief),
            (T("opsomming"), T("tip_opsomming"), self._bullet),
            (T("quote"), T("tip_quote"), self._quote),
            ("\U0001f517 " + T("link"), T("tip_link"), self._link),
        ):
            b = QPushButton(tekst); b.setMinimumHeight(38)
            b.setStyleSheet("font-size:15px; padding:6px 12px;")
            b.setToolTip(tip); b.clicked.connect(fn)
            h.addWidget(b)
        h.addStretch(1)
        return bar

    def _editor(self):
        houder = QWidget()
        v = QVBoxLayout(houder); v.setContentsMargins(20, 14, 20, 16); v.setSpacing(10)
        v.addWidget(self._opmaakbalk())
        self.canvas = _DiaCanvas(self._herplaats_alles)
        self.canvas.setStyleSheet("QFrame{background:#f4f4f2; border:1px solid %s;"
                                  " border-radius:8px;}" % LINE)
        v.addWidget(self.canvas, 1)
        # titel-vak (sleepbaar)
        self.titel_vak = _SleepVak(self.canvas, "t", self._vak_verplaatst)
        self.ed_titel = QLineEdit()
        self.ed_titel.setPlaceholderText(T("dia_titel_hint"))
        self.ed_titel.setStyleSheet("background:rgba(255,255,255,0.45); border:none; color:#161616;"
                                    " font-size:30px; font-weight:bold; padding:2px 4px;")
        self.ed_titel.textChanged.connect(self._wijzig)
        self.titel_vak.zet_inhoud(self.ed_titel)
        # inhoud-vak (sleepbaar)
        self.inhoud_vak = _SleepVak(self.canvas, "i", self._vak_verplaatst)
        self.ed_inhoud = QTextEdit()
        self.ed_inhoud.setPlaceholderText(T("dia_inhoud_hint"))
        self.ed_inhoud.setStyleSheet("background:rgba(255,255,255,0.45); border:none; color:#222222;"
                                     " font-size:20px;")
        self.ed_inhoud.document().setDefaultFont(QFont("Arial", 14))
        self.ed_inhoud.textChanged.connect(self._wijzig)
        self.ed_inhoud.cursorPositionChanged.connect(self._na_cursor)
        self.inhoud_vak.zet_inhoud(self.ed_inhoud)
        # afbeelding (sleepbaar)
        self.afb_label = _SleepLabel(self.canvas, self._afb_verplaatst)
        self.afb_label.hide()
        # onderbalk
        rij = QHBoxLayout(); rij.setSpacing(8)
        self.btn_afb = QPushButton("\U0001f5bc  " + T("afb_toevoegen")); self.btn_afb.setMinimumHeight(42)
        self.btn_afb.setToolTip(T("tip_afb_toevoegen")); self.btn_afb.clicked.connect(self._afb_toevoegen)
        self.btn_afb_verw = QPushButton(T("afb_verwijderen")); self.btn_afb_verw.setMinimumHeight(42)
        self.btn_afb_verw.setToolTip(T("tip_afb_verwijderen")); self.btn_afb_verw.clicked.connect(self._afb_verwijderen)
        self.afb_groot_lab = QLabel(T("afb_grootte")); self.afb_groot_lab.setStyleSheet("color:%s;" % MUTED)
        self.afb_schuif = QSlider(Qt.Orientation.Horizontal)
        self.afb_schuif.setMinimum(15); self.afb_schuif.setMaximum(90); self.afb_schuif.setValue(32)
        self.afb_schuif.setFixedWidth(180); self.afb_schuif.setToolTip(T("tip_afb_grootte"))
        self.afb_schuif.valueChanged.connect(self._afb_schaal_gewijzigd)
        tip = QLabel(T("sleep_tip")); tip.setStyleSheet("color:%s; font-style:italic;" % MUTED)
        rij.addWidget(self.btn_afb); rij.addWidget(self.btn_afb_verw)
        rij.addSpacing(12); rij.addWidget(self.afb_groot_lab); rij.addWidget(self.afb_schuif)
        rij.addStretch(1); rij.addWidget(tip)
        v.addLayout(rij)
        return houder

    # ---- opmaak ----
    def _merge_char(self, fmt):
        self.ed_inhoud.textCursor().mergeCharFormat(fmt)
        self.ed_inhoud.mergeCurrentCharFormat(fmt)
        self.ed_inhoud.setFocus()

    def _zet_font(self, naam):
        if not naam:
            return
        fmt = QTextCharFormat(); fmt.setFontFamily(naam); self._merge_char(fmt)

    def _zet_grootte(self, txt):
        try:
            pt = float(txt)
        except ValueError:
            return
        fmt = QTextCharFormat(); fmt.setFontPointSize(pt); self._merge_char(fmt)

    def _zet_kleur(self):
        col = QColorDialog.getColor(QColor("#222222"), self, T("kleur"))
        if col.isValid():
            fmt = QTextCharFormat(); fmt.setForeground(col); self._merge_char(fmt)

    def _vet(self):
        fmt = QTextCharFormat()
        zwaar = self.ed_inhoud.fontWeight() >= QFont.Weight.Bold
        fmt.setFontWeight(QFont.Weight.Normal if zwaar else QFont.Weight.Bold)
        self._merge_char(fmt)

    def _cursief(self):
        fmt = QTextCharFormat(); fmt.setFontItalic(not self.ed_inhoud.fontItalic())
        self._merge_char(fmt)

    def _bullet(self):
        self.ed_inhoud.textCursor().createList(QTextListFormat.Style.ListDisc)
        self.ed_inhoud.setFocus()

    def _quote(self):
        cur = self.ed_inhoud.textCursor()
        is_q = cur.blockFormat().leftMargin() > 0
        bf = QTextBlockFormat()
        bf.setLeftMargin(0 if is_q else 44); bf.setRightMargin(0 if is_q else 44)
        bf.setTopMargin(0 if is_q else 8); bf.setBottomMargin(0 if is_q else 8)
        cur.mergeBlockFormat(bf)
        cf = QTextCharFormat(); cf.setFontItalic(not is_q)
        cf.setForeground(QColor("#222222" if is_q else "#555f6b"))
        self._merge_char(cf)

    def _na_cursor(self):
        # zodra de cursor op/na een link staat, is nieuwe tekst toch gewoon normaal
        if getattr(self, "_bezig_cursor", False):
            return
        f = self.ed_inhoud.currentCharFormat()
        if f.isAnchor():
            self._bezig_cursor = True
            nf = QTextCharFormat()
            nf.setAnchor(False); nf.setAnchorHref("")
            nf.setFontUnderline(False); nf.setForeground(QColor("#222222"))
            self.ed_inhoud.setCurrentCharFormat(nf)
            self._bezig_cursor = False

    def _link(self):
        cur = self.ed_inhoud.textCursor()
        bestaande = cur.charFormat().anchorHref()
        url, ok = QInputDialog.getText(self, T("link"), T("link_vraag"),
                                       text=bestaande or "https://")
        if not ok:
            return
        url = url.strip()
        fmt = QTextCharFormat()
        if url:
            fmt.setAnchor(True); fmt.setAnchorHref(url)
            fmt.setForeground(QColor("#1a5fb4")); fmt.setFontUnderline(True)
            if cur.hasSelection():
                cur.mergeCharFormat(fmt)
            else:
                cur.insertText(url, fmt)
        else:
            fmt.setAnchor(False); fmt.setAnchorHref("")
            fmt.setForeground(QColor("#222222")); fmt.setFontUnderline(False)
            if cur.hasSelection():
                cur.mergeCharFormat(fmt)
        # invoer-opmaak terug naar normaal: wat je nu typt is geen link meer
        normaal = QTextCharFormat()
        normaal.setAnchor(False); normaal.setAnchorHref("")
        normaal.setForeground(QColor("#222222")); normaal.setFontUnderline(False)
        self.ed_inhoud.setCurrentCharFormat(normaal)
        self.ed_inhoud.setFocus()

    # ---- dia-beheer ----
    def _vul_lijst(self):
        self._laden = True
        self.lijst.clear()
        for i, d in enumerate(self.dias):
            titel = d.get("titel", "").strip() or T("dia_zonder_titel")
            self.lijst.addItem("%d.  %s" % (i + 1, titel))
        self._laden = False

    def _toon_dia(self, i):
        if not self.dias:
            return
        self.huidige = max(0, min(i, len(self.dias) - 1))
        d = _vul_standaard(self.dias[self.huidige])
        self._laden = True
        self.ed_titel.setText(d.get("titel", ""))
        self.ed_inhoud.setHtml(dia_inhoud_html(d))
        self.lijst.setCurrentRow(self.huidige)
        self.afb_schuif.blockSignals(True)
        self.afb_schuif.setValue(int(d.get("afb_b", 0.32) * 100))
        self.afb_schuif.blockSignals(False)
        self._laden = False
        self._plaats_vakken(); self._pas_afbeelding_toe()

    def _kies_dia(self, rij):
        if self._laden or rij < 0:
            return
        self._toon_dia(rij)

    def _wijzig(self):
        if self._laden or not self.dias:
            return
        self.dias[self.huidige]["titel"] = self.ed_titel.text()
        self.dias[self.huidige]["inhoud_html"] = self.ed_inhoud.toHtml()
        self.dias[self.huidige].pop("inhoud", None)
        titel = self.ed_titel.text().strip() or T("dia_zonder_titel")
        it = self.lijst.item(self.huidige)
        if it:
            it.setText("%d.  %s" % (self.huidige + 1, titel))
        self.status_signaal.emit(T("pres_gewijzigd"))

    def nieuwe_dia(self):
        self.dias.insert(self.huidige + 1, _dia_standaard())
        self._vul_lijst(); self._toon_dia(self.huidige + 1)
        self.ed_titel.setFocus()

    def verwijder_dia(self):
        if len(self.dias) <= 1:
            self.dias = [_dia_standaard()]
            self._vul_lijst(); self._toon_dia(0); return
        del self.dias[self.huidige]
        self._vul_lijst(); self._toon_dia(min(self.huidige, len(self.dias) - 1))

    def _verplaats(self, richting):
        n = self.huidige + richting
        if n < 0 or n >= len(self.dias):
            return
        self.dias[self.huidige], self.dias[n] = self.dias[n], self.dias[self.huidige]
        self._vul_lijst(); self._toon_dia(n)

    def presenteren(self):
        if not self.dias:
            return
        self._show = Diavoorstelling(self.dias, self.huidige)
        self._show.showFullScreen()

    # ---- tekstvakken plaatsen ----
    def _plaats_vakken(self):
        if not self.dias:
            return
        d = self.dias[self.huidige]
        cw, ch = max(1, self.canvas.width()), max(1, self.canvas.height())
        tw = int(d.get("t_w", 0.84) * cw)
        self.titel_vak.resize(tw, 78)
        self.titel_vak.move(int(d.get("t_x", 0.06) * cw), int(d.get("t_y", 0.06) * ch))
        iw = int(d.get("i_w", 0.84) * cw); ih = max(80, int(d.get("i_h", 0.46) * ch))
        self.inhoud_vak.resize(iw, ih)
        self.inhoud_vak.move(int(d.get("i_x", 0.06) * cw), int(d.get("i_y", 0.26) * ch))
        self.titel_vak.show(); self.inhoud_vak.show()

    def _herplaats_alles(self):
        self._plaats_vakken()
        if self.dias and self.dias[self.huidige].get("afbeelding"):
            self._pas_afbeelding_toe()

    def _vak_verplaatst(self, sleutel, vak):
        if not self.dias:
            return
        cw, ch = max(1, self.canvas.width()), max(1, self.canvas.height())
        p = vak.pos()
        if sleutel == "t":
            self.dias[self.huidige]["t_x"] = p.x() / cw
            self.dias[self.huidige]["t_y"] = p.y() / ch
        else:
            self.dias[self.huidige]["i_x"] = p.x() / cw
            self.dias[self.huidige]["i_y"] = p.y() / ch
        self.status_signaal.emit(T("pres_gewijzigd"))

    # ---- afbeelding ----
    @staticmethod
    def _pixmap_van_b64(b64):
        pm = QPixmap()
        if b64:
            try:
                pm.loadFromData(base64.b64decode(b64))
            except Exception:
                pass
        return pm

    def _pas_afbeelding_toe(self):
        if not self.dias:
            return
        d = self.dias[self.huidige]
        pm = self._pixmap_van_b64(d.get("afbeelding", ""))
        if pm.isNull():
            self.afb_label.hide()
            self.btn_afb_verw.setEnabled(False); self.afb_schuif.setEnabled(False)
            self.afb_groot_lab.setEnabled(False)
            self.btn_afb.setText("\U0001f5bc  " + T("afb_toevoegen"))
            return
        self.btn_afb_verw.setEnabled(True); self.afb_schuif.setEnabled(True)
        self.afb_groot_lab.setEnabled(True)
        self.btn_afb.setText("\U0001f5bc  " + T("afb_vervangen"))
        cw, ch = max(1, self.canvas.width()), max(1, self.canvas.height())
        w = max(40, int(d.get("afb_b", 0.32) * cw))
        h = int(w * pm.height() / pm.width()) if pm.width() else w
        self.afb_label.setPixmap(pm); self.afb_label.resize(w, h)
        x = int(d.get("afb_x", 0.72) * cw - w / 2)
        y = int(d.get("afb_y", 0.66) * ch - h / 2)
        x = max(0, min(x, cw - w)); y = max(0, min(y, ch - h))
        self.afb_label.move(x, y); self.afb_label.show(); self.afb_label.raise_()

    def _afb_verplaatst(self):
        if not self.dias:
            return
        cw, ch = max(1, self.canvas.width()), max(1, self.canvas.height())
        g = self.afb_label.geometry()
        self.dias[self.huidige]["afb_x"] = (g.x() + g.width() / 2) / cw
        self.dias[self.huidige]["afb_y"] = (g.y() + g.height() / 2) / ch
        self.status_signaal.emit(T("pres_gewijzigd"))

    def _afb_schaal_gewijzigd(self, val):
        if self._laden or not self.dias:
            return
        self.dias[self.huidige]["afb_b"] = val / 100.0
        self._pas_afbeelding_toe()
        self.status_signaal.emit(T("pres_gewijzigd"))

    def _afb_toevoegen(self):
        if not self.dias:
            return
        pad, _ = QFileDialog.getOpenFileName(
            self, T("afb_toevoegen"), DATA_MAP,
            "Afbeeldingen (*.png *.jpg *.jpeg *.bmp *.gif);;Alle bestanden (*)")
        if not pad:
            return
        try:
            with open(pad, "rb") as f:
                data = f.read()
            d = self.dias[self.huidige]
            d["afbeelding"] = base64.b64encode(data).decode("ascii")
            _vul_standaard(d)
            self.afb_schuif.blockSignals(True); self.afb_schuif.setValue(int(d["afb_b"] * 100))
            self.afb_schuif.blockSignals(False)
            self._pas_afbeelding_toe()
            self.status_signaal.emit(T("pres_gewijzigd"))
        except Exception as e:
            QMessageBox.critical(self, T("fout"), T("kon_niet_openen", e=str(e)))

    def _afb_verwijderen(self):
        if self.dias and self.dias[self.huidige].get("afbeelding"):
            self.dias[self.huidige]["afbeelding"] = ""
            self._pas_afbeelding_toe()
            self.status_signaal.emit(T("pres_gewijzigd"))

    # ---- bestand ----
    def nieuw(self):
        self.dias = [_dia_standaard()]; self.huidig_pad = None
        self._vul_lijst(); self._toon_dia(0)
        self.status_signaal.emit(T("naamloos"))

    def openen(self):
        pad, _ = QFileDialog.getOpenFileName(self, T("openen"), DATA_MAP,
                                             "DravePresentatie (*.json);;Alle bestanden (*)")
        if not pad:
            return
        try:
            with open(pad, "r", encoding="utf-8") as f:
                d = json.load(f)
            self.dias = d.get("dias") or [_dia_standaard()]
            for dd in self.dias:
                _vul_standaard(dd)
            self.huidig_pad = pad
            self._vul_lijst(); self._toon_dia(0)
            self.status_signaal.emit(T("geopend", p=os.path.basename(pad)))
        except Exception as e:
            QMessageBox.critical(self, T("fout"), T("kon_niet_openen", e=str(e)))

    def opslaan(self):
        if self.huidig_pad is None:
            return self.opslaan_als()
        return self._bewaar(self.huidig_pad)

    def opslaan_als(self):
        pad, _ = QFileDialog.getSaveFileName(self, T("opslaan_als"), DATA_MAP,
                                             "DravePresentatie (*.json)")
        if not pad:
            return False
        if not pad.lower().endswith(".json"):
            pad += ".json"
        if self._bewaar(pad):
            self.huidig_pad = pad
            return True
        return False

    def _bewaar(self, pad):
        try:
            with open(pad, "w", encoding="utf-8") as f:
                json.dump({"dias": self.dias}, f, indent=2, ensure_ascii=False)
            self.status_signaal.emit(T("opgeslagen_als", p=os.path.basename(pad)))
            return True
        except Exception as e:
            QMessageBox.critical(self, T("fout"), T("kon_niet_opslaan", e=str(e)))
            return False

    def export_pdf(self):
        pad, _ = QFileDialog.getSaveFileName(self, T("export_pdf"), DATA_MAP, "PDF (*.pdf)")
        if not pad:
            return
        if not pad.lower().endswith(".pdf"):
            pad += ".pdf"
        try:
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QPainter, QPageLayout
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(pad)
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            huidige = self.huidige
            # grips en schuifbalk verbergen tijdens het afdrukken
            self.titel_vak.grip.hide(); self.inhoud_vak.grip.hide()
            sbp = self.ed_inhoud.verticalScrollBarPolicy()
            self.ed_inhoud.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            painter = QPainter(printer)
            vlak = painter.viewport()
            for i in range(len(self.dias)):
                if i > 0:
                    printer.newPage()
                self._toon_dia(i)
                self.canvas.repaint()
                vel = QPixmap(self.canvas.size()); vel.fill(QColor("#f4f4f2"))
                self.canvas.render(vel)
                geschaald = vel.scaled(vlak.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                x = vlak.x() + (vlak.width() - geschaald.width()) // 2
                y = vlak.y() + (vlak.height() - geschaald.height()) // 2
                painter.drawPixmap(x, y, geschaald)
            painter.end()
            self.ed_inhoud.setVerticalScrollBarPolicy(sbp)
            self.titel_vak.grip.show(); self.inhoud_vak.grip.show()
            self._toon_dia(huidige)
            self.status_signaal.emit(T("opgeslagen_als", p=os.path.basename(pad)))
        except Exception as e:
            QMessageBox.critical(self, T("fout"), T("kon_niet_opslaan", e=str(e)))


# ======================================================================
# Tekenen
# ======================================================================
class TekenCanvas(QWidget):
    gewijzigd = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.afb = QPixmap(900, 620); self.afb.fill(Qt.GlobalColor.white)
        self.tool = "pen"; self.kleur = QColor("#1a1a1a"); self.dikte = 4
        self.last = None; self.start = None; self.preview_pt = None; self.bezig = False
        self.undo_stack = []
        self.setCursor(Qt.CursorShape.CrossCursor)

    def resizeEvent(self, ev):
        w = max(self.afb.width(), self.width()); h = max(self.afb.height(), self.height())
        if w != self.afb.width() or h != self.afb.height():
            nieuw = QPixmap(w, h); nieuw.fill(Qt.GlobalColor.white)
            p = QPainter(nieuw); p.drawPixmap(0, 0, self.afb); p.end()
            self.afb = nieuw
        self.update()

    def _push(self):
        self.undo_stack.append(self.afb.copy())
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def ongedaan(self):
        if self.undo_stack:
            self.afb = self.undo_stack.pop(); self.update(); self.gewijzigd.emit()

    def wissen(self):
        self._push(); self.afb.fill(Qt.GlobalColor.white); self.update(); self.gewijzigd.emit()

    def _pen(self):
        kleur = QColor("#ffffff") if self.tool == "gum" else self.kleur
        dikte = self.dikte * 4 if self.tool == "gum" else self.dikte
        return QPen(kleur, dikte, Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

    def mousePressEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        self._push(); self.bezig = True
        self.start = ev.position().toPoint(); self.last = self.start; self.preview_pt = self.start

    def mouseMoveEvent(self, ev):
        if not self.bezig:
            return
        pt = ev.position().toPoint()
        if self.tool in ("pen", "gum"):
            p = QPainter(self.afb); p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(self._pen()); p.drawLine(self.last, pt); p.end(); self.last = pt
        else:
            self.preview_pt = pt
        self.update()

    def mouseReleaseEvent(self, ev):
        if not self.bezig:
            return
        self.bezig = False
        if self.tool in ("lijn", "rechthoek", "ovaal") and self.start is not None:
            p = QPainter(self.afb); p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(self._pen()); self._vorm(p, self.start, ev.position().toPoint()); p.end()
        self.start = None; self.last = None; self.update(); self.gewijzigd.emit()

    def _vorm(self, p, a, b):
        r = QRect(a, b).normalized()
        if self.tool == "lijn":
            p.drawLine(a, b)
        elif self.tool == "rechthoek":
            p.drawRect(r)
        elif self.tool == "ovaal":
            p.drawEllipse(r)

    def paintEvent(self, ev):
        qp = QPainter(self); qp.drawPixmap(0, 0, self.afb)
        if self.bezig and self.tool in ("lijn", "rechthoek", "ovaal") \
                and self.start is not None and self.preview_pt is not None:
            qp.setRenderHint(QPainter.RenderHint.Antialiasing); qp.setPen(self._pen())
            self._vorm(qp, self.start, self.preview_pt)
        qp.end()

    def opslaan(self, pad):
        return self.afb.save(pad)

    def open_afb(self, pad):
        pm = QPixmap(pad)
        if pm.isNull():
            return False
        self._push()
        w = max(self.afb.width(), pm.width()); h = max(self.afb.height(), pm.height())
        nieuw = QPixmap(w, h); nieuw.fill(Qt.GlobalColor.white)
        p = QPainter(nieuw); p.drawPixmap(0, 0, pm); p.end()
        self.afb = nieuw; self.update(); self.gewijzigd.emit(); return True


class TekenWidget(QWidget):
    status_signaal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.tool_knoppen = {}
        self._bouw()

    def _bouw(self):
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        self.canvas = TekenCanvas()
        self.canvas.gewijzigd.connect(lambda: self.status_signaal.emit(T("teken_gewijzigd")))
        v.addWidget(self._balk())
        wrap = QWidget(); wrap.setStyleSheet("background:%s;" % BG)
        wl = QVBoxLayout(wrap); wl.setContentsMargins(12, 12, 12, 12)
        omkader = QFrame(); omkader.setStyleSheet("QFrame{border:1px solid %s; border-radius:6px;}" % LINE)
        ol = QVBoxLayout(omkader); ol.setContentsMargins(0, 0, 0, 0); ol.addWidget(self.canvas)
        wl.addWidget(omkader)
        v.addWidget(wrap, 1)

    def _knop(self, tekst, tip, fn, sleutel=None, sneltoets=None):
        b = QPushButton(tekst); b.setMinimumHeight(44); b.setMinimumWidth(54)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet("font-size:16px; padding:6px 12px;")
        b.setToolTip(tip + (("   (%s)" % sneltoets) if sneltoets else "")); b.setStatusTip(tip)
        b.clicked.connect(fn)
        if sneltoets:
            b.setShortcut(QKeySequence(sneltoets))
        if sleutel:
            self.tool_knoppen[sleutel] = b
        return b

    def _balk(self):
        bar = QWidget(); bar.setStyleSheet("background:%s;" % PANEEL)
        h = QHBoxLayout(bar); h.setContentsMargins(8, 6, 8, 6); h.setSpacing(8)
        for sleutel, tekst, tip in (
            ("pen", "\u270e " + T("pen"), T("tip_pen")),
            ("lijn", "\u2571 " + T("lijn"), T("tip_lijn")),
            ("rechthoek", "\u25ad " + T("rechthoek"), T("tip_rechthoek")),
            ("ovaal", "\u2b2d " + T("ovaal"), T("tip_ovaal")),
            ("gum", "\u232b " + T("gum"), T("tip_gum")),
        ):
            h.addWidget(self._knop(tekst, tip, lambda _=False, s=sleutel: self._kies_tool(s), sleutel=sleutel))
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setStyleSheet("color:%s;" % LINE)
        h.addWidget(sep)
        self.kleur_knop = QPushButton(T("kleur")); self.kleur_knop.setMinimumHeight(44)
        self.kleur_knop.setToolTip(T("tip_teken_kleur")); self.kleur_knop.clicked.connect(self._kies_kleur)
        self._kleur_swatch()
        h.addWidget(self.kleur_knop)
        lab = QLabel(T("dikte")); lab.setStyleSheet("border:none; color:%s;" % MUTED)
        h.addWidget(lab)
        self.cb_dikte = QComboBox(); self.cb_dikte.addItems(["2", "4", "6", "10", "16", "24"])
        self.cb_dikte.setCurrentText("4"); self.cb_dikte.setMinimumHeight(40)
        self.cb_dikte.setToolTip(T("tip_dikte"))
        self.cb_dikte.textActivated.connect(lambda t: setattr(self.canvas, "dikte", int(t)))
        h.addWidget(self.cb_dikte)
        h.addWidget(self._knop("\u21b6 " + T("ongedaan"), T("tip_teken_ongedaan"),
                               lambda: self.canvas.ongedaan(), sneltoets="Ctrl+Z"))
        h.addWidget(self._knop(T("wissen"), T("tip_wissen"), self._wissen))
        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.VLine); sep2.setStyleSheet("color:%s;" % LINE)
        h.addWidget(sep2)
        h.addWidget(self._knop(T("openen"), T("tip_teken_openen"), self._openen))
        h.addWidget(self._knop(T("teken_opslaan"), T("tip_teken_opslaan"), self._opslaan, sneltoets="Ctrl+S"))
        h.addStretch(1)
        self._kies_tool("pen")
        return bar

    def _kleur_swatch(self):
        c = self.canvas.kleur.name() if hasattr(self, "canvas") else "#1a1a1a"
        self.kleur_knop.setStyleSheet(
            "font-size:15px; padding:6px 12px; border-left:18px solid %s;" % c)

    def _kies_tool(self, sleutel):
        self.canvas.tool = sleutel
        for s, b in self.tool_knoppen.items():
            if s == sleutel:
                b.setStyleSheet("font-size:16px; padding:6px 12px; background:%s; color:#0c1116;"
                                " font-weight:bold; border:none; border-radius:8px;" % ACCENT)
            else:
                b.setStyleSheet("font-size:16px; padding:6px 12px;")

    def _kies_kleur(self):
        col = QColorDialog.getColor(self.canvas.kleur, self, T("kleur"))
        if col.isValid():
            self.canvas.kleur = col; self._kleur_swatch()

    def _wissen(self):
        if QMessageBox.question(self, T("wissen"), T("teken_wis_vraag"),
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            self.canvas.wissen()

    def _opslaan(self):
        pad, _ = QFileDialog.getSaveFileName(self, T("teken_opslaan"), DATA_MAP,
                                             "PNG (*.png);;JPEG (*.jpg)")
        if not pad:
            return
        if not (pad.lower().endswith(".png") or pad.lower().endswith(".jpg")):
            pad += ".png"
        if self.canvas.opslaan(pad):
            self.status_signaal.emit(T("opgeslagen_als", p=os.path.basename(pad)))
        else:
            QMessageBox.critical(self, T("fout"), T("kon_niet_opslaan", e="?"))

    def _openen(self):
        pad, _ = QFileDialog.getOpenFileName(self, T("openen"), DATA_MAP,
                                             "Afbeeldingen (*.png *.jpg *.jpeg *.bmp *.gif)")
        if not pad:
            return
        if self.canvas.open_afb(pad):
            self.status_signaal.emit(T("geopend", p=os.path.basename(pad)))
        else:
            QMessageBox.critical(self, T("fout"), T("kon_niet_openen", e="?"))


# ======================================================================
# Database (tabel/lijst)
# ======================================================================
class DatabaseWidget(QWidget):
    status_signaal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.huidig_pad = None
        self._bouw()
        self._nieuw_basis()

    def _bouw(self):
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        v.addWidget(self._balk())
        self.tabel = QTableWidget(0, 0)
        self.tabel.setStyleSheet(
            "QTableWidget{ background:#d6d6d6; color:#111111; gridline-color:#aaaaaa;"
            " font-size:15px; } QTableWidget::item:selected{ background:%s; color:#fff; }"
            "QHeaderView::section{ background:%s; color:#9ecbff; padding:8px;"
            " border:1px solid %s; font-weight:bold; font-size:15px; }" % (ACCENT, PANEEL, LINE))
        self.tabel.verticalHeader().setDefaultSectionSize(34)
        self.tabel.horizontalHeader().setStretchLastSection(True)
        self.tabel.itemChanged.connect(lambda *_a: self.status_signaal.emit(T("db_gewijzigd")))
        wrap = QWidget(); wrap.setStyleSheet("background:%s;" % BG)
        wl = QVBoxLayout(wrap); wl.setContentsMargins(12, 12, 12, 12); wl.addWidget(self.tabel)
        v.addWidget(wrap, 1)

    def _knop(self, tekst, tip, fn, obj=None, sneltoets=None):
        b = QPushButton(tekst); b.setMinimumHeight(44)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet("font-size:15px; padding:6px 12px;")
        if obj == "gevaar":
            b.setStyleSheet("font-size:15px; padding:6px 12px; color:%s; border:1px solid %s;" % (WARN, LINE))
        b.setToolTip(tip + (("   (%s)" % sneltoets) if sneltoets else "")); b.setStatusTip(tip)
        b.clicked.connect(fn)
        if sneltoets:
            b.setShortcut(QKeySequence(sneltoets))
        return b

    def _balk(self):
        bar = QWidget(); bar.setStyleSheet("background:%s;" % PANEEL)
        h = QHBoxLayout(bar); h.setContentsMargins(8, 6, 8, 6); h.setSpacing(8)
        h.addWidget(self._knop("+ " + T("db_rij"), T("tip_db_rij"), self.rij_toevoegen))
        h.addWidget(self._knop("\u2715 " + T("db_rij"), T("tip_db_rij_weg"), self.rij_verwijderen, obj="gevaar"))
        h.addWidget(self._knop("+ " + T("db_kolom"), T("tip_db_kolom"), self.kolom_toevoegen))
        h.addWidget(self._knop("\u2715 " + T("db_kolom"), T("tip_db_kolom_weg"), self.kolom_verwijderen, obj="gevaar"))
        h.addWidget(self._knop(T("db_hernoem"), T("tip_db_hernoem"), self.kolom_hernoemen))
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setStyleSheet("color:%s;" % LINE)
        h.addWidget(sep)
        h.addWidget(self._knop(T("nieuw"), T("tip_db_nieuw"), self.nieuw))
        h.addWidget(self._knop(T("openen"), T("tip_db_openen"), self.openen, sneltoets="Ctrl+O"))
        h.addWidget(self._knop(T("opslaan"), T("tip_db_opslaan"), self.opslaan, sneltoets="Ctrl+S"))
        h.addStretch(1)
        return bar

    def _nieuw_basis(self):
        self.tabel.blockSignals(True)
        self.tabel.clear()
        self.tabel.setColumnCount(3)
        self.tabel.setHorizontalHeaderLabels([T("db_kol1"), T("db_kol2"), T("db_kol3")])
        self.tabel.setRowCount(5)
        self.tabel.blockSignals(False)

    def rij_toevoegen(self):
        self.tabel.insertRow(self.tabel.rowCount())

    def rij_verwijderen(self):
        r = self.tabel.currentRow()
        if r >= 0:
            self.tabel.removeRow(r)

    def kolom_toevoegen(self):
        naam, ok = QInputDialog.getText(self, T("db_kolom"), T("db_kolom_naam"))
        if ok:
            c = self.tabel.columnCount()
            self.tabel.insertColumn(c)
            self.tabel.setHorizontalHeaderItem(c, QTableWidgetItem(naam.strip() or T("db_kolom")))

    def kolom_verwijderen(self):
        c = self.tabel.currentColumn()
        if c >= 0 and self.tabel.columnCount() > 1:
            self.tabel.removeColumn(c)

    def kolom_hernoemen(self):
        c = self.tabel.currentColumn()
        if c < 0:
            return
        oud = self.tabel.horizontalHeaderItem(c)
        oud_naam = oud.text() if oud else ""
        naam, ok = QInputDialog.getText(self, T("db_hernoem"), T("db_kolom_naam"), text=oud_naam)
        if ok and naam.strip():
            self.tabel.setHorizontalHeaderItem(c, QTableWidgetItem(naam.strip()))

    def nieuw(self):
        if QMessageBox.question(self, T("nieuw"), T("db_nieuw_vraag"),
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) == QMessageBox.StandardButton.Yes:
            self._nieuw_basis(); self.huidig_pad = None

    def _kop_namen(self):
        namen = []
        for c in range(self.tabel.columnCount()):
            it = self.tabel.horizontalHeaderItem(c)
            namen.append(it.text() if it else chr(65 + c))
        return namen

    def opslaan(self):
        pad, _ = QFileDialog.getSaveFileName(self, T("opslaan"), DATA_MAP, "CSV (*.csv)")
        if not pad:
            return
        if not pad.lower().endswith(".csv"):
            pad += ".csv"
        try:
            import csv
            with open(pad, "w", encoding="utf-8-sig", newline="") as f:
                s = csv.writer(f, delimiter=";")
                s.writerow(self._kop_namen())
                for r in range(self.tabel.rowCount()):
                    rij = []
                    for c in range(self.tabel.columnCount()):
                        it = self.tabel.item(r, c)
                        rij.append(it.text() if it else "")
                    s.writerow(rij)
            self.huidig_pad = pad
            self.status_signaal.emit(T("opgeslagen_als", p=os.path.basename(pad)))
        except Exception as e:
            QMessageBox.critical(self, T("fout"), T("kon_niet_opslaan", e=str(e)))

    def openen(self):
        pad, _ = QFileDialog.getOpenFileName(self, T("openen"), DATA_MAP,
                                             "CSV (*.csv);;Alle bestanden (*)")
        if not pad:
            return
        try:
            import csv
            with open(pad, "r", encoding="utf-8-sig", newline="") as f:
                rijen = list(csv.reader(f, delimiter=";"))
            self.tabel.blockSignals(True)
            self.tabel.clear()
            if rijen:
                koppen = rijen[0]
                self.tabel.setColumnCount(len(koppen))
                self.tabel.setHorizontalHeaderLabels(koppen)
                data = rijen[1:]
                self.tabel.setRowCount(len(data))
                for r, rij in enumerate(data):
                    for c, val in enumerate(rij):
                        if c < self.tabel.columnCount():
                            self.tabel.setItem(r, c, QTableWidgetItem(val))
            self.tabel.blockSignals(False)
            self.huidig_pad = pad
            self.status_signaal.emit(T("geopend", p=os.path.basename(pad)))
        except Exception as e:
            QMessageBox.critical(self, T("fout"), T("kon_niet_openen", e=str(e)))


# ======================================================================
# Welkomscherm
# ======================================================================
class WelkomDialoog(QDialog):
    def __init__(self, ouder, cfg):
        super().__init__(ouder)
        self.cfg = cfg
        self.setWindowTitle(T("welkom")); self.setWindowIcon(app_icoon())
        self.setStyleSheet(STIJL()); self.setMinimumSize(560, 460)
        lay = QVBoxLayout(self); lay.setContentsMargins(30, 24, 30, 24); lay.setSpacing(12)
        logo = QLabel(); pm = QPixmap(os.path.join(ASSETS, "logo.png"))
        if not pm.isNull():
            logo.setPixmap(pm.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kop = QLabel("%s  v%s" % (APP_NAAM, APP_VERSIE))
        kop.setStyleSheet("font-size:24px; font-weight:bold; color:#ffffff;")
        kop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tekst = QLabel(T("kies_onderdeel"))
        tekst.setStyleSheet("font-size:16px; color:%s;" % MUTED)
        tekst.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo); lay.addWidget(kop); lay.addWidget(tekst)
        lay.addStretch(1)
        self.chk = QCheckBox(T("toon_welkom"))
        self.chk.setChecked(cfg.get("toon_welkom", True))
        lay.addWidget(self.chk)
        start = QPushButton(T("start")); start.setObjectName("primair")
        start.setMinimumHeight(46); start.clicked.connect(self.accept)
        lay.addWidget(start)
        QTimer.singleShot(0, self._plaats_midden)

    def _plaats_midden(self):
        self.adjustSize()
        scr = QApplication.primaryScreen()
        if scr is not None:
            g = self.frameGeometry()
            g.moveCenter(scr.availableGeometry().center())
            self.move(g.topLeft())

    def accept(self):
        self.cfg["toon_welkom"] = self.chk.isChecked()
        bewaar_config(self.cfg)
        super().accept()


# ======================================================================
# Hoofdvenster
# ======================================================================
class Hoofdvenster(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle("%s  v%s" % (APP_NAAM, APP_VERSIE))
        self.setWindowIcon(app_icoon())
        self.setStyleSheet(STIJL())

        self.stapel = QStackedWidget()
        self.portaal = Portaal()
        self.writer = WriterWidget()
        self.rekenblad = Rekenblad()
        self.kasboek = KasboekWidget()
        self.presentatie = PresentatieWidget()
        self.tekenen = TekenWidget()
        self.database = DatabaseWidget()
        self.stapel.addWidget(self.portaal)     # 0
        self.stapel.addWidget(self.writer)      # 1
        self.stapel.addWidget(self.rekenblad)   # 2
        self.stapel.addWidget(self.kasboek)     # 3
        self.stapel.addWidget(self.presentatie) # 4
        self.stapel.addWidget(self.tekenen)     # 5
        self.stapel.addWidget(self.database)    # 6
        self.setCentralWidget(self.stapel)

        # rekenmachine in een eigen venster
        self.calc = RekenCentrum()
        self.calc_venster = RekenVenster(self, self.calc)

        self.portaal.onderdeel_gekozen.connect(self._open_onderdeel)
        self.writer.status_signaal.connect(self._status)
        self.rekenblad.status_signaal.connect(self._status)
        self.kasboek.status_signaal.connect(self._status)
        self.presentatie.status_signaal.connect(self._status)
        self.tekenen.status_signaal.connect(self._status)
        self.database.status_signaal.connect(self._status)
        self.calc.invoegen.connect(self._voeg_in_doc)

        self._maak_menu()
        self._maak_werkbalk()
        self.setStatusBar(QStatusBar())
        self._status(T("portaal"))
        self._toon(0)

    # ---- navigatie ----
    def _toon(self, idx):
        self.stapel.setCurrentIndex(idx)
        self.terug_actie.setVisible(idx != 0)
        namen = {0: T("portaal"), 1: T("tekstverwerker"), 2: T("rekenblad"),
                 3: T("kasboek"), 4: T("presentatie"), 5: T("tekenen"), 6: T("database")}
        self.setWindowTitle("%s - %s" % (APP_NAAM, namen.get(idx, "")))

    def _open_calc(self):
        self.calc_venster.toon()

    def _open_onderdeel(self, sleutel):
        if sleutel == "writer":
            self._toon(1)
        elif sleutel == "sheet":
            self._toon(2)
        elif sleutel == "kas":
            self._toon(3)
        elif sleutel == "slides":
            self._toon(4)
        elif sleutel == "draw":
            self._toon(5)
        elif sleutel == "db":
            self._toon(6)
        elif sleutel == "calc":
            self._open_calc()

    def _voeg_in_doc(self, tekst):
        self.writer.voeg_tekst_in(tekst)
        self._toon(1)
        self.raise_(); self.activateWindow()
        self._status(T("ingevoegd"))

    def _status(self, tekst):
        self.statusBar().showMessage(tekst, 6000)

    # ---- menu/werkbalk ----
    def _maak_werkbalk(self):
        bar = QToolBar(); bar.setMovable(False); bar.setIconSize(QSize(20, 20))
        self.addToolBar(bar)
        self.terug_actie = QAction("\u2190  " + T("terug_portaal"), self)
        self.terug_actie.triggered.connect(lambda: self._toon(0))
        bar.addAction(self.terug_actie)
        bar.addSeparator()
        a_writer = QAction(T("tekstverwerker"), self)
        a_writer.triggered.connect(lambda: self._toon(1))
        a_blad = QAction(T("rekenblad"), self)
        a_blad.triggered.connect(lambda: self._toon(2))
        a_kas = QAction(T("kasboek"), self)
        a_kas.triggered.connect(lambda: self._toon(3))
        a_pres = QAction(T("presentatie"), self)
        a_pres.triggered.connect(lambda: self._toon(4))
        a_teken = QAction(T("tekenen"), self)
        a_teken.triggered.connect(lambda: self._toon(5))
        a_db = QAction(T("database"), self)
        a_db.triggered.connect(lambda: self._toon(6))
        a_calc = QAction(T("rekenmachine"), self)
        a_calc.triggered.connect(lambda: self._open_calc())
        bar.addAction(a_writer); bar.addAction(a_blad); bar.addAction(a_kas)
        bar.addAction(a_pres); bar.addAction(a_teken); bar.addAction(a_db); bar.addAction(a_calc)
        leeg = QWidget(); leeg.setSizePolicy(QSizePolicy.Policy.Expanding,
                                             QSizePolicy.Policy.Preferred)
        bar.addWidget(leeg)
        donatie = QAction("\u2665 " + T("donatie"), self)
        donatie.triggered.connect(self._donatie)
        bar.addAction(donatie)

    def _maak_menu(self):
        balk = self.menuBar()
        m_best = balk.addMenu(T("bestand"))
        for tekst, fn, sneltoets in (
            (T("nieuw"), self.writer.nieuw, "Ctrl+N"),
            (T("openen"), self.writer.openen, "Ctrl+O"),
            (T("opslaan"), self.writer.opslaan, "Ctrl+S"),
            (T("opslaan_als"), self.writer.opslaan_als, "Ctrl+Shift+S"),
        ):
            a = QAction(tekst, self); a.triggered.connect(fn)
            if sneltoets:
                a.setShortcut(QKeySequence(sneltoets))
            m_best.addAction(a)
        m_best.addSeparator()
        a_af = QAction(T("afsluiten"), self); a_af.triggered.connect(self.close)
        a_af.setShortcut(QKeySequence("Ctrl+Q")); m_best.addAction(a_af)

        m_beeld = balk.addMenu(T("beeld"))
        for tekst, idx in ((T("portaal"), 0), (T("tekstverwerker"), 1), (T("rekenblad"), 2), (T("kasboek"), 3), (T("presentatie"), 4), (T("tekenen"), 5), (T("database"), 6)):
            a = QAction(tekst, self); a.triggered.connect(lambda _, i=idx: self._toon(i))
            m_beeld.addAction(a)
        a_rm = QAction(T("rekenmachine"), self)
        a_rm.triggered.connect(lambda: self._open_calc())
        m_beeld.addAction(a_rm)

        m_taal = balk.addMenu(T("taal"))
        huidig = self.cfg.get("taal") or "auto"
        for sleutel, label in (("auto", T("taal_auto")), ("nl", "Nederlands"), ("en", "English")):
            a = QAction(label, self); a.setCheckable(True)
            a.setChecked(huidig == sleutel)
            a.triggered.connect(lambda _=False, s=sleutel: self._kies_taal(s))
            m_taal.addAction(a)

        m_help = balk.addMenu(T("help"))
        a_gids = QAction(T("snelgids"), self); a_gids.setShortcut(QKeySequence("F1"))
        a_gids.triggered.connect(lambda: SnelgidsDialoog(self).exec())
        m_help.addAction(a_gids)
        a_over = QAction(T("over"), self); a_over.triggered.connect(self._over)
        m_help.addAction(a_over)

    def _kies_taal(self, sleutel):
        if sleutel == "auto":
            self.cfg.pop("taal", None)
        else:
            self.cfg["taal"] = sleutel
        bewaar_config(self.cfg)
        QMessageBox.information(self, T("taal"), T("taal_herstart"))

    def _donatie(self):
        QMessageBox.information(self, T("donatie"),
                               "DraveOffice is donationware.\n\n"
                               "PayPal: https://paypal.me/roger076\n"
                               "E-mail: service@dravenlock.nl\n\nKira & Dravenlock bedanken je!")

    def _over(self):
        QMessageBox.information(self, T("over"),
                               "%s v%s\n\n%s - lokale, offline office-suite.\n"
                               "Donationware. (c) Dravenlock." % (APP_NAAM, APP_VERSIE, APP_NAAM))

    def closeEvent(self, ev):
        if self.writer._bevestig_verlies():
            self.calc_venster.close()
            ev.accept()
        else:
            ev.ignore()


_QT_VERTALERS = []


def installeer_qt_vertaling(app, taal):
    """Laadt Qt's eigen vertalingen (rechtermuismenu, systeemknoppen in dialogen)."""
    if taal != "nl":
        return
    try:
        pad = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    except Exception:
        return
    for naam in ("qtbase_nl", "qt_nl"):
        t = QTranslator()
        if t.load(naam, pad):
            app.installTranslator(t)
            _QT_VERTALERS.append(t)   # referentie bewaren tegen opruimen


def main():
    global _TAAL
    zorg_voor_mappen()
    # Windows: zorg dat de taakbalk het app-icoon toont i.p.v. het Python-icoon
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Dravenlock.DraveOffice")
        except Exception:
            pass
    cfg = laad_config()
    _TAAL = cfg.get("taal") or detecteer_taal()
    kasboek._TAAL = _TAAL
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAAM)
    app.setWindowIcon(app_icoon())
    installeer_qt_vertaling(app, _TAAL)
    venster = Hoofdvenster(cfg)
    venster.showMaximized()
    if cfg.get("toon_welkom", True):
        WelkomDialoog(venster, cfg).exec()
    try:  # Dravenlock: stille update-check (uit te zetten; Ctrl+Shift+U = met de hand)
        import drave_update
        drave_update.start(venster, 'DraveOffice', APP_VERSIE)
    except Exception:
        pass
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
