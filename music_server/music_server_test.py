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
        next_song = music_collection.play({"title": ["sani"]})
        self.assertEqual(["/foo/metallica - sanitarium.mp3"], next_song)

    def test_search_artist_and_title(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/rainbow - gates of babylon.mp3":{ "artist": "rainbow", "title": "Gates of Babylon"},
            "/foo/yngwie malmsteen - pictures of home.mp3":{ "artist": "yngwie malmsteen", "title": "Pictures of Home"},
            "/foo/yngwie malmsteen - gates of babylon.mp3":{ "artist": "yngwie malmsteen", "title": "Gates of Babylon"}
            })
        next_song = music_collection.play({"title": ["gates of babylon"], "artist": ["yngwie malmsteen"]})
        self.assertEqual(["/foo/yngwie malmsteen - gates of babylon.mp3"], next_song)

    def test_double_title_search(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - call of the wild.mp3":{ "artist": "metallica", "title": "Call of the Wild"},
            "/foo/metallica - cal of chtulu.mp3":{ "artist": "metallica", "title": "Cal of Chtulu"},
            "/foo/metallica - khtulu returns.mp3":{ "artist": "metallica", "title": "Ktulu Awakens"}
            })
        next_song = music_collection.play({"title": ["Call", "Ktulu"]})
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
        next_song = music_collection.play({"artist": ["metalliac"]})
        self.assertEqual(set(["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3", "/foo/metallica - call of ktulu.mp3"]), set(next_song))

    def test_fuzzy_choose_shortest_match(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - jump in the fire.mp3":{ "artist": "Metallica", "title": "Jump in the fire"},
            "/foo/van halen - jump.mp3":{ "artist": "Van Halen", "title": "Jump"},
            "/foo/c64 - jumping jackson.mp3":{ "artist": "C64", "title": "Jumping Jackson"},
            })
        next_song = music_collection.play({"title": ["jump"]})
        self.assertEqual(set(["/foo/van halen - jump.mp3"]), set(next_song))

    def test_exact_match(self):
        logger = Logger("music_server")
        music_collection = MusicCollection(logger, {
            "/foo/metallica - jump in the fire.mp3":{ "artist": "metallica", "title": "jump in the fire"},
            "/foo/iron maiden - the trooper.mp3":{ "artist": "Iron Maiden", "title": "The Trooper"},
            "/foo/metallica - call of ktulu.mp3":{ "artist": "metallica", "title": "call of ktulu"},
            "/foo/metallica - orion.mp3":{ "artist": "metallica", "title": "Orion"},
            "/foo/acdc - for those about to rock.mp3":{ "artist": "acdc", "title": "For Those about to Rock"}
            })
        # exact match - typo -> no matches
        next_song = music_collection.play({"artist": [",metalliac"]})
        self.assertEqual(set(), set(next_song))
        # fuzzy match - typo -> multiple matches
        next_song = music_collection.play({"artist": ["metalliac"]})
        self.assertEqual(set(["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3", "/foo/metallica - call of ktulu.mp3"]), set(next_song))
        # exact match - no typo -> multiple matches
        next_song = music_collection.play({"artist": [",metallica"]})
        self.assertEqual(set(["/foo/metallica - jump in the fire.mp3", "/foo/metallica - orion.mp3", "/foo/metallica - call of ktulu.mp3"]), set(next_song))

if __name__ == '__main__':
    unittest.main()
