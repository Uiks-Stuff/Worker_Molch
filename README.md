# Worker_Molch – modularer Discord-Bot

Ein selbst gehosteter, modularer Discord-Bot auf Basis von **Python 3.13**, **discord.py 2.7.1** und **Docker Compose**. Der Bot läuft auf einem eigenen Ubuntu-Server und kann um einzelne, unabhängig aktivierbare Module erweitert werden.

Diese Anleitung ist bewusst Schritt für Schritt geschrieben. Sie beginnt bei einem frischen Ubuntu-Server, auf dem Docker noch nicht installiert ist.

> **Vorgesehene Umgebung dieses Projekts**
> - Ubuntu Server 26.04 LTS (64-Bit / `amd64`)
> - Projektverzeichnis: `/mnt/local_storage/discordbot`
> - Docker Engine und Docker Compose Plugin
> - Container läuft intern als Benutzer mit UID/GID `10001`
>
> Auf anderen Ubuntu-Versionen kann die Docker-Installation leicht abweichen. Die hier beschriebene Installation nutzt das offizielle Docker-APT-Repository. Ubuntu 26.04 LTS wird von Docker Engine unterstützt.

---

## Inhaltsverzeichnis

1. [Aktuelle Funktionen](#aktuelle-funktionen)
2. [Was wird benötigt?](#was-wird-benötigt)
3. [Ubuntu vorbereiten](#1-ubuntu-vorbereiten)
4. [Docker installieren](#2-docker-installieren)
5. [Projekt auf den Server bringen](#3-projekt-auf-den-server-bringen)
6. [Discord-Bot im Developer Portal erstellen](#4-discord-bot-im-discord-developer-portal-erstellen)
7. [Bot konfigurieren](#5-bot-konfigurieren)
8. [Bot starten](#6-bot-starten)
9. [Betrieb und Verwaltung](#7-betrieb-und-verwaltung)
10. [Weitere Module hinzufügen](#8-weitere-module-hinzufügen)
11. [Wichtige Hinweise zu `/clear`](#wichtige-hinweise-zu-clear)
12. [Fehlerbehebung](#fehlerbehebung)
13. [Sicherheit und Backups](#sicherheit-und-backups)

---

## Aktuelle Funktionen

### Core-Befehle

Diese Befehle gehören zum Bot-Kern und bleiben verfügbar, auch wenn alle optionalen Module deaktiviert sind.

| Befehl | Funktion |
|---|---|
| `/ping` | Prüft, ob der Bot erreichbar ist, und zeigt seine Gateway-Latenz an. |
| `/module list` | Zeigt alle erkannten Module und deren Status an. |
| `/module enable modul:clear` | Aktiviert das Modul `clear` und registriert dessen Slash-Commands. |
| `/module disable modul:clear` | Deaktiviert das Modul `clear` und entfernt dessen Slash-Commands. |
| `/module reload modul:clear` | Lädt ein bereits aktives Modul neu, ohne den gesamten Bot neu zu starten. |

Für alle `/module`-Befehle benötigt das ausführende Mitglied die Discord-Berechtigung **Server verwalten** (`Manage Server`). Die Antworten sind nur für den ausführenden Benutzer sichtbar.

### Modul `clear`

| Befehl | Funktion |
|---|---|
| `/clear` | Löscht den gesamten Nachrichtenverlauf des aktuellen Textkanals oder Threads. |
| `/clear anzahl:50` | Löscht die letzten 50 Nachrichten des aktuellen Kanals/Threads. |
| `/clear benutzer:@Mitglied` | Löscht alle Nachrichten dieses Mitglieds im aktuellen Kanal/Thread. |
| `/clear anzahl:50 benutzer:@Mitglied` | Löscht die letzten 50 Nachrichten dieses Mitglieds im aktuellen Kanal/Thread. |

`anzahl` ist optional und kann von 1 bis 100.000 gesetzt werden. Wird `benutzer` angegeben, zählt `anzahl` nur Nachrichten dieses Mitglieds. Der Bot durchsucht den Verlauf von neu nach alt, bis die gewünschte Anzahl passender Nachrichten gefunden wurde.

Vor jeder Löschung erscheint eine Bestätigungsabfrage. Nur der Benutzer, der den Befehl gestartet hat, kann bestätigen. Die Bestätigung läuft nach zwei Minuten ab. Während des Löschens wird der Fortschritt angezeigt.

Das Modul funktioniert in normalen Discord-Textkanälen und Threads. Sprachkanäle und andere Kanaltypen werden nicht unterstützt.

### Modul `honeypot`

Ein Honeypot-Channel bannt automatisch jeden, der dort schreibt (typisch für Scammer). Aktivieren mit `/module enable modul:honeypot`.

| Befehl | Beschreibung |
|---|---|
| `/honeypot start` | Startet die Überwachung. Ist kein Channel gesetzt, wird ein vorhandener Textchannel „honeypot“ genutzt oder neu angelegt. |
| `/honeypot stop` | Beendet die Überwachung; die Infonachricht bekommt den Zusatz „Honeypot under construction“. |
| `/honeypot status` | Zeigt Status, Channel, Save-Roles, Sprache und Anzahl gebannter User. |
| `/honeypot channel channel:#kanal` | Setzt bzw. wechselt den Channel; ohne Angabe wird der Channel entfernt und die Überwachung gestoppt. |
| `/honeypot setrole rolle1:@Rolle [rolle2 … rolle5]` | Fügt Save-Roles hinzu: deren Mitglieder werden nie gebannt. |
| `/honeypot removerole rolle1:@Rolle [rolle2 … rolle5]` | Entfernt Save-Roles. |
| `/honeypot setlanguage language:DEUTSCH` | Setzt die Sprache der Infonachricht im Channel (Autocomplete aus der Sprachdatei). |

Alle Befehle sind nur auf Servern nutzbar, nur für Mitglieder mit **Mitglieder bannen** (Moderatoren/Admins) und antworten nur für den Ausführenden sichtbar.

**Wer wird nicht gebannt:** Mitglieder mit Save-Role, Mitglieder mit „Mitglieder bannen“ oder Administrator, der Servereigentümer, Bots und Webhooks. Beim Bann werden zusätzlich die Nachrichten des Users der letzten Stunde (serverweit) gelöscht.

**Infonachricht:** Der Bot postet im Channel den Text aus der Sprachdatei samt Ban-Anzahl und hält ihn aktuell. `@everyone` wird nur einmalig beim Aufsetzen gepingt, nicht nach Neustart, Bearbeitung oder `start` nach `stop`.

**Log:** Im Honeypot-Channel legt der Bot einen privaten Thread „honeypot-log“ an (sichtbar für Moderatoren mit „Threads verwalten“ und Admins). Jeder Bann steht dort mit User-ID, Name, Grund, Nachricht und Zeitpunkt; auch fehlgeschlagene Banns.

**Sprachdatei:** `modules/honeypot/languages.txt`, Format `[NAME]` gefolgt von Zeilen ` - …`: Zeile 1 = Infotext, Zeile 2 = Ban-Zeile (`X` wird durch die Anzahl ersetzt), Zeile 3 (optional) = Zusatz bei gestoppter Überwachung. Neue Sprachen einfach als weiteren Abschnitt anfügen – kein Reload nötig.

**Voraussetzungen:**
- Im Discord Developer Portal (Bot) muss der **Message Content Intent** aktiviert sein, sonst startet der Bot nicht.
- Bot-Rechte im Honeypot-Channel: Kanal ansehen, Nachrichten senden, Nachrichtenverlauf anzeigen, Nachrichten verwalten, Mitglieder bannen, @everyone erwähnen, Private Threads erstellen, In Threads Nachrichten senden. Fehlende Rechte meldet `/honeypot start`. Zum automatischen Anlegen des Channels braucht der Bot **Kanäle verwalten**.
- Rollenhierarchie: Die Bot-Rolle muss **über** den Rollen der zu bannenden User stehen, sonst scheitert der Bann (wird im Log-Thread vermerkt).
- Die Einstellungen liegen in `data/honeypot.json`; das Verzeichnis `data` muss für den Docker-Benutzer beschreibbar sein (siehe 5.3).
- Nach Änderungen an `main.py` (Intents) ist ein Neubau nötig: `sudo docker compose up -d --build`.

### Modul `rolepanel`

Der Bot postet im Willkommenskanal eine Nachricht mit einem Button pro wählbarer Rolle. Jedes Mitglied kann sich per Klick die Rolle geben und per erneutem Klick wieder entfernen. Aktivieren mit `/module enable modul:rolepanel`.

| Befehl | Beschreibung |
|---|---|
| `/rolepanel start` | Postet die Rollenauswahl. Ist kein Kanal gesetzt, wird ein vorhandener Textkanal „willkommen“ genutzt oder neu angelegt. Fehler, wenn keine wählbaren Rollen gesetzt sind. |
| `/rolepanel stop` | Entfernt die Nachricht und beendet die Rollenauswahl. |
| `/rolepanel userrole rolle1:@Rolle [rolle2 … rolle5]` | Schaltet Rollen in der Auswahl an oder aus (je Rolle umschalten). Höchstens 25 Rollen. |
| `/rolepanel clear` | Entfernt alle Rollen aus der Auswahl. |
| `/rolepanel info` | Zeigt Status, Kanal, Sprache, Hierarchie, Save-Roles und wählbare Rollen. |
| `/rolepanel setrole rolle1:@Rolle [rolle2 … rolle5]` | Fügt Save-Roles hinzu: nur diese (sowie Servereigentümer und Administratoren) dürfen die `/rolepanel`-Befehle nutzen. |
| `/rolepanel removerole rolle1:@Rolle [rolle2 … rolle5]` | Entfernt Save-Roles. |
| `/rolepanel setlanguage language:DEUTSCH` | Setzt die Sprache der Nachricht (Autocomplete aus der Sprachdatei); die Nachricht im Kanal wird sofort angepasst. |
| `/rolepanel setmessage` | Öffnet ein Formular zum Ändern des Nachrichtentextes der aktuellen Sprache; leeres Feld = Standardtext. |
| `/rolepanel sethierarchie ebene:10` | Hierarchieebene des Moduls im Willkommenskanal (1–100, Standard 10; **kleinere Zahl = weiter oben**). |
| `/rolepanel channel channel:#kanal` | Setzt bzw. überschreibt den gemeinsamen Willkommenskanal; vorhandene Bot-Nachrichten ziehen ohne Ping um. |

Die Befehle sind nur auf Servern nutzbar und antworten nur für den Ausführenden sichtbar. Sie sind in Discord für alle sichtbar; ohne Save-Role (und ohne Eigentümer-/Administratorrecht) kommt eine verständliche Meldung. Die Buttons dürfen alle Mitglieder nutzen; die Rückmeldung (`➕ @Rolle` / `➖ @Rolle`) sieht nur der Klickende.

**Wählbare Rollen:** Abgelehnt werden `@everyone`, von Bots/Integrationen verwaltete Rollen, Rollen mit Admin-/Moderationsrechten (Administrator, Server/Rollen/Kanäle verwalten, Bannen, Kicken, Nachrichten verwalten, @everyone erwähnen), Rollen auf oder über der höchsten Bot-Rolle und Rollen auf oder über der eigenen höchsten Rolle (außer Eigentümer/Administrator).

**Willkommenskanal & Hierarchie (für künftige Module):** Der Kanal ist ein gemeinsamer Dienst (`core/welcome_channel.py`, `get_welcome_manager(bot)`). Module melden sich per `register(schlüssel, render)` an und posten über `publish`; der Bot ordnet alle Nachrichten nach Hierarchieebene (bei gleicher Ebene nach Schlüssel). Da Discord Nachrichten nicht verschieben kann, werden falsch platzierte Bot-Nachrichten gelöscht und in richtiger Reihenfolge neu gesendet; Nachrichten von Mitgliedern bleiben unberührt. `@everyone` pingt nur beim Posten durch `start`, nie beim Bearbeiten oder Neuordnen.

**Sprachdatei:** `modules/rolepanel/languages.txt`, Format `[NAME]` gefolgt von Zeilen ` - …` (Nachrichtentext, mehrere Zeilen möglich). Zeilen ohne `-` (z. B. „Rolle 1“) sind nur Platzhalter; die Liste der Rollen hängt der Bot automatisch an. Neue Sprachen als weiteren Abschnitt anfügen – kein Reload nötig. Entfernte Sprache → Fallback DEUTSCH.

**Voraussetzungen:**
- Bot-Recht **Rollen verwalten** (serverweit); die Bot-Rolle muss **über** allen wählbaren Rollen stehen.
- Bot-Rechte im Willkommenskanal: Kanal ansehen, Nachrichten senden, Nachrichtenverlauf anzeigen, @everyone erwähnen. Zum automatischen Anlegen des Kanals braucht der Bot **Kanäle verwalten**. Fehlende Rechte meldet `/rolepanel start`.
- Der Kern wurde erweitert (`core/`, `main.py`): einmalig `sudo docker compose up -d --build` nötig.
- Die Einstellungen liegen in `data/rolepanel.json` und `data/welcome_channel.json`; `data` muss für den Docker-Benutzer beschreibbar sein.
- Wird der Willkommenskanal gelöscht, ist die Rollenauswahl inaktiv (mit `/rolepanel start` neu starten); gelöschte Rollen verschwinden automatisch aus Auswahl und Save-Roles; eine manuell gelöschte Nachricht wird beim nächsten Update ohne Ping neu gesendet.

---

## Was wird benötigt?

- Ein 64-Bit-Ubuntu-Server mit Internetverbindung.
- Zugriff auf den Server per SSH oder direkt über die Konsole.
- Ein Benutzerkonto mit `sudo`-Rechten.
- Ein Discord-Server, auf dem du den Bot hinzufügen darfst.
- Ein Discord-Konto für das [Discord Developer Portal](https://discord.com/developers/applications).
- Zugriff auf dieses GitHub-Repository oder eine Kopie der Projektdateien.

**Du musst Python nicht separat auf Ubuntu installieren.** Python 3.13 und die Python-Abhängigkeiten befinden sich im Docker-Image.

---

## 1. Ubuntu vorbereiten

Melde dich per SSH auf deinem Ubuntu-Server an.

### 1.1 Ubuntu-Version und Architektur prüfen

```bash
cat /etc/os-release
uname -m
```

Für die hier beschriebene Serverinstallation wird Ubuntu 26.04 LTS und eine 64-Bit-Architektur (`x86_64` bzw. `amd64`) angenommen.

### 1.2 Paketlisten aktualisieren und Grundwerkzeuge installieren

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl git openssh-client nano
```

- `curl` wird benötigt, um den offiziellen Docker-Schlüssel herunterzuladen.
- `git` wird benötigt, um das Projekt aus GitHub zu beziehen bzw. später zu aktualisieren.
- `nano` ist ein einfacher Texteditor für die Konfigurationsdateien.

Falls Ubuntu nach einem Neustart fragt, starte den Server neu und verbinde dich anschließend erneut per SSH.

---

## 2. Docker installieren

Wir installieren Docker Engine aus dem **offiziellen Docker-Repository**. Nicht Docker Desktop und nicht das veraltete separate Programm `docker-compose`.

### 2.1 Offiziellen Docker-Schlüssel hinterlegen

Die folgenden Befehle vollständig kopieren und ausführen:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

### 2.2 Docker-Repository eintragen

```bash
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
```

Paketlisten aktualisieren:

```bash
sudo apt update
```

### 2.3 Docker Engine und Compose installieren

```bash
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2.4 Docker automatisch starten lassen

```bash
sudo systemctl enable --now docker
```

### 2.5 Installation testen

```bash
sudo docker run hello-world
```

Wenn Docker funktioniert, erscheint eine Meldung mit `Hello from Docker!`.

Zusätzlich die Compose-Version prüfen:

```bash
sudo docker compose version
```

> **Hinweis zu `sudo`:** In dieser Anleitung werden Docker-Befehle mit `sudo` ausgeführt. Das ist die sichere Standardvariante. Benutzer, die Mitglied der Linux-Gruppe `docker` sind, können Docker ohne `sudo` bedienen; diese Gruppe verleiht jedoch weitreichende, praktisch root-ähnliche Rechte. Deshalb wird sie hier nicht automatisch eingerichtet.

---

## 3. Projekt auf den Server bringen

Das Projekt wird in diesem Setup unter folgendem Pfad betrieben:

```text
/mnt/local_storage/discordbot
```

### 3.1 Prüfen, ob der Speicher eingebunden ist

Wenn `/mnt/local_storage` eine separate Festplatte oder ein separates Dateisystem ist, muss es **vor** dem Anlegen des Projektordners eingebunden sein.

```bash
findmnt /mnt/local_storage
```

Wenn du hier eine Ausgabe mit dem eingebundenen Dateisystem siehst, ist der Mount vorhanden. Wenn keine Ausgabe erscheint, halte an und prüfe zuerst die Einbindung deiner Festplatte. Sonst könnten die Dateien versehentlich auf der Systempartition landen.

### 3.2 Projekt aus GitHub klonen

Erstelle zuerst den Zielordner. Er muss leer sein:

```bash
sudo mkdir -p /mnt/local_storage/discordbot
sudo chown "$USER":"$USER" /mnt/local_storage/discordbot
```

**Bei einem öffentlichen Repository** kannst du direkt per HTTPS klonen. Ersetze `GITHUB-BENUTZER` und `REPOSITORY` durch die passenden Werte:

```bash
git clone https://github.com/GITHUB-BENUTZER/REPOSITORY.git /mnt/local_storage/discordbot
```

**Bei einem privaten Repository (empfohlen: SSH-Deploy-Key):**

1. Auf dem Ubuntu-Server einen Schlüssel erzeugen:

   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   ssh-keygen -t ed25519 -C "worker-molch-server" -f ~/.ssh/worker_molch_deploy
   ```

   Bei der Passphrase-Abfrage kannst du für diesen nur lesenden Deploy-Key eine Passphrase setzen. Wenn du das tust, muss der Schlüssel vor Git-Operationen über einen SSH-Agent entsperrt werden.

2. Den öffentlichen Schlüssel anzeigen:

   ```bash
   cat ~/.ssh/worker_molch_deploy.pub
   ```

3. Den kompletten angezeigten Schlüssel kopieren. Auf GitHub das Repository öffnen und zu **Settings → Deploy keys → Add deploy key** gehen. Einen Namen wie `Ubuntu DiscordBot Server` vergeben und den Schlüssel einfügen. **Allow write access nicht aktivieren** – der Server soll nur lesen und aktualisieren können.

4. Auf dem Ubuntu-Server die SSH-Verbindung konfigurieren:

   ```bash
   nano ~/.ssh/config
   ```

   Folgenden Inhalt eintragen:

   ```sshconfig
   Host github-worker-molch
       HostName github.com
       User git
       IdentityFile ~/.ssh/worker_molch_deploy
       IdentitiesOnly yes
   ```

   Speichern und die Rechte setzen:

   ```bash
   chmod 600 ~/.ssh/config
   ```

5. Das Repository klonen. Ersetze wieder `GITHUB-BENUTZER` und `REPOSITORY`:

   ```bash
   git clone git@github-worker-molch:GITHUB-BENUTZER/REPOSITORY.git /mnt/local_storage/discordbot
   ```

GitHub erklärt Deploy Keys außerdem in der [offiziellen Dokumentation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys). Niemals ein persönliches Passwort oder einen Token direkt in einen Clone-Befehl schreiben.

> **Wenn die Projektdateien bereits auf dem Server liegen:** Diesen Clone-Schritt überspringen. Nicht versuchen, ein zweites Repository in einem bereits befüllten Projektordner zu klonen.

### 3.3 In den Projektordner wechseln

```bash
cd /mnt/local_storage/discordbot
```

Prüfen, ob die wichtigsten Dateien vorhanden sind:

```bash
ls -la
```

Im Hauptverzeichnis müssen mindestens diese Dateien zu sehen sein:

```text
Dockerfile
compose.yaml
main.py
requirements.txt
.env.example
.gitignore
```

Außerdem müssen die Verzeichnisse `core`, `modules` und `config` vorhanden sein.

---

## 4. Discord-Bot im Developer Portal erstellen

### 4.1 Neue Discord-Anwendung erstellen

1. Öffne https://discord.com/developers/applications.
2. Melde dich mit deinem Discord-Konto an.
3. Klicke auf **New Application**.
4. Gib dem Bot einen Namen, zum Beispiel `Worker Molch`.
5. Erstelle die Anwendung.
6. Öffne links den Bereich **Bot** und erstelle dort den Bot-Benutzer, falls er noch nicht angelegt wurde.

### 4.2 Bot-Token kopieren

Im Bereich **Bot** kannst du den Token erzeugen bzw. zurücksetzen und kopieren.

> **WICHTIG: Der Bot-Token ist ein Passwort.** Nicht in GitHub hochladen, nicht in Screenshots zeigen und nicht an andere Personen schicken. Falls er versehentlich veröffentlicht wird, im Developer Portal sofort zurücksetzen und den neuen Token in der `.env` eintragen.

### 4.3 Server-ID herausfinden

1. Öffne Discord.
2. Öffne **Benutzereinstellungen → Erweitert**.
3. Aktiviere den **Entwicklermodus**.
4. Rechtsklicke auf das Symbol deines Discord-Servers.
5. Wähle **Server-ID kopieren**.

Diese ID wird im nächsten Schritt als `GUILD_ID` eingetragen.

### 4.4 Bot auf den Discord-Server einladen

Im Developer Portal unter **Installation** bzw. **OAuth2** die folgenden Scopes auswählen:

- `bot`
- `applications.commands`

Dem Bot mindestens diese Serverberechtigungen geben:

- **View Channels** – Kanäle ansehen
- **Read Message History** – Nachrichtenverlauf anzeigen
- **Manage Messages** – Nachrichten verwalten/löschen

Anschließend den generierten Installationslink öffnen und den Bot auf den gewünschten Discord-Server einladen.

Für die Slash-Commands allein ist kein privilegierter Intent nötig. Das Modul `honeypot` verlangt jedoch den **Message Content Intent** (siehe [Modul `honeypot`](#modul-honeypot)). Aktiviere ihn im Developer Portal unter *Bot → Privileged Gateway Intents*.

---

## 5. Bot konfigurieren

Alle folgenden Befehle im Projektverzeichnis ausführen:

```bash
cd /mnt/local_storage/discordbot
```

### 5.1 `.env`-Datei erstellen

Die Datei `.env.example` ist eine Vorlage. Daraus wird die echte Konfigurationsdatei erstellt:

```bash
cp .env.example .env
nano .env
```

Trage deine echten Werte ein:

```ini
DISCORD_TOKEN=HIER_DEN_ECHTEN_BOT_TOKEN_EINTRAGEN
GUILD_ID=HIER_DIE_DISCORD_SERVER_ID_EINTRAGEN
```

Beispiel: Die `GUILD_ID` besteht aus Ziffern. Keine Platzhalter stehen lassen.

Speichern in Nano:

1. `STRG + O` drücken.
2. Mit `Enter` bestätigen.
3. Mit `STRG + X` schließen.

Zugriff auf die Datei einschränken:

```bash
chmod 600 .env
```

### 5.2 Modulkonfiguration prüfen

Öffne die Modulkonfiguration:

```bash
nano config/modules.json
```

Das `clear`-Modul soll beim Start aktiv sein. Die Konfiguration sieht beispielsweise so aus:

```json
{
  "enabled_modules": [
    "modules.clear.cog"
  ]
}
```

Wenn weitere Module aktiviert werden, verwaltet der Bot diese Liste selbst. Die ältere Schreibweise `modules.clear` wird aus Kompatibilitätsgründen ebenfalls erkannt.

### 5.3 Verzeichnisrechte für den Docker-Benutzer setzen

Der Bot läuft im Container aus Sicherheitsgründen nicht als root, sondern mit UID/GID `10001`. Er muss die Konfiguration speichern und Daten sowie Logs schreiben dürfen.

```bash
sudo chown -R 10001:10001 config data logs
```

Die Funktionsmodule werden im Container nur lesbar eingebunden. Die Modulverwaltung kann deshalb Module laden, aber nicht versehentlich deren Python-Dateien aus dem Container heraus verändern.

### 5.4 Prüfen, dass `.env` nicht in Git landet

```bash
git check-ignore -v .env
```

Git sollte anzeigen, dass `.env` durch `.gitignore` ignoriert wird. Die Datei `.env.example` darf dagegen im Repository liegen, weil sie nur Platzhalter enthält.

Wenn `.env` bereits früher committet oder zu GitHub gepusht wurde, reicht `.gitignore` allein nicht aus. Dann muss die Datei zusätzlich aus der Git-Verfolgung entfernt und ein eventuell offengelegter Token im Developer Portal erneuert werden.

---

## 6. Bot starten

Im Projektverzeichnis:

```bash
cd /mnt/local_storage/discordbot
sudo docker compose up -d --build
```

Beim ersten Start lädt Docker das Basis-Image für Python, installiert die Python-Abhängigkeiten und baut den Bot-Container. Das kann beim ersten Durchlauf etwas dauern.

### 6.1 Prüfen, ob der Container läuft

```bash
sudo docker compose ps
```

Der Dienst `discord-bot` sollte den Status `Up` bzw. `running` haben.

### 6.2 Bot-Log anzeigen

```bash
sudo docker compose logs -f --tail=100
```

Bei einem erfolgreichen Start sollten Meldungen in dieser Art erscheinen:

```text
Modul geladen: modules.clear.cog
3 Slash-Command(s) für Server ... synchronisiert.
Shard ID None has connected to Gateway
Bot angemeldet als ...
```

Mit `STRG + C` beendest du nur die Log-Anzeige. Der Bot läuft im Hintergrund weiter.

### 6.3 In Discord testen

Im Discord-Server sollten die Befehle verfügbar sein:

- `/ping`
- `/clear`
- `/module list`

Wenn Slash-Commands nicht auftauchen, zuerst das Bot-Log kontrollieren. Prüfe außerdem, ob `GUILD_ID` wirklich die ID des Servers ist, auf dem der Bot installiert wurde.

---

## 7. Betrieb und Verwaltung

Alle Docker-Befehle werden im Projektverzeichnis ausgeführt:

```bash
cd /mnt/local_storage/discordbot
```

| Aufgabe | Befehl |
|---|---|
| Status anzeigen | `sudo docker compose ps` |
| Logs live ansehen | `sudo docker compose logs -f --tail=100` |
| Bot neu starten | `sudo docker compose restart` |
| Bot stoppen | `sudo docker compose down` |
| Bot starten | `sudo docker compose up -d` |
| Nach Core-Code-Änderungen neu bauen | `sudo docker compose up -d --build` |

### 24/7-Betrieb

In `compose.yaml` ist `restart: unless-stopped` eingestellt. Außerdem wird Docker beim Systemstart aktiviert. Dadurch startet Docker den Bot-Container nach einem Serverneustart automatisch wieder, sofern er nicht vorher ausdrücklich gestoppt wurde.

Der Bot baut selbst eine ausgehende Verbindung zu Discord auf. Für die normalen Bot-Funktionen müssen keine eingehenden Ports am Router freigegeben werden.

Der Server muss natürlich eingeschaltet sein und eine funktionierende Internetverbindung besitzen.

### Code aktualisieren

Wenn das Repository direkt über Git verwaltet wird und auf dem Server eine eigene Arbeitskopie liegt:

```bash
cd /mnt/local_storage/discordbot
git pull --ff-only
sudo docker compose up -d --build
```

Wenn GitHub Desktop dagegen – wie in der hier verwendeten Einrichtung – direkt auf denselben Projektordner über eine Windows-Netzwerkfreigabe zugreift, sind die gepushten Dateien bereits in diesem Ordner vorhanden. Core-Änderungen müssen dann auf dem Server nur noch mit `sudo docker compose up -d --build` in das Image übernommen werden.

**Achtung bei `config/modules.json`:** Diese Datei wird vom laufenden Bot geändert, sobald Module aktiviert oder deaktiviert werden. GitHub Desktop kann solche Laufzeitänderungen deshalb als lokale Änderung anzeigen. Vor einem Pull oder dem Übernehmen fremder Änderungen diese Datei prüfen und die gewünschte Modulliste beibehalten. Nicht unüberlegt lokale Änderungen überschreiben.

---

## 8. Weitere Module hinzufügen

Der Bot ist modular aufgebaut. Optionale Funktionen liegen jeweils in einem eigenen Ordner unter `modules/`.

### 8.1 Ordnerstruktur eines Moduls

Ein Modul mit dem Namen `beispiel` benötigt mindestens:

```text
modules/
└── beispiel/
    ├── __init__.py
    └── cog.py
```

Die Datei `cog.py` muss eine asynchrone `setup(bot)`-Funktion bereitstellen, die das Cog beim Laden beim Bot registriert. Das Modul wird unter dem Python-Extension-Namen `modules.beispiel.cog` geladen.

### 8.2 Modul aktivieren

Wenn der Modulordner und die beiden Dateien vorhanden sind, in Discord ausführen:

```text
/module enable modul:beispiel
```

Der Bot lädt das Modul, speichert den aktivierten Zustand in `config/modules.json` und synchronisiert die Slash-Commands.

### 8.3 Modul deaktivieren oder neu laden

```text
/module disable modul:beispiel
/module reload modul:beispiel
```

`reload` funktioniert nur für ein bereits geladenes Modul.

### 8.4 Muss Docker neu gebaut werden?

- **Neue oder geänderte Dateien in `modules/`:** Der Ordner ist in Docker eingebunden. Ein neu angelegtes Modul kann nach dem Hinzufügen direkt mit `/module enable` geladen werden. Ein bereits aktives Modul kann mit `/module reload` neu geladen werden. Für reine Moduländerungen ist kein Image-Neubau erforderlich.
- **Änderungen am Bot-Kern**, z. B. `main.py`, `core/module_manager.py` oder `core/module_commands.py`: Dafür ist ein Neubau erforderlich:

  ```bash
  sudo docker compose up -d --build
  ```

Die Modulverwaltung selbst ist Bestandteil des Core und bleibt auch dann verfügbar, wenn alle optionalen Module ausgeschaltet sind.

---

## Wichtige Hinweise zu `/clear`

- `/clear` löscht alle Nachrichten des aktuellen Textkanals oder Threads, soweit Discord und die Bot-Berechtigungen es erlauben.
- `/clear anzahl:X` zählt die letzten `X` Nachrichten im Kanal.
- `/clear benutzer:@Mitglied` filtert auf Nachrichten dieses Mitglieds.
- `/clear anzahl:X benutzer:@Mitglied` durchsucht den Verlauf von neu nach alt und zählt nur Nachrichten des ausgewählten Mitglieds, bis `X` passende Nachrichten gefunden wurden.
- Jede Löschung muss ausdrücklich bestätigt werden. Nur der Aufrufer kann die Bestätigung betätigen; sie verfällt nach zwei Minuten.
- Die Löschung ist endgültig. Bereits gelöschte Nachrichten können nicht wiederhergestellt werden.
- Discord erlaubt das Bulk-Löschen nur für Nachrichten, die jünger als 14 Tage sind. Ältere Nachrichten werden einzeln gelöscht. Große oder sehr alte Verläufe können deshalb deutlich länger dauern.
- Das Modul zeigt während des Vorgangs den Fortschritt an. Einzelne Nachrichten, die aus technischen Gründen nicht gelöscht werden können, werden als Fehler gezählt. Fehlen dem Bot die nötigen Rechte, kann der Vorgang abbrechen; bereits gelöschte Nachrichten bleiben gelöscht.

### Berechtigungen für `/clear`

Das ausführende Discord-Mitglied benötigt:

- `Manage Messages` / **Nachrichten verwalten**

Der Bot benötigt im betroffenen Kanal:

- `View Channel` / **Kanal ansehen**
- `Read Message History` / **Nachrichtenverlauf anzeigen**
- `Manage Messages` / **Nachrichten verwalten**

### Berechtigungen für `/module`

Das ausführende Discord-Mitglied benötigt:

- `Manage Server` / **Server verwalten**

---

## Fehlerbehebung

### `docker: command not found`

Docker wurde nicht installiert oder die Installation ist fehlgeschlagen. Die Schritte in [Docker installieren](#2-docker-installieren) erneut kontrollieren.

### `permission denied` beim Docker-Befehl

In dieser Anleitung werden Docker-Befehle mit `sudo` ausgeführt. Prüfe, ob du `sudo` vor den Befehl gesetzt hast.

### `PermissionError` bei `config/modules.json`

Der Container kann die Modulkonfiguration nicht schreiben. Im Projektverzeichnis ausführen:

```bash
sudo chown -R 10001:10001 config
```

Dann den Bot neu starten:

```bash
sudo docker compose restart
```

### Bot startet nicht oder beendet sich sofort

Die letzten Logzeilen anzeigen:

```bash
sudo docker compose logs --tail=150
```

Häufige Ursachen sind ein falsch eingetragener Token, eine falsche `GUILD_ID`, eine fehlende Datei oder falsche Dateirechte.

### `403 Forbidden` oder `Missing Access` beim Synchronisieren

Prüfen:

1. Ist der Bot tatsächlich auf dem angegebenen Discord-Server?
2. Ist `GUILD_ID` die Server-ID und nicht die Bot-, Application- oder Kanal-ID?
3. Wurde die Application mit den Scopes `bot` und `applications.commands` installiert?

### Warnungen zu `PyNaCl` oder `davey`

Diese Warnungen betreffen die Unterstützung von Sprachkanälen/Voice-Funktionen. Der aktuelle Bot verwendet keine Voice-Funktionen; für `/ping`, `/clear` und `/module` sind diese Pakete nicht erforderlich.

### Fehler `PrivilegedIntentsRequired` / Message Content Intent

Das Modul `honeypot` benötigt den privilegierten **Message Content Intent**; der Bot fordert ihn an. Aktiviere ihn im Developer Portal unter *Bot → Privileged Gateway Intents → Message Content Intent*. Ohne diese Einstellung bricht der Start mit `PrivilegedIntentsRequired` ab.

---

## Sicherheit und Backups

- **`.env` niemals committen oder zu GitHub pushen.** Sie enthält den geheimen Bot-Token.
- `.env` ist in `.gitignore` eingetragen. `.env.example` enthält nur Platzhalter und darf versioniert werden.
- Falls ein Token versehentlich veröffentlicht wird: im Discord Developer Portal zurücksetzen und anschließend die lokale `.env` aktualisieren.
- Das GitHub-Repository sollte privat sein, wenn der Quellcode nicht öffentlich sein soll.
- `config/modules.json` enthält den Aktivierungsstatus der Module und sollte mitgesichert werden.
- `data/` und `logs/` liegen außerhalb des Container-Images und bleiben bei einem normalen Container-Neubau erhalten.
- Für ein Backup mindestens `config/`, `data/`, `modules/`, `.env` und die Projektdateien sichern. Die `.env`-Sicherung muss geschützt und darf nicht ins Git-Repository gelegt werden.

---

## Weiterführende Dokumentation

- [Docker Engine auf Ubuntu installieren](https://docs.docker.com/engine/install/ubuntu/)
- [Docker Compose-Dokumentation](https://docs.docker.com/compose/)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [discord.py-Dokumentation](https://discordpy.readthedocs.io/)
- [GitHub: Deploy Keys verwalten](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys)
