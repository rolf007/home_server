#!/usr/bin/env python3

from music_server import MusicCollection
from logger import Logger
import unittest

class TestMusicServer(unittest.TestCase):

    def setUp(self):
        pass

    def eq(self, music_collection, expected, search):
        music_collection.start_search(lambda session_id: self.assertEqual(set(expected), set(music_collection.get_search_result(session_id))), search, 1, False)

    def test_simple_title_search(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - orion.mp3":{ "artist": "metallica", "title": "orion"},
            "/foo/metallica - the house jack built.mp3":{ "artist": "metallica", "title": "The house that Jack built"},
            "/foo/metallica - sanitarium.mp3":{ "artist": "metallica", "title": "Sanitarium"},
            "/foo/metallica - for whom the bells toll.mp3":{ "artist": "metallica", "title": "Fro whom the Bells Toll"}
            })
        self.eq(music_collection, ["/foo/metallica - sanitarium.mp3"], {"title": ["sani"]})


    def test_search_artist_and_title(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/rainbow - gates of babylon.mp3":{ "artist": "rainbow", "title": "Gates of Babylon"},
            "/foo/yngwie malmsteen - pictures of home.mp3":{ "artist": "yngwie malmsteen", "title": "Pictures of Home"},
            "/foo/yngwie malmsteen - gates of babylon.mp3":{ "artist": "yngwie malmsteen", "title": "Gates of Babylon"}
            })
        self.eq(music_collection, ["/foo/yngwie malmsteen - gates of babylon.mp3"], {"title": ["gates of babylon"], "artist": ["yngwie malmsteen"]})

    def test_double_title_search(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - call of the wild.mp3":{ "artist": "metallica", "title": "Call of the Wild"},
            "/foo/metallica - cal of chtulu.mp3":{ "artist": "metallica", "title": "Cal of Chtulu"},
            "/foo/metallica - khtulu returns.mp3":{ "artist": "metallica", "title": "Ktulu Awakens"}
            })
        self.eq(music_collection, ["/foo/metallica - cal of chtulu.mp3"], {"title": ["Call", "Ktulu"]})

    def test_equally_good_matches(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - jump in the fire.mp3":{ "artist": "metallica", "title": "jump in the fire"},
            "/foo/iron maiden - the trooper.mp3":{ "artist": "Iron Maiden", "title": "The Trooper"},
            "/foo/metallica - call of ktulu.mp3":{ "artist": "metallica", "title": "call of ktulu"},
            "/foo/metallica - orion.mp3":{ "artist": "metallica", "title": "Orion"},
            "/foo/acdc - for those about to rock.mp3":{ "artist": "acdc", "title": "For Those about to Rock"}
            })
        self.eq(music_collection, ["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3", "/foo/metallica - call of ktulu.mp3"], {"artist": ["metalliac"]})

    def test_fuzzy_choose_shortest_match(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - jump in the fire.mp3":{ "artist": "Metallica", "title": "Jump in the fire"},
            "/foo/van halen - jump.mp3":{ "artist": "Van Halen", "title": "Jump"},
            "/foo/c64 - jumping jackson.mp3":{ "artist": "C64", "title": "Jumping Jackson"},
            })
        self.eq(music_collection, ["/foo/van halen - jump.mp3"], {"title": ["jump"]})

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
        self.eq(music_collection, [], {"artist": [",metalliac"]})
        # fuzzy match - typo -> multiple matches
        self.eq(music_collection, ["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3", "/foo/metallica - call of ktulu.mp3"], {"artist": ["metalliac"]})
        # exact match - no typo -> multiple matches
        self.eq(music_collection, ["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3", "/foo/metallica - call of ktulu.mp3"], {"artist": [",metallica"]})
        # exact match - no typo case sensitive -> multiple matches
        self.eq(music_collection, ["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3"], {"artist": [":,metallica"]})
        # negative exact match - no typo -> multiple matches
        self.eq(music_collection, ["/foo/iron maiden - the trooper.mp3", "/foo/acdc - for those about to rock.mp3"], {"artist": ["!,metallica"]})

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
        self.eq(music_collection, ["/foo/iron maiden - aces high.mp3"], {"release": ["1984"]})
        # songs from one specific year - multiple matches
        self.eq(music_collection, ["/foo/iron maiden - tailgunner - LIVE.mp3", "/foo/iron maiden - prowler - LIVE.mp3", "/foo/iron maiden - sanctuary - LIVE.mp3"], {"release": ["1993"]})
        # songs from range of years - exactly including
        self.eq(music_collection, ["/foo/iron maiden - moonchild.mp3", "/foo/iron maiden - tailgunner.mp3", "/foo/iron maiden - the fugitive.mp3"], {"release": ["-1988-1992"]})
        # songs from range of years - exactly not including
        self.eq(music_collection, ["/foo/iron maiden - tailgunner.mp3"], {"release": ["-1989-1991"]})
        # songs from open range of years: up to specific year
        self.eq(music_collection, ["/foo/iron maiden - killers.mp3", "/foo/iron maiden - prowler.mp3", "/foo/iron maiden - gangland.mp3"], {"release": ["--1982"]})
        # songs from open range of years: from specific year
        self.eq(music_collection, ["/foo/iron maiden - 2 a.m..mp3", "/foo/iron maiden - futureal.mp3"], {"release": ["-1995-"]})
        # songs NOT from range of years
        self.eq(music_collection, ["/foo/iron maiden - prowler.mp3", "/foo/iron maiden - futureal.mp3"], {"release": ["!-1981-1995"]})

    def test_regex_match(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/iron maiden - iron maiden.mp3":{ "artist": "Iron Maiden", "title": "Iron Maiden"},
            "/foo/ramin djawadi - iron man theme.mp3":{ "artist": "Ramin Djawadi", "title": "Theme from Iron Man"},
            "/foo/black sabbath - iron man.mp3":{ "artist": "Black Sabbath", "title": "Iron Man"},
            "/foo/mark winholtz - ironman hymn.mp3":{ "artist": "Mark Winholtz", "title": "Ironman Hymn - Everything is Possible"},
            })
        self.eq(music_collection, ["/foo/iron maiden - iron maiden.mp3", "/foo/black sabbath - iron man.mp3"], {"title": ["/^iron ma"]})
        self.eq(music_collection, ["/foo/iron maiden - iron maiden.mp3", "/foo/black sabbath - iron man.mp3", "/foo/mark winholtz - ironman hymn.mp3"], {"title": ["/^iron\s*ma"]})
        self.eq(music_collection, ["/foo/iron maiden - iron maiden.mp3", "/foo/black sabbath - iron man.mp3"], {"title": [":/^Iron\s*Ma"]})
        self.eq(music_collection, ["/foo/ramin djawadi - iron man theme.mp3", "/foo/mark winholtz - ironman hymn.mp3"], {"title": ["!:/^Iron\s*Ma"]})


if __name__ == '__main__':
    unittest.main()
