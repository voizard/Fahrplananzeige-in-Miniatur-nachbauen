// ---------------------------------------------------------------------------
// Strassenbahn-Abfahrten auf dem LilyGO T-Display S3
//
// Datenquelle: NVBW/EFA-Endpunkt Baden-Wuerttemberg (www.efa-bw.de).
// Liefert echte Echtzeit-Abfahrten der VAG Freiburg als JSON, ohne API-Key.
//
// Zwei Darstellungen, umschaltbar ueber DISPLAY_STYLE in config.h:
//   1 = VAG-DFI-Look (orange LED-Schrift auf dunklem Grund, wie die
//       Anzeigen an den Haltestellen)
//   0 = Farblook (farbige Linien-Badges)
// ---------------------------------------------------------------------------
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Arduino_GFX_Library.h>
#include <time.h>
#include <ctype.h>   // tolower() fuer den Richtungsfilter

#include "config.h"

// Aeltere/alternative config-Dateien kennen die neuen Werte noch nicht.
// Ohne diese Fallbacks bricht der Build ab, sobald man z. B.
// config.littenweiler.h ueber config.h kopiert.
#ifndef FILTER_LINE2
#define FILTER_LINE2      ""
#endif
#ifndef FILTER_DIRECTION2
#define FILTER_DIRECTION2 ""
#endif
#ifndef LAUF_MS
#define LAUF_MS           120
#endif

// --- Display: 1.9" ST7789 am 8-Bit-Parallelbus (Werte aus dem LilyGO-Repo) ---
#define PIN_LCD_POWER 15   // muss HIGH sein, sonst bleibt das Panel dunkel
#define PIN_LCD_BL    38

Arduino_DataBus *bus = new Arduino_ESP32PAR8Q(
    7 /* DC */, 6 /* CS */, 8 /* WR */, 9 /* RD */,
    39, 40, 41, 42, 45, 46, 47, 48 /* D0..D7 */);

// Rotation 1 = Querformat 320x170. Offsets 35/35 sind IPS-typisch.
Arduino_GFX *gfx = new Arduino_ST7789(
    bus, 5 /* RST */, 1 /* rotation */, true /* IPS */, 170, 320, 35, 0, 35, 0);

// --- HTTPS: GlobalSign Root CA - R6 (Aussteller von *.efa-bw.de) ---
static const char ROOT_CA[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIIFgzCCA2ugAwIBAgIORea7A4Mzw4VlSOb/RVEwDQYJKoZIhvcNAQEMBQAwTDEg
MB4GA1UECxMXR2xvYmFsU2lnbiBSb290IENBIC0gUjYxEzARBgNVBAoTCkdsb2Jh
bFNpZ24xEzARBgNVBAMTCkdsb2JhbFNpZ24wHhcNMTQxMjEwMDAwMDAwWhcNMzQx
MjEwMDAwMDAwWjBMMSAwHgYDVQQLExdHbG9iYWxTaWduIFJvb3QgQ0EgLSBSNjET
MBEGA1UEChMKR2xvYmFsU2lnbjETMBEGA1UEAxMKR2xvYmFsU2lnbjCCAiIwDQYJ
KoZIhvcNAQEBBQADggIPADCCAgoCggIBAJUH6HPKZvnsFMp7PPcNCPG0RQssgrRI
xutbPK6DuEGSMxSkb3/pKszGsIhrxbaJ0cay/xTOURQh7ErdG1rG1ofuTToVBu1k
ZguSgMpE3nOUTvOniX9PeGMIyBJQbUJmL025eShNUhqKGoC3GYEOfsSKvGRMIRxD
aNc9PIrFsmbVkJq3MQbFvuJtMgamHvm566qjuL++gmNQ0PAYid/kD3n16qIfKtJw
LnvnvJO7bVPiSHyMEAc4/2ayd2F+4OqMPKq0pPbzlUoSB239jLKJz9CgYXfIWHSw
1CM69106yqLbnQneXUQtkPGBzVeS+n68UARjNN9rkxi+azayOeSsJDa38O+2HBNX
k7besvjihbdzorg1qkXy4J02oW9UivFyVm4uiMVRQkQVlO6jxTiWm05OWgtH8wY2
SXcwvHE35absIQh1/OZhFj931dmRl4QKbNQCTXTAFO39OfuD8l4UoQSwC+n+7o/h
bguyCLNhZglqsQY6ZZZZwPA1/cnaKI0aEYdwgQqomnUdnjqGBQCe24DWJfncBZ4n
WUx2OVvq+aWh2IMP0f/fMBH5hc8zSPXKbWQULHpYT9NLCEnFlWQaYw55PfWzjMpY
rZxCRXluDocZXFSxZba/jJvcE+kNb7gu3GduyYsRtYQUigAZcIN5kZeR1Bonvzce
MgfYFGM8KEyvAgMBAAGjYzBhMA4GA1UdDwEB/wQEAwIBBjAPBgNVHRMBAf8EBTAD
AQH/MB0GA1UdDgQWBBSubAWjkxPioufi1xzWx/B/yGdToDAfBgNVHSMEGDAWgBSu
bAWjkxPioufi1xzWx/B/yGdToDANBgkqhkiG9w0BAQwFAAOCAgEAgyXt6NH9lVLN
nsAEoJFp5lzQhN7craJP6Ed41mWYqVuoPId8AorRbrcWc+ZfwFSY1XS+wc3iEZGt
Ixg93eFyRJa0lV7Ae46ZeBZDE1ZXs6KzO7V33EByrKPrmzU+sQghoefEQzd5Mr61
55wsTLxDKZmOMNOsIeDjHfrYBzN2VAAiKrlNIC5waNrlU/yDXNOd8v9EDERm8tLj
vUYAGm0CuiVdjaExUd1URhxN25mW7xocBFymFe944Hn+Xds+qkxV/ZoVqW/hpvvf
cDDpw+5CRu3CkwWJ+n1jez/QcYF8AOiYrg54NMMl+68KnyBr3TsTjxKM4kEaSHpz
oHdpx7Zcf4LIHv5YGygrqGytXm3ABdJ7t+uA/iU3/gKbaKxCXcPu9czc8FB10jZp
nOZ7BN9uBmm23goJSFmH63sUYHpkqmlD75HHTOwY3WzvUy2MmeFe8nI+z1TIvWfs
pA9MRf/TuTAjB0yPEL+GltmZWrSZVxykzLsViVO6LAUP5MSeGbEYNNVMnbrt9x+v
JJUEeKgDu+6B5dpffItKoZB0JaezPkvILFa9x8jvOOJckvB595yEunQtYQEgfn7R
8k8HWV+LLUNS60YMlOH1Zkd5d9VUWx+tJDfLRVpOoERIyNiwmcUVhAn21klJwGW4
5hpxbqCo8YLoRT5s1gLXCmeDBVrJpBA=
-----END CERTIFICATE-----
)EOF";

// --- Farben ---------------------------------------------------------------
// DFI-Look: Werte aus dem Foto der VAG-Anzeige abgenommen.
#define C_DFI_BG      0x18E3   // dunkles Blaugrau (Hintergrund)
#define C_DFI_HEAD    0x2124   // Kopfzeile, etwas heller
#define C_DFI_RULE    0x4208   // Trennlinien
#define C_DFI_ORANGE  0xFB60   // LED-Orange (#FF6E00)
#define C_DFI_WHITE   0xFFFF   // Kopfzeile + Spaltentitel
#define C_DFI_DIM     0x8C71   // Nebentext (Steig, Uhrzeit)

// Farblook (Alternative)
#define C_BG    0x1082
#define C_BAR   0x2945
#define C_TEXT  0xFFFF
#define C_DIM   0x8C71
#define C_GOOD  0x2E8B
#define C_SOON  0xFD20
#define C_LATE  0xF800

// Untere Laufschrift fuer Verspaetungen -- wie die durchlaufende Meldung
// an den echten DFIs. Nur sichtbar, wenn es wirklich eine Verspaetung gibt.
#define MELD_H      20               // Hoehe des Streifens
#define MELD_Y      (170 - MELD_H)   // Oberkante (150)
#define MELD_TEXT_Y (MELD_Y + 2)     // Textoberkante (Groesse 2 = 16 px)
#define MELD_TX     12               // Zeichenbreite bei Textgroesse 2

struct Abfahrt {
  char linie[8];
  char richtung[48];
  int  minuten;
  char uhrzeit[6];
  char steig[6];
  int  verspaetung;   // Minuten (Feld servingLine.delay)
  bool tram;
};

static Abfahrt abfahrten[MAX_DEPARTURES];
static int  anzahl = 0;
static char serverZeit[6] = "--:--";
static bool letzterAbrufOk = false;

// Zuege, die jetzt einfahren -- dort blinkt statt der Minuten ein Symbol.
#define MAX_BLINK 4
struct BlinkSlot { int x, y; bool an; };
static BlinkSlot blinkSlots[MAX_BLINK];
static int blinkCount = 0;

// Laufschrift unten: Text, Pixelbreite und aktueller Scroll-Versatz.
static char meldung[200] = "";
static int  meldBreite = 0;
static int  meldOffset = 0;

// ------------------------------------------------------------------ Zeichnen

static uint16_t linienFarbe(const char *linie) {
  static const uint16_t palette[] = {0xF800, 0xFD20, 0x07E0, 0x001F,
                                     0xF81F, 0x07FF, 0xFFE0};
  return palette[abs(atoi(linie)) % 7];
}

static void zeichneKopfzeileDFI() {
  gfx->fillRect(0, 0, 320, 22, C_DFI_HEAD);
  gfx->setTextColor(C_DFI_WHITE);
  gfx->setTextSize(2);
  gfx->setCursor(6, 4);
  gfx->print(STOP_NAME);
  gfx->setTextSize(1);
  gfx->setCursor(276, 8);
  gfx->print(serverZeit);

  // Spaltentitel
  gfx->setTextColor(C_DFI_WHITE);
  gfx->setTextSize(1);
  gfx->setCursor(8, 25);
  gfx->print("Linie");
  gfx->drawFastVLine(44, 24, 8, C_DFI_RULE);
  gfx->setCursor(50, 25);
  gfx->print("Ziel");
  gfx->setCursor(266, 25);
  gfx->print("Abfahrt");
  gfx->drawFastHLine(0, 36, 320, C_DFI_RULE);
}

// ------------------------------------------------------------------- Uhr
// Die Uhr laeuft aus der internen Uhr (NTP), nicht aus der Serverzeit des
// Abrufs. Nur so tickt sie sekundengenau weiter, auch wenn ein Abruf
// fehlschlaegt oder die 30 s bis zum naechsten Abruf noch laufen.
static bool uhrVonNTP(char *out, size_t n) {
  struct tm t;
  if (!getLocalTime(&t, 0)) return false;
  if (t.tm_year < 120) return false;          // Jahr < 2020 -> noch nicht gesetzt
  snprintf(out, n, "%02d:%02d", t.tm_hour, t.tm_min);
  return true;
}

// Nur das kleine Uhrfeld neu zeichnen, nicht die ganze Kopfzeile.
static void zeichneUhr() {
#if DISPLAY_STYLE == 1
  gfx->fillRect(270, 5, 48, 13, C_DFI_HEAD);
  gfx->setTextColor(C_DFI_WHITE);
  gfx->setTextSize(1);
  gfx->setCursor(276, 8);
#else
  gfx->fillRect(274, 4, 44, 12, C_BAR);
  gfx->setTextColor(C_TEXT);
  gfx->setTextSize(1);
  gfx->setCursor(278, 7);
#endif
  gfx->print(serverZeit);
}

// Neu zeichnen nur, wenn sich die Minute wirklich geaendert hat.
static void aktualisiereUhr() {
  char neu[6];
  if (!uhrVonNTP(neu, sizeof(neu))) return;   // NTP noch nicht bereit
  if (strcmp(neu, serverZeit) == 0) return;
  memcpy(serverZeit, neu, sizeof(neu));
  zeichneUhr();
}

// Kleines Tram-Piktogramm -- erscheint blinkend, wenn der Zug jetzt einfaehrt.
// Box 20x16 px. Aus Grundformen gezeichnet, weil die GFX-Schrift keine
// Sonderzeichen kennt.
static const int TRAM_W = 30;
static const int TRAM_H = 16;

static void zeichneTramSymbol(int x, int y, bool an) {
  if (!an) return;
  const uint16_t col = C_DFI_ORANGE;
  gfx->drawFastHLine(x + 9, y, 12, col);            // Stromabnehmer
  gfx->drawFastVLine(x + 15, y, 3, col);            // Haltestange
  gfx->fillRoundRect(x + 1, y + 3, 28, 9, 2, col);  // Wagenkasten (Rechteck)
  gfx->fillRect(x + 3, y + 5, 24, 3, C_DFI_BG);     // Fensterband

  gfx->fillCircle(x + 6, y + 14, 2, col);           // Raeder (drei)
  gfx->fillCircle(x + 15, y + 14, 2, col);
  gfx->fillCircle(x + 24, y + 14, 2, col);
}

// Eine Abfahrtszeile im DFI-Stil zeichnen und die verbrauchte Hoehe
// zurueckgeben. tsize = 3 (gross, wenn nur wenige Zeilen anstehen) oder 2.
static int zeichneZeileDFI(const Abfahrt &a, int y, int tsize) {
  const int cw = 6 * tsize;      // Zeichenbreite
  const int ch = 8 * tsize;      // Zeichenhoehe

  char kombi[72];
  snprintf(kombi, sizeof(kombi), "%s %s", a.linie, a.richtung);

  // Rechts steht entweder die Minutenzahl oder -- wenn der Zug jetzt
  // einfaehrt -- ein blinkendes Tram-Symbol, wie an den echten Anzeigen.
  // Bewusst NUR bei genau 0 (so gewuenscht): bei 1 min steht noch die
  // Zahl. Nicht auf <= umstellen.
  const bool einfahrt = (a.minuten == 0);

  char zahl[4];
  snprintf(zahl, sizeof(zahl), "%d", a.minuten < 0 ? 0 : a.minuten);
  int wnum = strlen(zahl) * cw;
  int wmin = 3 * 6;                       // "min" immer in Groesse 1
  int xmin = 318 - (wnum + 4 + wmin);
  if (einfahrt) xmin = 318 - TRAM_W;      // Platz fuer das Symbol

  // Passt der Text in grosser Schrift nicht, eine Nummer kleiner versuchen.
  int maxchars = (xmin - 12) / cw;
  if ((int)strlen(kombi) > maxchars && tsize > 2) {
    return zeichneZeileDFI(a, y, 2);
  }

  gfx->setTextColor(C_DFI_ORANGE);

  int hoehe = ch;
  if ((int)strlen(kombi) <= maxchars) {
    gfx->setTextSize(tsize);
    gfx->setCursor(6, y);
    gfx->print(kombi);
  } else {
    // zweizeilig, wie im Original bei langen Bus-Zielen. Am Wortende
    // umbrechen, sonst wird z. B. "Freiburg Hauptbahnhof" zu "Freiburg
    // Hauptbahn" + "hof" zerhackt.
    int sp = maxchars;
    while (sp > 0 && kombi[sp] != ' ') sp--;
    if (sp <= 0) sp = maxchars;          // ein einziges langes Wort: hart trennen
    char l1[40];
    snprintf(l1, sizeof(l1), "%.*s", sp, kombi);
    gfx->setTextSize(tsize);
    gfx->setCursor(6, y);
    gfx->print(l1);
    gfx->setTextSize(1);
    gfx->setCursor(6, y + ch + 3);
    const char *rest = kombi + sp;
    while (*rest == ' ') rest++;
    gfx->print(rest);
    hoehe = ch + 3 + 8;
  }

  if (einfahrt) {
    int ytop = y + (ch - TRAM_H) / 2;
    zeichneTramSymbol(xmin, ytop, true);
    if (blinkCount < MAX_BLINK) {
      blinkSlots[blinkCount].x = xmin;
      blinkSlots[blinkCount].y = ytop;
      blinkSlots[blinkCount].an = true;
      blinkCount++;
    }
  } else {
    gfx->setTextSize(tsize);
    gfx->setCursor(xmin, y);
    gfx->print(zahl);
    gfx->setTextSize(1);
    gfx->setCursor(xmin + wnum + 4, y + (ch - 8) / 2);
    gfx->print("min");
  }

  return hoehe;
}

// Hoehe einer Zeile vorab berechnen -- gleiche Logik wie zeichneZeileDFI,
// aber ohne zu zeichnen. Noetig, um den Block vertikal zu zentrieren.
static int zeileHoehe(const Abfahrt &a, int tsize) {
  const int cw = 6 * tsize;
  const int ch = 8 * tsize;

  char kombi[72];
  snprintf(kombi, sizeof(kombi), "%s %s", a.linie, a.richtung);
  int maxchars = (318 - (20 + 4 + 18) - 12) / cw;   // groesster Fall rechts
  if ((int)strlen(kombi) > maxchars && tsize > 2) {
    return zeileHoehe(a, 2);
  }
  return ((int)strlen(kombi) <= maxchars) ? ch : ch + 3 + 8;
}

static void zeichneDFI() {
  zeichneKopfzeileDFI();
  gfx->fillRect(0, 37, 320, 170 - 37, C_DFI_BG);

  if (anzahl == 0) {
    gfx->setTextColor(C_DFI_ORANGE);
    gfx->setTextSize(2);
    gfx->setCursor(10, 80);
    gfx->print("keine Abfahrten");
    return;
  }

  // Wie an den echten Anzeigen: stehen nur ein oder zwei Abfahrten an,
  // wird die Schrift groesser (3x statt 2x) und der Platz besser genutzt.
  // Steht unten eine Laufschrift, ruecken die Abfahrtszeilen nach oben.
  const int unten = meldung[0] ? MELD_Y : 170;

  const bool gross = (anzahl <= 2);
  const int tsize  = gross ? 3 : 2;
  const int gap    = gross ? 14 : 6;

  // Gesamthoehe ermitteln und den Block im Anzeigebereich (37..170)
  // vertikal zentrieren.
  int gesamt = 0;
  for (int i = 0; i < anzahl; i++) {
    gesamt += zeileHoehe(abfahrten[i], tsize);
    if (i + 1 < anzahl) gesamt += gap;
  }
  const int bereich = unten - 37;
  int y = 37 + (bereich - gesamt) / 2;
  if (y < 40) y = 40;

  for (int i = 0; i < anzahl; i++) {
    int h = zeichneZeileDFI(abfahrten[i], y, tsize);
    y += h + gap;
    if (y > unten - 2) break;
  }
}

static void zeichneKlassisch() {
  gfx->fillRect(0, 0, 320, 22, C_BAR);
  gfx->setTextColor(C_TEXT);
  gfx->setTextSize(2);
  gfx->setCursor(6, 4);
  gfx->print(STOP_NAME);
  gfx->setTextSize(1);
  gfx->setCursor(278, 7);
  gfx->print(serverZeit);

  gfx->fillRect(0, 22, 320, 148, C_BG);
  if (anzahl == 0) {
    gfx->setTextColor(C_LATE);
    gfx->setTextSize(2);
    gfx->setCursor(10, 80);
    gfx->print("keine Abfahrten");
    return;
  }

  int y = 26;
  for (int i = 0; i < anzahl; i++) {
    Abfahrt &a = abfahrten[i];

    uint16_t fc = linienFarbe(a.linie);
    gfx->fillRoundRect(4, y, 34, 20, 4, fc);
    gfx->setTextColor(0x0000);
    gfx->setTextSize(2);
    gfx->setCursor(atoi(a.linie) >= 10 ? 8 : 13, y + 3);
    gfx->print(a.linie);

    char richtung[19];
    snprintf(richtung, sizeof(richtung), "%.17s", a.richtung);
    if (strlen(a.richtung) > 17) { richtung[15] = '.'; richtung[16] = '.'; richtung[17] = 0; }
    gfx->setTextColor(C_TEXT);
    gfx->setTextSize(2);
    gfx->setCursor(44, y + 3);
    gfx->print(richtung);

    uint16_t mc = a.minuten < 5 ? C_GOOD : (a.minuten < 10 ? C_SOON : C_LATE);
    gfx->setTextColor(mc);
    gfx->setTextSize(2);
    char buf[8];
    snprintf(buf, sizeof(buf), "%2d", a.minuten);
    gfx->setCursor(258, y + 3);
    gfx->print(buf);
    gfx->setTextColor(C_DIM);
    gfx->setTextSize(1);
    gfx->setCursor(288, y + 6);
    gfx->print("min");

    gfx->setTextColor(C_DIM);
    gfx->setTextSize(1);
    gfx->setCursor(44, y + 14);
    gfx->print("Steig ");
    gfx->print(a.steig[0] ? a.steig : "-");
    gfx->setCursor(150, y + 14);
    gfx->print(a.uhrzeit);
    if (a.verspaetung > 0) { gfx->print("  +"); gfx->print(a.verspaetung); gfx->print(" min"); }

    y += 23;
    if (y > 150) break;
  }
}

// Laufschrift unten zeichnen. Der Text startet rechts ausserhalb des Bildes
// und wandert nach links. drawChar() prueft die Bildgrenzen selbst, der Text
// darf also teilweise ausserhalb liegen.
static void zeichneMeldung() {
  if (!meldung[0]) return;
  gfx->drawFastHLine(0, MELD_Y - 1, 320, C_DFI_RULE);
  gfx->fillRect(0, MELD_Y, 320, MELD_H, C_DFI_BG);
  gfx->setTextColor(C_DFI_ORANGE);
  gfx->setTextSize(2);
  gfx->setCursor(320 - meldOffset, MELD_TEXT_Y);
  gfx->print(meldung);
}

// Aus den angezeigten Abfahrten die Verspaetungsmeldung bauen. Gibt es keine
// Verspaetung, bleibt der Text leer und der Streifen verschwindet.
static void baueMeldung() {
  meldung[0] = 0;
  char *p = meldung;
  size_t rest = sizeof(meldung);
  for (int i = 0; i < anzahl; i++) {
    if (abfahrten[i].verspaetung <= 0) continue;
    char teil[72];
    snprintf(teil, sizeof(teil), "%s %s +%d min",
             abfahrten[i].linie, abfahrten[i].richtung,
             abfahrten[i].verspaetung);
    int n = snprintf(p, rest, "%s%s",
                     (p == meldung ? "" : "   +++   "), teil);
    if (n < 0 || (size_t)n >= rest) break;
    p += n;
    rest -= (size_t)n;
  }
  meldBreite = (int)strlen(meldung) * MELD_TX;
  meldOffset = 0;
}

static void zeichneListe() {
#if DISPLAY_STYLE == 1
  zeichneDFI();
  zeichneMeldung();
#else
  zeichneKlassisch();
#endif
}

static void zeigeStatus(const char *text) {
#if DISPLAY_STYLE == 1
  gfx->fillRect(0, 37, 320, 133, C_DFI_BG);
  gfx->setTextColor(C_DFI_ORANGE);
#else
  gfx->fillRect(0, 22, 320, 148, C_BG);
  gfx->setTextColor(C_TEXT);
#endif
  gfx->setTextSize(2);
  gfx->setCursor(10, 80);
  gfx->print(text);
}

// Wenn der Zugang scheitert: einmal scannen und die gefundenen Netze
// auflisten. Das verraet sofort, ob der eigene Hotspot ueberhaupt im
// 2,4-GHz-Band sendet -- der ESP32 kann nur 2,4 GHz.
static void zeigeWlanDiagnose() {
  int n = WiFi.scanNetworks(false, true);   // synchron, auch versteckte
#if DISPLAY_STYLE == 1
  gfx->fillRect(0, 37, 320, 133, C_DFI_BG);
  gfx->setTextColor(C_DFI_ORANGE);
#else
  gfx->fillRect(0, 22, 320, 148, C_BG);
  gfx->setTextColor(C_TEXT);
#endif
  gfx->setTextSize(1);
  gfx->setCursor(8, 40);
  gfx->print("kein Zugang -- gefundene Netze (2,4 GHz):");
  if (n <= 0) {
    gfx->setCursor(8, 56);
    gfx->print("keines. Hotspot laeuft wohl auf 5 GHz.");
  } else {
    int y = 54;
    for (int i = 0; i < n && i < 7; i++) {
      char z[44];
      snprintf(z, sizeof(z), "%s (%d dBm, K%d)",
               WiFi.SSID(i).c_str(), WiFi.RSSI(i), WiFi.channel(i));
      gfx->setCursor(8, y);
      gfx->print(z);
      y += 11;
    }
  }
  Serial.printf("Scan: %d Netze\n", n);
  for (int i = 0; i < n; i++)
    Serial.printf("  %s  %d dBm  Kanal %d\n",
                  WiFi.SSID(i).c_str(), WiFi.RSSI(i), WiFi.channel(i));
  WiFi.scanDelete();
}


// -------------------------------------------------------------- Daten holen

// Gross-/Kleinschreibung egal: prueft, ob ``nadel`` in ``heuhaufen`` steckt.
static bool enthaelt(const char *heuhaufen, const char *nadel) {
  if (!nadel || !nadel[0]) return true;
  if (!heuhaufen) return false;
  char h[64], n[64];
  snprintf(h, sizeof(h), "%s", heuhaufen);
  snprintf(n, sizeof(n), "%s", nadel);
  for (char *p = h; *p; p++) *p = tolower(*p);
  for (char *p = n; *p; p++) *p = tolower(*p);
  return strstr(h, n) != nullptr;
}

// Lange Ziele abkuerzen. "Hauptbahnhof" ist auf 320 px zu lang und wurde
// sonst zweizeilig in kleiner Schrift gequetscht -- kaum lesbar. Die Tabelle
// laesst sich leicht erweitern; laengste Form immer zuerst, sonst greift
// z. B. "Bahnhof" vor "Hauptbahnhof".
struct Kuerzung { const char *lang; const char *kurz; };
static const Kuerzung KUERZUNGEN[] = {
    {"Hauptbahnhof", "Hbf"},
    {"Bahnhof",      "Bf"},
};

// Alle Vorkommen von lang durch kurz ersetzen. kurz darf hoechstens so lang
// sein wie lang, dann passt das Ergebnis immer in denselben Puffer.
// Nur ganze Woerter ersetzen: sonst wuerde "Bahnhofstrasse" zu "Bfstrasse".
static void ersetze(char *buf, const char *lang, const char *kurz) {
  const size_t ll = strlen(lang), kl = strlen(kurz);
  if (kl > ll) return;
  char *p = buf;
  while ((p = strstr(p, lang)) != nullptr) {
    char *vor = p, *nach = p + ll;
    // Steht direkt ein Buchstabe davor oder dahinter, ist es ein laengeres
    // Wort und wird nicht angetastet.
    bool wortAnfang = (p == buf) || !isalpha((unsigned char)p[-1]);
    bool wortEnde   = !isalpha((unsigned char)*nach);
    if (!(wortAnfang && wortEnde)) { p += ll; continue; }
    (void)vor;
    memmove(nach + kl - ll, nach, strlen(nach) + 1);
    memcpy(p, kurz, kl);
    p += kl;
  }
}

static void kuerzeZiel(char *buf) {
  for (const Kuerzung &k : KUERZUNGEN) ersetze(buf, k.lang, k.kurz);
}

// Der EFA-Server liefert ALLE Zahlen als Text ("countdown":"2", nicht 2).
// ArduinoJson gibt bei einem Typ-Mismatch den Standardwert zurueck, also
// stillschweigend -1 bzw. 0 -- deshalb lief die Anzeige auf "0 min" fest.
// Diese Funktion liest beide Formen und ist damit gegen beide Faelle sicher.
static int zahlAus(JsonVariantConst v, int standard) {
  if (v.is<int>()) return v.as<int>();
  const char *t = v.as<const char *>();
  return t ? atoi(t) : standard;
}

static bool holeAbfahrten() {
  char url[320];
  snprintf(url, sizeof(url),
           "https://www.efa-bw.de/nvbw/XML_DM_REQUEST"
           "?outputFormat=JSON&type_dm=stopID&name_dm=%s"
           "&mode=direct&useRealtime=1&limit=%d&depType=stopEvents"
           "&coordOutputFormat=WGS84%%5Bdd.ddddd%%5D",
           STOP_ID, REQUEST_LIMIT);

  WiFiClientSecure client;
  client.setCACert(ROOT_CA);
  client.setTimeout(12);

  HTTPClient https;
  if (!https.begin(client, url)) return false;
  https.setTimeout(12000);
  int code = https.GET();
  if (code != HTTP_CODE_OK) {
    Serial.printf("HTTP %d\n", code);
    https.end();
    return false;
  }
  String payload = https.getString();
  https.end();

  // Nur die benoetigten Felder behalten -- spart RAM
  JsonDocument filter;
  JsonObject f0 = filter["departureList"].add<JsonObject>();
  f0["countdown"] = true;
  f0["platform"] = true;
  f0["realDateTime"] = true;
  JsonObject fs = f0["servingLine"].to<JsonObject>();
  fs["number"] = true; fs["direction"] = true; fs["motType"] = true;
  fs["delay"] = true;
  filter["parameters"][0]["name"] = true;
  filter["parameters"][0]["value"] = true;

  JsonDocument doc;
  DeserializationError err =
      deserializeJson(doc, payload, DeserializationOption::Filter(filter));
  if (err) {
    Serial.printf("JSON: %s\n", err.c_str());
    return false;
  }

  // Die Serverzeit dient nur als Rueckfall, solange die NTP-Uhr noch nicht
  // steht. Sobald NTP laeuft, fuehrt aktualisiereUhr() die Anzeige -- sonst
  // wuerden sich beide Quellen im Minutentakt gegenseitig ueberschreiben.
  char ntpProbe[6];
  bool ntpLaeuft = uhrVonNTP(ntpProbe, sizeof(ntpProbe));
  for (JsonObject p : doc["parameters"].as<JsonArray>()) {
    if (ntpLaeuft) break;
    if (strcmp(p["name"] | "", "serverTime") == 0) {
      const char *t = p["value"] | "";
      const char *hhmm = strchr(t, 'T');
      if (hhmm && strlen(hhmm) >= 6) {
        memcpy(serverZeit, hhmm + 1, 5);
        serverZeit[5] = 0;
      }
    }
  }

  anzahl = 0;
  for (JsonObject e : doc["departureList"].as<JsonArray>()) {
    if (anzahl >= MAX_DEPARTURES) break;
    JsonObject sl = e["servingLine"];
    bool tram = strcmp(sl["motType"] | "0", "4") == 0;   // 4 = Stadtbahn
    if (SHOW_TRAM_ONLY && !tram) continue;

    const char *linie = sl["number"] | "?";
    const char *richtung = sl["direction"] | "";

    // Zwei Filter, Tram und Bus werden nach Abfahrtszeit GEMISCHT -- die
    // Reihenfolge kommt vom Server. Ein Filter passt, dann wird die Abfahrt
    // uebernommen. Leere Linie ("") schaltet den jeweiligen Filter ab.
    bool passt = false;
    if (FILTER_LINE[0] && strcmp(linie, FILTER_LINE) == 0 &&
        enthaelt(richtung, FILTER_DIRECTION)) passt = true;
    if (!passt && FILTER_LINE2[0] && strcmp(linie, FILTER_LINE2) == 0 &&
        enthaelt(richtung, FILTER_DIRECTION2)) passt = true;
    if (!passt) continue;

    Abfahrt &a = abfahrten[anzahl];
    snprintf(a.linie, sizeof(a.linie), "%s", linie);
    // Erst nach dem Filtern kuerzen: der Filter vergleicht mit dem
    // Originaltext des Servers ("Hauptbahnhof").
    snprintf(a.richtung, sizeof(a.richtung), "%s", richtung);
    kuerzeZiel(a.richtung);
    a.minuten = zahlAus(e["countdown"], -1);
    a.tram = tram;

    JsonObject rt = e["realDateTime"];
    snprintf(a.uhrzeit, sizeof(a.uhrzeit), "%02d:%02d",
             zahlAus(rt["hour"], 0), zahlAus(rt["minute"], 0));
    snprintf(a.steig, sizeof(a.steig), "%s", (const char *)(e["platform"] | ""));
    a.verspaetung = zahlAus(sl["delay"], 0);
    anzahl++;
  }
  baueMeldung();
  return true;
}

static bool verbindeWLAN() {
  if (WiFi.status() == WL_CONNECTED) return true;
  zeigeStatus("WLAN ...");
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 20000) delay(250);
  bool ok = (WiFi.status() == WL_CONNECTED);
  // Statuscode ist aussagekraeftig: 1 = SSID nicht gefunden (z. B. 5 GHz),
  // 4 = Verbindung fehlgeschlagen (meist falsches Passwort), 6 = getrennt.
  Serial.printf("WLAN: %s (Status %d)\n", ok ? "ok" : "fehlt", (int)WiFi.status());
  return ok;
}

static void aktualisiere() {
  static bool diagnoseGezeigt = false;
  blinkCount = 0;
  if (!verbindeWLAN()) {
    // Beim ersten Fehlschlag die Netze auflisten, danach nur die kurze
    // Meldung -- ein Scan bei jedem Durchlauf waere unnoetig langsam.
    if (!diagnoseGezeigt) { zeigeWlanDiagnose(); diagnoseGezeigt = true; }
    else zeigeStatus("kein WLAN");
    return;
  }
  diagnoseGezeigt = false;
  if (holeAbfahrten()) {
    letzterAbrufOk = true;
    zeichneListe();
  } else if (!letzterAbrufOk) {
    zeigeStatus("keine Daten");
  }
}

void setup() {
  Serial.begin(115200);

  // Panel mit Strom versorgen, dann Backlight
  pinMode(PIN_LCD_POWER, OUTPUT);
  digitalWrite(PIN_LCD_POWER, HIGH);
  pinMode(PIN_LCD_BL, OUTPUT);
  digitalWrite(PIN_LCD_BL, HIGH);

  gfx->begin();
  gfx->fillScreen(C_DFI_BG);

  zeigeStatus("starte ...");
  configTzTime(TZ_INFO, "pool.ntp.org", "time.nist.gov");
  aktualisiere();
}

void loop() {
  aktualisiere();

  // Waehrend der Wartezeit bis zum naechsten Abruf das Einfahrts-Symbol
  // blinken lassen. Nur der kleine Symbolbereich wird neu gezeichnet,
  // nicht die ganze Liste.
  uint32_t ende = millis() + (uint32_t)REFRESH_SECONDS * 1000UL;
  uint32_t tBlink = millis(), tLauf = millis();
  bool phase = true;
  while ((int32_t)(millis() - ende) < 0) {
    delay(20);
    uint32_t now = millis();

    // Einfahrts-Symbol blinken lassen -- nur der kleine Symbolbereich.
    if (now - tBlink >= (uint32_t)BLINK_MS) {
      tBlink = now;
      phase = !phase;
      for (int i = 0; i < blinkCount; i++) {
        gfx->fillRect(blinkSlots[i].x - 1, blinkSlots[i].y - 1,
                      TRAM_W + 2, TRAM_H + 2, C_DFI_BG);
        if (phase) zeichneTramSymbol(blinkSlots[i].x, blinkSlots[i].y, true);
      }
    }

    // Verspaetungsmeldung unten durchlaufen lassen.
    if (meldung[0] && now - tLauf >= (uint32_t)LAUF_MS) {
      tLauf = now;
      meldOffset++;
      if (meldOffset > 320 + meldBreite) meldOffset = 0;
      zeichneMeldung();
    }

    aktualisiereUhr();   // Uhr laeuft auch waehrend der Wartezeit weiter
  }
}
