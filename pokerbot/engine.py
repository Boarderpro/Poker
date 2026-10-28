"""Seven-card evaluation and Monte Carlo equity, without external dependencies."""
from collections import Counter
from dataclasses import dataclass
import random

RANKS = "23456789TJQKA"
SUITS = "shdc"
CATEGORIES = ("High Card", "Paar", "Zwei Paare", "Drilling (Trips)", "Straight", "Flush", "Full House", "Vierling", "Straight Flush")
DECK = tuple(range(52))


def parse_cards(text):
    """Read cards such as 'As Kh', '10h Jd', or 'A♠ K♥'."""
    for symbol, suit in zip("♠♥♦♣", SUITS):
        text = text.replace(symbol, suit)
    cards = []
    for token in text.replace(",", " ").split():
        token = token.upper().replace("10", "T")
        if len(token) != 2 or token[0] not in RANKS or token[1].lower() not in SUITS:
            raise ValueError(f"Ungültige Karte: {token}. Beispiel: As Kh oder 10h Jd")
        cards.append(RANKS.index(token[0]) * 4 + SUITS.index(token[1].lower()))
    if len(set(cards)) != len(cards):
        raise ValueError("Jede Karte darf nur einmal vorkommen.")
    return cards


def format_cards(cards):
    return " ".join(RANKS[c // 4] + "♠♥♦♣"[c % 4] for c in cards)


def straight_high(ranks):
    ranks = set(ranks)
    if 14 in ranks:
        ranks.add(1)
    for high in range(14, 5 - 1, -1):
        if all(rank in ranks for rank in range(high - 4, high + 1)):
            return high
    return 0


def evaluate(cards):
    """Return an ordered tuple for the strongest five-card hand among 5–7 cards."""
    if not 5 <= len(cards) <= 7 or len(set(cards)) != len(cards) or any(c not in DECK for c in cards):
        raise ValueError("Die Bewertung benötigt 5–7 unterschiedliche Karten.")
    ranks = [c // 4 + 2 for c in cards]
    counts = Counter(ranks)
    groups = sorted(((count, rank) for rank, count in counts.items()), reverse=True)
    flush = next((sorted((c // 4 + 2 for c in cards if c % 4 == suit), reverse=True)
                  for suit in range(4) if sum(c % 4 == suit for c in cards) >= 5), None)
    if flush and (high := straight_high(flush)):
        return (8, high)
    if groups[0][0] == 4:
        quad = groups[0][1]
        return (7, quad, max(r for r in ranks if r != quad))
    trips = sorted((r for r, count in counts.items() if count >= 3), reverse=True)
    if trips:
        pairs = sorted((r for r, count in counts.items() if count >= 2 and r != trips[0]), reverse=True)
        if pairs:
            return (6, trips[0], pairs[0])
    if flush:
        return (5, *flush[:5])
    if high := straight_high(ranks):
        return (4, high)
    if trips:
        return (3, trips[0], *sorted((r for r in ranks if r != trips[0]), reverse=True)[:2])
    pairs = sorted((r for r, count in counts.items() if count == 2), reverse=True)
    if len(pairs) >= 2:
        return (2, *pairs[:2], max(r for r in ranks if r not in pairs[:2]))
    if pairs:
        return (1, pairs[0], *sorted((r for r in ranks if r != pairs[0]), reverse=True)[:3])
    return (0, *sorted(ranks, reverse=True)[:5])


def positions(players):
    if not 2 <= players <= 8:
        raise ValueError("Am Tisch müssen 2–8 Spieler sitzen.")
    return {
        2: ("D/SB", "BB"), 3: ("D", "SB", "BB"), 4: ("D", "SB", "BB", "UTG"),
        5: ("D", "SB", "BB", "UTG", "CO"), 6: ("D", "SB", "BB", "UTG", "HJ", "CO"),
        7: ("D", "SB", "BB", "UTG", "UTG+1", "HJ", "CO"),
        8: ("D", "SB", "BB", "UTG", "UTG+1", "MP", "HJ", "CO"),
    }[players]


@dataclass(frozen=True)
class Result:
    samples: int
    win: float
    tie: float
    loss: float
    equity: float
    categories: tuple


def calculate(hole, board=(), players=2, samples=10000, seed=None):
    """Estimate showdown outcomes against uniformly random opponent hands.

    Categories describe the mutually exclusive best final hand, including board
    hands. Equity is the expected pot share, accounting for multiway splits.
    """
    positions(players)
    known = tuple(hole) + tuple(board)
    if len(hole) != 2 or len(board) not in (0, 3, 4, 5):
        raise ValueError("Zwei Handkarten und 0, 3, 4 oder 5 Boardkarten erforderlich.")
    if len(set(known)) != len(known) or any(c not in DECK for c in known):
        raise ValueError("Karten müssen gültig und eindeutig sein.")
    if not isinstance(samples, int) or samples < 1:
        raise ValueError("Die Anzahl Simulationen muss positiv sein.")
    rng = random.Random(seed)
    deck = [c for c in DECK if c not in known]
    missing = 5 - len(board)
    wins = ties = 0
    equity = 0.0
    categories = [0] * 9
    for _ in range(samples):
        draw = rng.sample(deck, missing + 2 * (players - 1))
        final_board = tuple(board) + tuple(draw[:missing])
        hero = evaluate(tuple(hole) + final_board)
        categories[hero[0]] += 1
        opponents = [evaluate(tuple(draw[i:i + 2]) + final_board)
                     for i in range(missing, len(draw), 2)]
        best = max(opponents)
        if hero > best:
            wins += 1
            equity += 1
        elif hero == best:
            ties += 1
            equity += 1 / (1 + opponents.count(hero))
    return Result(samples, wins / samples, ties / samples, (samples - wins - ties) / samples,
                  equity / samples, tuple(n / samples for n in categories))
