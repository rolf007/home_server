#!/usr/bin/env python3

from music_server import MusicCollection
from logger import Logger
import unittest

class TestMusicServer(unittest.TestCase):

    def setUp(self):
        pass

    def test_simple_title_search(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - orion.mp3":{ "artist": "metallica", "title": "orion"},
            "/foo/metallica - the house jack built.mp3":{ "artist": "metallica", "title": "The house that Jack built"},
            "/foo/metallica - sanitarium.mp3":{ "artist": "metallica", "title": "Sanitarium"},
            "/foo/metallica - for whom the bells toll.mp3":{ "artist": "metallica", "title": "Fro whom the Bells Toll"}
            })
        next_song = music_collection.resolve_query({"title": ["sani"]})
        self.assertEqual(["/foo/metallica - sanitarium.mp3"], next_song)

    def test_search_artist_and_title(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/rainbow - gates of babylon.mp3":{ "artist": "rainbow", "title": "Gates of Babylon"},
            "/foo/yngwie malmsteen - pictures of home.mp3":{ "artist": "yngwie malmsteen", "title": "Pictures of Home"},
            "/foo/yngwie malmsteen - gates of babylon.mp3":{ "artist": "yngwie malmsteen", "title": "Gates of Babylon"}
            })
        next_song = music_collection.resolve_query({"title": ["gates of babylon"], "artist": ["yngwie malmsteen"]})
        self.assertEqual(["/foo/yngwie malmsteen - gates of babylon.mp3"], next_song)

    def test_double_title_search(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - call of the wild.mp3":{ "artist": "metallica", "title": "Call of the Wild"},
            "/foo/metallica - cal of chtulu.mp3":{ "artist": "metallica", "title": "Cal of Chtulu"},
            "/foo/metallica - khtulu returns.mp3":{ "artist": "metallica", "title": "Ktulu Awakens"}
            })
        next_song = music_collection.resolve_query({"title": ["Call", "Ktulu"]})
        self.assertEqual(["/foo/metallica - cal of chtulu.mp3"], next_song)

    def test_equally_good_matches(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - jump in the fire.mp3":{ "artist": "metallica", "title": "jump in the fire"},
            "/foo/iron maiden - the trooper.mp3":{ "artist": "Iron Maiden", "title": "The Trooper"},
            "/foo/metallica - call of ktulu.mp3":{ "artist": "metallica", "title": "call of ktulu"},
            "/foo/metallica - orion.mp3":{ "artist": "metallica", "title": "Orion"},
            "/foo/acdc - for those about to rock.mp3":{ "artist": "acdc", "title": "For Those about to Rock"}
            })
        next_song = music_collection.resolve_query({"artist": ["metalliac"]})
        self.assertEqual(set(["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3", "/foo/metallica - call of ktulu.mp3"]), set(next_song))

    def test_fuzzy_choose_shortest_match(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - jump in the fire.mp3":{ "artist": "Metallica", "title": "Jump in the fire"},
            "/foo/van halen - jump.mp3":{ "artist": "Van Halen", "title": "Jump"},
            "/foo/c64 - jumping jackson.mp3":{ "artist": "C64", "title": "Jumping Jackson"},
            })
        next_song = music_collection.resolve_query({"title": ["jump"]})
        self.assertEqual(set(["/foo/van halen - jump.mp3"]), set(next_song))

    def test_exact_match(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - jump in the fire.mp3":{ "artist": "metallica", "title": "jump in the fire"},
            "/foo/iron maiden - the trooper.mp3":{ "artist": "Iron Maiden", "title": "The Trooper"},
            "/foo/metallica - call of ktulu.mp3":{ "artist": "metaLLICA", "title": "call of ktulu"},
            "/foo/metallica - orion.mp3":{ "artist": "metallica", "title": "Orion"},
            "/foo/acdc - for those about to rock.mp3":{ "artist": "acdc", "title": "For Those about to Rock"}
            })
        # exact match - typo -> no matches
        next_song = music_collection.resolve_query({"artist": [",metalliac"]})
        self.assertEqual(set(), set(next_song))
        # fuzzy match - typo -> multiple matches
        next_song = music_collection.resolve_query({"artist": ["metalliac"]})
        self.assertEqual(set(["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3", "/foo/metallica - call of ktulu.mp3"]), set(next_song))
        # exact match - no typo -> multiple matches
        next_song = music_collection.resolve_query({"artist": [",metallica"]})
        self.assertEqual(set(["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3", "/foo/metallica - call of ktulu.mp3"]), set(next_song))
        # exact match - no typo case sensitive -> multiple matches
        next_song = music_collection.resolve_query({"artist": [":,metallica"]})
        self.assertEqual(set(["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3"]), set(next_song))
        # negative exact match - no typo -> multiple matches
        next_song = music_collection.resolve_query({"artist": ["!,metallica"]})
        self.assertEqual(set(["/foo/iron maiden - the trooper.mp3", "/foo/acdc - for those about to rock.mp3"]), set(next_song))

    def test_numeric_range_match(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/iron maiden - prowler.mp3":{ "artist": "Iron Maiden", "title": "Prowler", "release": "1980"},
            "/foo/iron maiden - killers.mp3":{ "artist": "Iron Maiden", "title": "Killers", "release": "1981"},
            "/foo/iron maiden - gangland.mp3":{ "artist": "Iron Maiden", "title": "Gangland", "release": "1982"},
            "/foo/iron maiden - still life.mp3":{ "artist": "Iron Maiden", "title": "Still Life", "release": "1983"},
            "/foo/iron maiden - aces high.mp3":{ "artist": "Iron Maiden", "title": "Aces High", "release": "1984"},
            "/foo/iron maiden - deja-vu.mp3":{ "artist": "Iron Maiden", "title": "Deja-vu", "release": "1986"},
            "/foo/iron maiden - moonchild.mp3":{ "artist": "Iron Maiden", "title": "Moonchild", "release": "1988"},
            "/foo/iron maiden - tailgunner.mp3":{ "artist": "Iron Maiden", "title": "Tailgunner", "release": "1990"},
            "/foo/iron maiden - the fugitive.mp3":{ "artist": "Iron Maiden", "title": "The Fugitive", "release": "1992"},
            "/foo/iron maiden - tailgunner - LIVE.mp3":{ "artist": "Iron Maiden", "title": "Tailgunner - LIVE", "release": "1993"},
            "/foo/iron maiden - prowler - LIVE.mp3":{ "artist": "Iron Maiden", "title": "Prowler - LIVE", "release": "1993"},
            "/foo/iron maiden - sanctuary - LIVE.mp3":{ "artist": "Iron Maiden", "title": "Sanctuary - LIVE", "release": "1993"},
            "/foo/iron maiden - 2 a.m..mp3":{ "artist": "Iron Maiden", "title": "2 A.M.", "release": "1995"},
            "/foo/iron maiden - futureal.mp3":{ "artist": "Iron Maiden", "title": "Futureal", "release": "1998"},
            })
        # songs from one specific year - one match
        next_song = music_collection.resolve_query({"release": ["1984"]})
        self.assertEqual(set(["/foo/iron maiden - aces high.mp3"]), set(next_song))
        # songs from one specific year - multiple matches
        next_song = music_collection.resolve_query({"release": ["1993"]})
        self.assertEqual(set(["/foo/iron maiden - tailgunner - LIVE.mp3", "/foo/iron maiden - prowler - LIVE.mp3", "/foo/iron maiden - sanctuary - LIVE.mp3"]), set(next_song))
        # songs from range of years - exactly including
        next_song = music_collection.resolve_query({"release": ["-1988-1992"]})
        self.assertEqual(set(["/foo/iron maiden - moonchild.mp3", "/foo/iron maiden - tailgunner.mp3", "/foo/iron maiden - the fugitive.mp3"]), set(next_song))
        # songs from range of years - exactly not including
        next_song = music_collection.resolve_query({"release": ["-1989-1991"]})
        self.assertEqual(set(["/foo/iron maiden - tailgunner.mp3"]), set(next_song))
        # songs from open range of years: up to specific year
        next_song = music_collection.resolve_query({"release": ["--1982"]})
        self.assertEqual(set(["/foo/iron maiden - killers.mp3", "/foo/iron maiden - prowler.mp3", "/foo/iron maiden - gangland.mp3"]), set(next_song))
        # songs from open range of years: from specific year
        next_song = music_collection.resolve_query({"release": ["-1995-"]})
        self.assertEqual(set(["/foo/iron maiden - 2 a.m..mp3", "/foo/iron maiden - futureal.mp3"]), set(next_song))
        # songs NOT from range of years
        next_song = music_collection.resolve_query({"release": ["!-1981-1995"]})
        self.assertEqual(set(["/foo/iron maiden - prowler.mp3", "/foo/iron maiden - futureal.mp3"]), set(next_song))

    def test_regex_match(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/iron maiden - iron maiden.mp3":{ "artist": "Iron Maiden", "title": "Iron Maiden"},
            "/foo/ramin djawadi - iron man theme.mp3":{ "artist": "Ramin Djawadi", "title": "Theme from Iron Man"},
            "/foo/black sabbath - iron man.mp3":{ "artist": "Black Sabbath", "title": "Iron Man"},
            "/foo/mark winholtz - ironman hymn.mp3":{ "artist": "Mark Winholtz", "title": "Ironman Hymn - Everything is Possible"},
            })
        next_song = music_collection.resolve_query({"title": ["/^iron ma"]})
        self.assertEqual(set(["/foo/iron maiden - iron maiden.mp3", "/foo/black sabbath - iron man.mp3"]), set(next_song))
        next_song = music_collection.resolve_query({"title": ["/^iron\s*ma"]})
        self.assertEqual(set(["/foo/iron maiden - iron maiden.mp3", "/foo/black sabbath - iron man.mp3", "/foo/mark winholtz - ironman hymn.mp3"]), set(next_song))
        next_song = music_collection.resolve_query({"title": [":/^Iron\s*Ma"]})
        self.assertEqual(set(["/foo/iron maiden - iron maiden.mp3", "/foo/black sabbath - iron man.mp3"]), set(next_song))
        next_song = music_collection.resolve_query({"title": ["!:/^Iron\s*Ma"]})
        self.assertEqual(set(["/foo/ramin djawadi - iron man theme.mp3", "/foo/mark winholtz - ironman hymn.mp3"]), set(next_song))


if __name__ == '__main__':
    unittest.main()
