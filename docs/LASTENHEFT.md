# Lastenheft: Honeypot Moderator

## Ziel
Er soll Nutzer, welche in einen definierten Channel schreiben vom Server bannen. Der Bann wird in einen Thread des Channel gepostet. Der Thread soll nur für User mit einer bestimmten Servergruppe sichtbar sein. Der Thread enthält die Informationen über User ID, Banngrund und Nachricht.

## Funktionen
- F1: User welche keiner save Role angehören werden gebannt, wenn sie in den überwachten (gesetzten) Channel schreiben
- F2: Es wird ein Ereignisslog in einem Thread des überwachten Channels geführt, wenn ein Bann über den Bot erfolgt
- F3: Im Channel soll eine Infonachricht für Users stehen, welche auf die Honeypot Funktion aufmerksam macht, sowie die Anzahl der gebannten User über den Honeypot anzeigt.

## Befehle (Slash-Commands)
| Befehl | Parameter | Wer darf ihn nutzen? | Was passiert? |
|---|---|---|---|
|/honeypot start| - | Moderatoren, Admin| Startet die Überwachung des Channels, erstellt einen Textchannel "Honeypot", falls kein Channel zum überwachen angegeben ist und überwacht diesen |
|/honeypot stop| - |Moderatoren, Admin|Stoppt die Überwachung des Channels|
|/honeypot status| - |Moderatoren, Admin|gibt den Status des Bots zurück (aktiv / inaktiv), den gesetzten Channel und die gesetzten Save Roles|
|/honeypot channel | ChanelName |Moderatoren, Admin|legt den zu überwachenden Channel fest (maximal einen), ein fehlender Parameter entfernt den gesetzten Channel|
|/honeypot setRole | Role [Rolle1, Rolle2, ...] |Moderatoren, Admin|fügt "save" Roles hinzu|
|/honeypot removeRole | Role [Rolle1, Rolle2, ...] |Moderatoren, Admin|entfernt "save" Roles|
|/honeypot setLanguage|language |Moderatoren, Admin|Setzt die Sprache des Ausdrucks im Channel|


## Daten / Speicherung
Speicherung der setRoles und , sowie des 
Speicherung des zu überwachenden Channels
Speicherung status des Bots (aktiv oder inaktiv)
Speicherung der Anzahl der gebannten User

## Rahmenbedingungen
- Als eigenes Modul unter `modules/` umsetzen
- Es wird eine sprachdatei benötigt nach folgendem Format:
[DEUTSCH]
 - @everyone Hallo! Dieser Channel ist dafür da um jeden Scammer direkt zu bannen der auf dem Server was versucht! Das heißt jeder User der in diesen Channel schreibt, wird direkt GEBANNT 
 - Bans: X
 
 Der Ausdruck [DEUTSCH] ist das suchwort für die Sprache, welche mit /honeypot setLanguage language:DEUTSCH gesetzt wird. beliebig erweiterbar.


## Abnahmekriterien
Woran erkennst du, dass es fertig ist?
- alle /honepot befehle funktionieren wie vorgegeben
- Es werden die User gebannt, welche wärend der Überwachung in den gesetzten Channel Schreiben, außer User mit Rollen
- Thread des zu überwachenden Channels ist nur für Moderatoren und Admins sichtbar
- beim wechseln der Sprache wird die Nachricht im überwachten Channel angepasst.

## Nicht Teil dieser Aufgabe
- …
