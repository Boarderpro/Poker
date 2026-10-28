import unittest
from itertools import combinations
from pokerbot.engine import calculate, evaluate, parse_cards, positions
from pokerbot.web import render


class PokerTests(unittest.TestCase):
    def test_all_categories(self):
        hands = ['As Kd 9h 7c 3s', 'As Ad 9h 7c 3s', 'As Ad 9h 9c 3s',
                 'As Ad Ah 7c 3s', 'As 2d 3h 4c 5s', 'As Js 9s 7s 3s',
                 'As Ad Ah 7c 7s', 'As Ad Ah Ac 3s', '9s Ts Js Qs Ks']
        for category, hand in enumerate(hands):
            with self.subTest(hand=hand):
                self.assertEqual(evaluate(parse_cards(hand))[0],category)

    def test_seven_cards_match_five_card_reference(self):
        import random
        rng = random.Random(7)
        for _ in range(200):
            cards = rng.sample(range(52),7)
            self.assertEqual(evaluate(cards), max(evaluate(c) for c in combinations(cards,5)))

    def test_two_trips_make_full_house(self):
        self.assertEqual(evaluate(parse_cards('As Ad Ah Ks Kd Kh 2c')), (6,14,13))

    def test_wheel_loses_to_six_high(self):
        self.assertLess(evaluate(parse_cards('As 2d 3h 4c 5s')),evaluate(parse_cards('2s 3d 4h 5c 6s')))

    def test_board_royal_split_eight_players(self):
        r = calculate(parse_cards('2h 3h'), parse_cards('Ts Js Qs Ks As'),8,100,seed=1)
        self.assertEqual((r.win,r.tie,r.loss,r.equity),(0,1,0,1/8))
        self.assertEqual(r.categories[8],1)

    def test_unbeatable_royal(self):
        r = calculate(parse_cards('As Ks'),parse_cards('Qs Js Ts 2h 3d'),8,100,seed=2)
        self.assertEqual(r.win,1)
        self.assertEqual(r.equity,1)

    def test_preflop_aces(self):
        r = calculate(parse_cards('As Ah'),players=2,samples=3000,seed=4)
        self.assertTrue(.80 < r.equity < .90)
        self.assertAlmostEqual(sum(r.categories),1)
        self.assertAlmostEqual(r.win+r.tie+r.loss,1)

    def test_invalid_cards_and_boards(self):
        for text in ('As As','Xs','Ahh'):
            with self.assertRaises(ValueError): parse_cards(text)
        for board in ('As Kh','As 3h 4c'):
            with self.assertRaises(ValueError):
                calculate(parse_cards('As Kd'),parse_cards(board),samples=10)
        for n in (1,9):
            with self.assertRaises(ValueError): positions(n)

    def test_web_stages(self):
        for flop,turn,river in (('','',''),('Qs Js Ts','',''),('Qs Js Ts','2h',''),('Qs Js Ts','2h','3d')):
            page = render(dict(table='3',active='2',hole='As Ks',flop=flop,turn=turn,river=river,samples='2000'),True)
            self.assertIn('Equity / Potanteil',page)
            self.assertNotIn('role="alert"',page)

    def test_web_validation_and_escaping(self):
        page = render(dict(hole='<script>'),True)
        self.assertIn('role="alert"',page)
        self.assertNotIn('<script>',page)
        page = render(dict(hole='As Kh',river='2d'),True)
        self.assertIn('zuerst Flop',page)
        page = render(dict(table='oops'),True)
        self.assertIn('role="alert"',page)


if __name__ == '__main__':
    unittest.main()
