
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

Das PC-Programm verbindet Qiskit mit der IBM Quantum Platform. Python 3.10 oder
neuer wird empfohlen.

1. Installiere die benötigten Pakete im Projektordner:

   ```shell
   python -m pip install -r requirements.txt
   ```

2. Starte die grafische Oberfläche:

   ```shell
   python tools/qiskit_pc_bridge.py
   ```

3. Gib deinen [IBM Cloud API Key](https://quantum.cloud.ibm.com/) ein. Die
   Eingabe ist unsichtbar. Die optionale Service-Instanz und Region können leer
   gelassen werden, damit Qiskit sie automatisch auswählt.

Der Key wird nur gespeichert, wenn du dies ausdrücklich bestätigst. Qiskit
speichert ihn dann unverschlüsselt in deinem Benutzerkonto; verwende diese
Option deshalb nur auf einem vertrauenswürdigen persönlichen Computer.

Das Programm führt eine echte Kontoabfrage aus und öffnet danach das
Verbindungs-Dashboard. Dort werden der IBM- und Calliope-Verbindungsstatus,
verfügbare USB-Ports und alle über USB empfangenen Nachrichten angezeigt. Der
bisherige `HELLO`/`HELLO_ACK`-Handshake wird ebenfalls unterstützt.

#### Metadaten (verwendet für Suche, Rendering)

* for PXT/calliopemini
<script src="https://makecode.com/gh-pages-embed.js"></script><script>makeCodeRender("{{ site.makecode.home_url }}", "{{ site.github.owner_name }}/{{ site.github.repository_name }}");</script>
