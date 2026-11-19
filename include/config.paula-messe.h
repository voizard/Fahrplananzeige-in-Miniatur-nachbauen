// ---------------------------------------------------------------------------
// FERTIGES BEISPIEL: Paula-Modersohn-Platz -> nur Linie 4 nach Messe
//
// Nur noch WLAN eintragen, dann diese Datei als config.h verwenden:
//     cp include/config.paula-messe.h include/config.h
//
// Live geprueft am 19.11.2026: Der Filter liefert 11 Treffer aus 30
// angefragten Abfahrten, alle von Steig 1. Linie 4 Richtung Messe faehrt
// tagsueber etwa alle 10 Minuten.
//
// Hinweis: An dieser Haltestelle faehrt Linie 4 in drei Richtungen --
// 'Vauban', 'Messe' und 'H.-von-Stephan-Str.'. Ohne Richtungsfilter
// waeren alle drei gemischt.
// ---------------------------------------------------------------------------
#pragma once

// --- WLAN ---
#define WIFI_SSID       "DEIN_WLAN"
#define WIFI_PASSWORD   "DEIN_PASSWORT"

// --- Haltestelle: Paula-Modersohn-Platz ---
#define STOP_ID         "de:08311:30651"
#define STOP_NAME       "Paula-Modersohn-Platz"

// --- Anzeige ---
#define MAX_DEPARTURES  2        // nur die naechsten 2, wie die echten Anzeigen
#define REFRESH_SECONDS 30       // Aktualisierungsintervall
#define SHOW_TRAM_ONLY  true     // nur Stadtbahn (motType 4)
#define REQUEST_LIMIT   30       // vor dem Filtern angefragte Abfahrten

// --- Darstellung: DFI-Look wie die Anzeigen an der Haltestelle ---

// Blinktakt des Tram-Symbols bei Einfahrt (Millisekunden)
#define BLINK_MS        600
#define DISPLAY_STYLE   1

// Laufschrift der Verspaetungsmeldung unten: Millisekunden pro Schritt.
#define LAUF_MS         120

// --- Filter: welche Linien angezeigt werden ---
// Bis zu zwei Filter. Tram und Bus werden nach Abfahrtszeit GEMISCHT.
// Eine leere Linie ("") schaltet den jeweiligen Filter ab.
#define FILTER_LINE       "4"
#define FILTER_DIRECTION  "Messe"

#define FILTER_LINE2      ""             // kein zweiter Filter
#define FILTER_DIRECTION2 ""

// --- Zeitzone ---
#define TZ_INFO         "CET-1CEST,M3.5.0,M10.5.0/3"  // Europe/Berlin
