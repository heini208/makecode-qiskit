
> Diese Seite bei [https://heini208.github.io/makecode-qiskit/](https://heini208.github.io/makecode-qiskit/) öffnen

## Als Erweiterung verwenden

Dieses Repository kann als **Erweiterung** in MakeCode hinzugefügt werden.

* öffne [https://makecode.calliope.cc/](https://makecode.calliope.cc/)
* klicke auf **Neues Projekt**
* klicke auf **Erweiterungen** unter dem Zahnrad-Menü
* nach **https://github.com/heini208/makecode-qiskit** suchen und importieren

## Dieses Projekt bearbeiten

Um dieses Repository in MakeCode zu bearbeiten.

* öffne [https://makecode.calliope.cc/](https://makecode.calliope.cc/)
* klicke auf **Importieren** und dann auf **Importiere URL**
* füge **https://github.com/heini208/makecode-qiskit** ein und klicke auf Importieren

## Mit IBM Quantum verbinden

Das separate PC-Programm verbindet Qiskit mit der IBM Quantum Platform. Es wird
im Repository
[qiskit_serial_bridge](https://github.com/heini208/qiskit_serial_bridge)
entwickelt; dieses MakeCode-Repository enthält bewusst keine Kopie davon.

1. Lade die passende Anwendung von der
   [neuesten Bridge-Version](https://github.com/heini208/qiskit_serial_bridge/releases/latest)
   herunter und starte sie.
2. Wähle bereits gespeicherte Zugangsdaten oder gib deinen
   [IBM Cloud API Key](https://quantum.cloud.ibm.com/) ein. Die
   Eingabe ist unsichtbar. Die optionale Service-Instanz und Region können leer
   gelassen werden, damit Qiskit sie automatisch auswählt.

Der Key wird nur gespeichert, wenn du dies ausdrücklich bestätigst. Qiskit
speichert ihn dann unverschlüsselt in deinem Benutzerkonto; verwende diese
Option deshalb nur auf einem vertrauenswürdigen persönlichen Computer.

Das Programm führt eine echte Kontoabfrage aus und öffnet danach das
Verbindungs-Dashboard. Dort werden der IBM- und Calliope-Verbindungsstatus,
verfügbare USB-Ports und alle über USB empfangenen Nachrichten angezeigt. Das
Programm durchsucht die seriellen Ports automatisch und erkennt den Calliope
anhand seiner USB-Geräteinformationen. Das funktioniert unabhängig vom
MakeCode-Programm auf dem Calliope. Die manuelle Portauswahl bleibt als Fallback
verfügbar; ein vorhandener `HELLO`/`HELLO_ACK`-Handshake wird weiterhin
beantwortet, ist aber nicht erforderlich.

### Lokale und echte IBM-Jobs

Der Block **run circuit locally** simuliert den Schaltkreis sofort auf dem
Calliope. Der Block **run circuit on IBM Quantum** sendet denselben Schaltkreis
über USB an das PC-Programm und startet dort einen echten `SamplerV2`-Job. Das
PC-Programm muss dafür geöffnet und mit IBM sowie dem Calliope verbunden sein.
Die Erweiterung verwendet die standardmäßige USB-Seriell-Verbindung und lässt
bereits gestartete serielle Ausgaben des Benutzerprogramms unverändert.
Im seriellen Protokoll erscheinen zusätzlich kurze `MICROQISKIT_INFO`- und
`MICROQISKIT_ERROR`-Meldungen. Sie zeigen Übertragung, IBM-Annahme,
Statusänderungen, Abschluss, Validierungsfehler und Timeouts an.
Für eigene Ausgaben muss `serial write line` verwendet werden. Ein
`serial write string` beendet die Zeile nicht und kann deshalb mit der nächsten
Protokollnachricht verschmelzen. Die Erweiterung sendet ihre Protokollzeilen
zeichenweise mit einer kurzen Pause, damit der Calliope-v3-Sendepuffer nicht mit
einer langen Zeichenkette auf einmal gefüllt wird. Eingehende PC-Nachrichten
werden mit MakeCodes Newline-Trennzeichen und `serial read line` gelesen.
Das PC-Programm zeigt auch Text aus `serial write string` nach einer kurzen
Leerlaufzeit als **no newline** an, verarbeitet ihn aber nicht als Protokollzeile.

Kritische Calliope-Anfragen verwenden zusätzlich einen Rahmen mit Sitzungsnummer,
laufender Nummer und Prüfsumme. Das PC-Programm bestätigt gültige Rahmen; bei
einer beschädigten oder ausbleibenden Bestätigung sendet der Calliope die Anfrage
automatisch erneut. Wiederholungen werden bestätigt, aber nur einmal verarbeitet.
Die zeichenweise übertragene Protokollversion beginnt mit `MQ2`.
Die Ergebnisblöcke erwarten die lokale Calliope-Job-ID (`job1`, `job2`, ...), die
vom Startblock zurückgegeben wird, oder direkt die IBM-Runtime-ID aus dem
PC-Protokoll beziehungsweise der IBM-Workloads-Seite. Bei einer noch unbekannten
IBM-ID lädt das PC-Programm den Job im Hintergrund über IBM, überwacht ihn und
speichert sein Sampler-Ergebnis anschließend im gleichen lokalen Cache.

Beide Run-Blöcke geben dieselbe Art von Job-ID zurück. Deshalb funktionieren
die gleichen Ergebnisblöcke für lokale und echte Jobs. Ein lokaler Job ist
sofort fertig; bei einem IBM-Job kann mit **job is finished** gewartet und mit
**status of job** der aktuelle Zustand angezeigt werden. Bei nur einem Shot ist
**bit list result** ein einzelnes echtes Messergebnis des IBM-Quantencomputers.

Mit **print summary for job to serial** lassen sich Ergebnisse ohne LED-Matrix
lesbar ausgeben. Das Dropdown bietet außerdem **One shot**, **Counts** und
**Status**. Bei einem IBM-Job erscheint die Ausgabe im Nachrichtenfenster des
PC-Programms; lokale Ergebnisse können auch mit einem normalen seriellen
Monitor gelesen werden.

Das Starten eines IBM-Jobs bleibt asynchron und gibt die Job-ID sofort zurück.
**status of job** fragt den aktuellen Zustand beim PC ab und wartet nur auf die
passende Statusantwort. Ergebnisblöcke senden eine Ergebnisanfrage und warten
nur auf das vollständige Ergebnismuster oder eine Fehlermeldung. Lokale Jobs
antworten immer sofort. Als Schutz bei einer getrennten Verbindung gilt für
Statusantworten ein Timeout von fünf Sekunden und für IBM-Ergebnisse ein Timeout
von zehn Minuten. Die Meldung steht dann in **last MicroQiskit error**; der
IBM-Job wird nicht abgebrochen und sein Ergebnis kann später noch eintreffen.

**job is finished** bleibt absichtlich nicht blockierend und eignet sich für
Abfrageschleifen. Ein zusätzlicher **wait for job**-Block ist nicht nötig.

Für jeden IBM-Job läuft im PC-Programm ein eigener Hintergrund-Thread. Er
aktualisiert den Status regelmäßig und lädt das Sampler-Ergebnis nach Abschluss
genau einmal von IBM. Anschließend liegen Status, alle einzelnen Shots, Counts,
Backend und IBM-Job-ID im lokalen Speicher des PC-Programms. Weitere Anfragen
des Calliope werden aus diesem Cache beantwortet und erzeugen keine zusätzliche
IBM-Abfrage oder erneute Ausführung.

Das Dashboard zeigt alle in der aktuellen Programmsitzung bekannten Jobs mit
Calliope-ID, IBM-Runtime-ID, Quantensystem, Status und Cache-Zustand. Außerdem
zeigt **Last sent to Calliope** die letzte Antwort des PC-Programms; im seriellen
Protokoll bleiben weiterhin beide Kommunikationsrichtungen vollständig sichtbar.
Eine Calliope- oder IBM-ID kann in der Job-Tabelle angeklickt und über
**Copy selected ID** kopiert werden. Ein Doppelklick auf die ID kopiert sie direkt.

#### Metadaten (verwendet für Suche, Rendering)

* for PXT/calliopemini
<script src="https://makecode.com/gh-pages-embed.js"></script><script>makeCodeRender("{{ site.makecode.home_url }}", "{{ site.github.owner_name }}/{{ site.github.repository_name }}");</script>
