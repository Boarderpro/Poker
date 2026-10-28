"""Local browser UI. Run with python -m pokerbot."""
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
import argparse
import random
from .engine import CATEGORIES, calculate, parse_cards, format_cards, positions, DECK

STYLE = '''
:root{font-family:system-ui,sans-serif;color:#e6eeeb;background:#101d19;color-scheme:dark}
*{box-sizing:border-box}body{margin:0}main{max-width:58rem;margin:auto;padding:2rem 1rem}
h1{font-size:2.4rem;margin-bottom:.4rem}p{line-height:1.6;color:#bbcdc4}
fieldset,section{border:1px solid #527465;border-radius:1rem;padding:1.3rem;margin:1.5rem 0;background:#182b23}
legend{font-weight:bold}label{display:block;margin-top:1rem;margin-bottom:.4rem}
input,select,button{font:inherit;padding:.8rem;min-height:48px;border:1px solid #88a496;border-radius:.5rem;width:100%}
button{margin-top:1.4rem;background:#a7efbd;color:#122219;font-weight:bold;cursor:pointer}
a{color:#a7efbd}:focus-visible{outline:3px solid #ffe097;outline-offset:3px}
.stats{display:flex;flex-wrap:wrap;gap:1rem}.stat{flex:1;min-width:8rem;padding:1rem;border:1px solid #527465;border-radius:.6rem}
strong{font-size:1.6rem;display:block}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:.6rem;border-bottom:1px solid #527465}td:last-child{text-align:right}
.error{border:2px solid #ffbf9c;padding:1rem}small{line-height:1.6;display:block;color:#bbcdc4}
'''


def render(values, submitted=False):
    defaults = dict(table='6', active='6', position='D', hole='', flop='', turn='', river='', samples='10000')
    defaults.update(values)
    v = defaults
    error = result = ''
    try:
        table = int(v['table'])
        seats = positions(table)
        active = int(v['active'])
        if not 2 <= active <= table:
            raise ValueError('Aktive Spieler müssen zwischen 2 und der Tischgröße liegen (inklusive dir).')
        if submitted:
            if v['position'] not in seats:
                raise ValueError('Bitte wähle eine Position passend zur Tischgröße und berechne erneut.')
            hole = parse_cards(v['hole'])
            if not hole:
                hole = random.sample(DECK, 2)
                v['hole'] = ' '.join('23456789TJQKA'[c // 4] + 'shdc'[c % 4] for c in hole)
            flop, turn, river = (parse_cards(v[k]) for k in ('flop', 'turn', 'river'))
            if len(flop) not in (0, 3) or len(turn) > 1 or len(river) > 1:
                raise ValueError('Flop: genau 3 Karten; Turn und River: jeweils eine Karte oder leer.')
            if (turn and not flop) or (river and not turn):
                raise ValueError('Bitte zuerst Flop, dann Turn und anschließend River eingeben.')
            samples = int(v['samples'])
            if samples not in (2000, 10000, 30000):
                raise ValueError('Bitte eine angebotene Simulationszahl wählen.')
            board = flop + turn + river
            r = calculate(hole, board, active, samples)
            phase = {0:'Preflop',3:'Flop',4:'Turn',5:'River – Durchgang abgeschlossen'}[len(board)]
            stats = ''.join(f'<div class="stat">{label}<strong>{value:.2%}</strong></div>' for label,value in (
                ('Gewinn (allein)',r.win),('Split Pot',r.tie),('Verlust',r.loss),('Equity / Potanteil',r.equity)))
            rows = ''.join(f'<tr><th scope="row">{name}</th><td>{chance:.2%}</td></tr>' for name,chance in reversed(list(zip(CATEGORIES,r.categories))))
            result = f'''<section aria-labelledby="results"><h2 id="results">{phase}</h2>
<p>Deine Hand: {format_cards(hole)} · Board: {format_cards(board) or 'noch leer'} · {active} aktive Spieler</p>
<div class="stats">{stats}</div><h3>Beste Hand am River</h3>
<p>Die Kategorien schließen sich gegenseitig aus, zählen auch reine Board-Hände und ergeben zusammen 100 %. Royal Flush zählt als Straight Flush.</p>
<table><thead><tr><th scope="col">Handkategorie</th><th scope="col">Wahrscheinlichkeit</th></tr></thead><tbody>{rows}</tbody></table>
<p>Monte-Carlo-Schätzung aus {samples:,} Simulationen. Typische maximale Schwankung der Gewinnquote (95 %): ±{98 / samples**.5:.2f} Prozentpunkte. Am River steht deine Handkategorie fest; unbekannte Gegnerhände werden weiter simuliert.</p></section>'''
    except ValueError as exc:
        error = f'<p class="error" role="alert">{escape(str(exc))}</p>'
        seats = positions(int(v['table'])) if v['table'] in tuple(map(str,range(2,9))) else positions(6)
    def select(name, label, choices):
        options = ''.join(f'<option value="{escape(str(x))}" {"selected" if str(x)==v[name] else ""}>{escape(str(x))}</option>' for x in choices)
        return f'<label for="{name}">{label}</label><select id="{name}" name="{name}">{options}</select>'
    def field(name, label):
        return f'<label for="{name}">{label}</label><input id="{name}" name="{name}" value="{escape(v[name], quote=True)}" maxlength="40" spellcheck="false" autocapitalize="off" autocomplete="off" aria-describedby="cards-help">'
    fields = select('table','Spieler am Tisch (inklusive dir)', range(2,9)) + select('active','Noch aktive Spieler (inklusive dir)',range(2,9))
    fields += select('position','Deine Position',seats) + field('hole','Deine zwei Karten (leer = zufällig austeilen)')
    fields += field('flop','Flop (3 Karten, optional)') + field('turn','Turn (1 Karte, optional)') + field('river','River (1 Karte, optional)')
    fields += select('samples','Anzahl Simulationen', (2000,10000,30000))
    return f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pokerbot · Hold’em Chancen</title><style>{STYLE}</style></head>
<body><main><header><p>TEXAS HOLD’EM · CHANCENRECHNER</p><h1>Deine nächste Hand.</h1><p>Von Preflop bis River: Gewinnchancen und Handwahrscheinlichkeiten für 2–8 Spieler.</p></header>
{error}<form method="get" action="/"><fieldset><legend>Tisch &amp; Karten</legend><p id="cards-help">Karten mit Leerzeichen trennen, z. B. As Kh oder 10h Jd Qc. s = Pik, h = Herz, d = Karo, c = Kreuz. D = Dealer/Button, CO = Cutoff, HJ = Hijack, UTG = erste Position nach BB. Im Heads-up ist D zugleich SB.</p>
{fields}<button type="submit" name="calculate" value="1">Chancen berechnen / aktualisieren</button></fieldset></form>
<p>Neue Boardkarten ergänzen, ausgeschiedene Spieler reduzieren und erneut berechnen. Bei geänderter Tischgröße wird die Positionsauswahl nach dem Absenden angepasst.</p>{result}
<p>Gegnerhände sind zufällig und gleichverteilt. Position und Folds liefern ohne gegnerische Handranges keine zusätzlichen Informationen. Unbekannte abgelegte Karten werden nicht als bekannte Karten entfernt. Keine Einsatzempfehlung oder Gewinnzusage.</p><a href="/">Neuer Durchgang</a></main></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        if url.path != '/':
            self.send_error(404)
            return
        if len(url.query) > 4096:
            self.send_error(414)
            return
        data = {k: v[-1] for k,v in parse_qs(url.query, keep_blank_values=True).items()}
        body = render(data, 'calculate' in data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description='Lokaler Poker-Chancenrechner')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host,args.port),Handler)
    print(f'Pokerbot läuft auf {args.host}:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
