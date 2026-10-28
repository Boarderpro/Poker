# Pokerbot – Texas Hold’em

Python-Webanwendung für 2–8 Spieler. Python 3.10 oder neuer, keine externen Abhängigkeiten.

## Start

```sh
python -m pokerbot
```

Im Browser `http://127.0.0.1:8000` öffnen. Optional: `--host 0.0.0.0 --port 8000` für einen zugänglichen Entwicklungsserver. Der eingebaute HTTP-Server ist für lokale Entwicklung gedacht, nicht für öffentliches Hosting.

1. Tischgröße, aktive Spieler (jeweils inklusive dir) und Position auswählen.
2. Zwei Karten eingeben oder das Feld zum zufälligen Austeilen leer lassen.
3. Berechnen. Die ausgeteilte Hand bleibt in den Feldern erhalten.
4. Flop ergänzen, aktive Spieler bei Folds reduzieren, erneut berechnen.
5. Mit Turn und River wiederholen. „Neuer Durchgang“ leert das Formular.

Kartenformat: `As Kh`, `10h Jd Qc`; s/Pik, h/Herz, d/Karo, c/Kreuz. Kartensymbole werden ebenfalls akzeptiert. D bedeutet Dealer/Button (Heads-up D/SB).

## Berechnung

Monte-Carlo-Simulation ohne Zurücklegen über alle unbekannten Board- und Gegnerkarten. Gegner erhalten gleichverteilte zufällige Hände; gegnerische Ranges, Einsätze und Fold-Verhalten werden nicht modelliert. Die Position ist eine Tischangabe und verändert unter diesen Annahmen keine Wahrscheinlichkeit.

- **Gewinn**: alleinige beste Hand.
- **Split Pot**: gemeinsam beste Hand.
- **Equity**: erwarteter Potanteil, einschließlich anteiliger Split Pots.
- **Handkategorien**: jeweils die beste Fünf-Karten-Hand bis zum River, einschließlich Board-Händen. Gegenseitig ausschließend: Ein Full House zählt nicht zusätzlich als Drilling; Straight Flush nicht zusätzlich als Flush. Royal Flush ist Straight Flush.

Die Ergebnisse sind Schätzungen, keine exakten Werte. Mehr Simulationen reduzieren Schwankungen und dauern länger. Am River steht die eigene Handkategorie fest; der Ausgang gegen unbekannte Gegner bleibt eine Schätzung. Unbekannte Fold-Karten sind nicht bekannt und werden nicht entfernt. Sobald nur du übrig bist, ist die Hand durch Folds gewonnen; die Showdown-Simulation ist für mindestens zwei aktive Spieler gedacht.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests prüfen Handwertung, Split Pots, bekannte River-Situationen, Eingabevalidierung und die Weboberfläche. Es werden keine externen Dienste oder Zugangsdaten benötigt.
