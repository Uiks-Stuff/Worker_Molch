# Lastenheft: <Role Panel>

## Ziel
In einem vorher definierten "Willkommens"-Channel kommt eine Nachricht, wo User mit dem click auf einen Button Rollen für sich wählen können (z.b. @DD oder @Heal)

## Funktionen
- F1: Rollen können von Admins und Moderatoren gesetzt werden
- F2: User können Rollen erhalten indem sie auf Buttons klicken innerhalb der Nachricht
- F3: Es gibt eine Standard Nachricht für den Bot, diese kann über /rolepanel setmassage bearbeitet werden.
- F4: Das Modul soll eine eistellbare Hierarchieebene erhalten, wodurch der Bot bei mehreren Nachrichten im Willkommenskanal die NAchrichten Nach Hierarchieebene anordnet (für zukünftige Module welche im Wilkommenchannel posten) Standard: 10

## Befehle (Slash-Commands)
| Befehl | Parameter | Wer darf ihn nutzen? | Was passiert? |
|---|---|---|---|
| /rolepanel start | - | Moderatoren, Admin | fügt die Nachricht in den "willkommenskanal" ein wenn Rollen definiert sind sonst Fehlermeldung, falls kein Channel definiert ist wird "Willkommen" definiert |
| /rolepanel stop | - | Moderatoren, Admin | entfernt die Nachricht aus dem gesetzten Channel |
| /rolepanel setRole | Role [Rolle1, Rolle2, ...] |Moderatoren, Admin|fügt "save" Roles hinzu|
| /rolepanel removeRole | Role [Rolle1, Rolle2, ...] |Moderatoren, Admin|entfernt "save" Roles|
| /rolepanel clear | - | Moderatoren, Admin | entfernt alle gesetzten Rollen in der Nachricht|
| /rolepanel userrole | - | Moderatoren, Admin | fügt eine Rolle zur Auswahl in der Nachticht hinzu oder entfernt sie |
| /rolepanel setLanguage | language |Moderatoren, Admin|Setzt die Sprache des Ausdrucks im Channel|
| /rolepanel setmassage | - | Moderatoren, Admin | bearbeitet die zu verwendende Nachricht im Channel |
| /rolepanel sethierarchie | - | Moderatoren, Admin | setzt die hierarchieebene des Moduls (Standard: 10)

## Daten / Speicherung
Speicherung der setRoles
Speicherung des Willkommenskanals
Speicherung der userroles, also der erwerbbaren Rollen
Speicherung der Nachricht im Channel

## Rahmenbedingungen
- Als eigenes Modul unter `modules/` umsetzen
- Es wird eine sprachdatei benötigt nach folgendem Format:
[DEUTSCH]
 - @everyone Hallo! hier könnt ihr Rollen wählen, was ihr gerne Machen würdet!

Rolle 1
Rolle 2
Rolle ...
 
 Der Ausdruck [DEUTSCH] ist das suchwort für die Sprache, welche mit /rolepanel setLanguage language:DEUTSCH gesetzt wird. beliebig erweiterbar.


## Abnahmekriterien
Woran erkennst du, dass es fertig ist?
- alle /rolepanel Befehle funktionieren wie vorgegeben
- User können sich per knopfdruck Rollen geben und diese wieder entfernen
- beim wechseln der Sprache wird die Nachricht im überwachten Channel angepasst

## Nicht Teil dieser Aufgabe
- …
