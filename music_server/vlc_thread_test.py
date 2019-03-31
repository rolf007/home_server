#!/usr/bin/env python3

from music_server import VlcThread
from logger import Logger
import unittest
import time
import os
import sys

class TestLogger():
    def log(self, s):
        #print("TestLogger: %s" % s)
        pass

home_server_root = os.path.split(sys.path[0])[0]

def full_path(filename):
    return os.path.join(home_server_root, "music_server", "test_music", filename)

class TestVlcThread(unittest.TestCase):

    def setUp(self):
        logger = TestLogger()
        self.vlc_thread = VlcThread(logger)
        self.assertEqual(None, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("stopped", self.vlc_thread.get_status())
        self.assertEqual([], self.vlc_thread.get_playlist())


    def tearDown(self):
        self.vlc_thread.shut_down()
        time.sleep(0.1)

    def test_enqueue_at_end_of_playlist__q(self):
        self.vlc_thread.enqueue([full_path("1.mp3"), full_path("2.mp3"), full_path("3.mp3")], 'q')
        time.sleep(0.1)
        self.assertEqual(3, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,5], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))

        self.vlc_thread.next()
        time.sleep(0.1)
        self.assertEqual(4, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,5], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))

        self.vlc_thread.enqueue([full_path("4.mp3"), full_path("5.mp3")], 'q')
        time.sleep(0.1)
        self.assertEqual(4, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,5,6,7], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))
        self.assertEqual("4.mp3", self.vlc_thread.get_filename(6))
        self.assertEqual("5.mp3", self.vlc_thread.get_filename(7))

        self.vlc_thread.stop()
        time.sleep(0.1)
        self.assertEqual(None, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("stopped", self.vlc_thread.get_status())
        self.assertEqual([], self.vlc_thread.get_playlist())

        self.vlc_thread.enqueue([full_path("6.mp3")], 'q')
        time.sleep(0.1)
        self.assertEqual(8, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([8], self.vlc_thread.get_playlist())
        self.assertEqual("6.mp3", self.vlc_thread.get_filename(8))


    def test_clear_playlist_Then_play_this__c(self):
        self.vlc_thread.enqueue([full_path("1.mp3"), full_path("2.mp3"), full_path("3.mp3")], 'c')
        time.sleep(0.1)
        self.assertEqual(3, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,5], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))

        self.vlc_thread.next()
        time.sleep(0.1)
        self.assertEqual(4, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,5], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))

        self.vlc_thread.enqueue([full_path("4.mp3"), full_path("5.mp3")], 'c')
        time.sleep(0.1)
        self.assertEqual(6, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([6,7], self.vlc_thread.get_playlist())
        self.assertEqual("4.mp3", self.vlc_thread.get_filename(6))
        self.assertEqual("5.mp3", self.vlc_thread.get_filename(7))

        self.vlc_thread.stop()
        time.sleep(0.1)
        self.assertEqual(None, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("stopped", self.vlc_thread.get_status())
        self.assertEqual([], self.vlc_thread.get_playlist())

        self.vlc_thread.enqueue([full_path("6.mp3")], 'c')
        time.sleep(0.1)
        self.assertEqual(8, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([8], self.vlc_thread.get_playlist())
        self.assertEqual("6.mp3", self.vlc_thread.get_filename(8))


    def test_play_NOW__n(self):
        self.vlc_thread.enqueue([full_path("1.mp3"), full_path("2.mp3"), full_path("3.mp3")], 'n')
        time.sleep(0.1)
        self.assertEqual(3, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,5], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))

        self.vlc_thread.next()
        time.sleep(0.1)
        self.assertEqual(4, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,5], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))

        self.vlc_thread.enqueue([full_path("4.mp3"), full_path("5.mp3")], 'n')
        time.sleep(0.1)
        self.assertEqual(6, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,6,7,5], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))
        self.assertEqual("4.mp3", self.vlc_thread.get_filename(6))
        self.assertEqual("5.mp3", self.vlc_thread.get_filename(7))

        self.vlc_thread.stop()
        time.sleep(0.1)
        self.assertEqual(None, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("stopped", self.vlc_thread.get_status())
        self.assertEqual([], self.vlc_thread.get_playlist())

        self.vlc_thread.enqueue([full_path("6.mp3")], 'n')
        time.sleep(0.1)
        self.assertEqual(8, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([8], self.vlc_thread.get_playlist())
        self.assertEqual("6.mp3", self.vlc_thread.get_filename(8))

    def test_play_next__x(self):
        self.vlc_thread.enqueue([full_path("1.mp3"), full_path("2.mp3"), full_path("3.mp3")], 'x')
        time.sleep(0.1)
        self.assertEqual(3, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,5], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))

        self.vlc_thread.next()
        time.sleep(0.1)
        self.assertEqual(4, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,5], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))

        self.vlc_thread.enqueue([full_path("4.mp3"), full_path("5.mp3")], 'x')
        time.sleep(0.1)
        self.assertEqual(4, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4,6,7,5], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("2.mp3", self.vlc_thread.get_filename(4))
        self.assertEqual("3.mp3", self.vlc_thread.get_filename(5))
        self.assertEqual("4.mp3", self.vlc_thread.get_filename(6))
        self.assertEqual("5.mp3", self.vlc_thread.get_filename(7))

        self.vlc_thread.stop()
        time.sleep(0.1)
        self.assertEqual(None, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("stopped", self.vlc_thread.get_status())
        self.assertEqual([], self.vlc_thread.get_playlist())

        self.vlc_thread.enqueue([full_path("6.mp3")], 'x')
        time.sleep(0.1)
        self.assertEqual(8, self.vlc_thread.get_cur_playlist_id())
        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([8], self.vlc_thread.get_playlist())
        self.assertEqual("6.mp3", self.vlc_thread.get_filename(8))

if __name__ == '__main__':
    unittest.main()
patch="""
there's a bug in vlc, when using 'move [X][Y]' in remote control (vlc -I rc)
To fix this in gentoo, do this:
create file:
sudo vi /etc/portage/patches/media-video/vlc/move.patch

diff --git a/modules/lua/libs/playlist.c b/modules/lua/libs/playlist.c
index a3f0ee66f8..778263b03d 100644
--- a/modules/lua/libs/playlist.c
+++ b/modules/lua/libs/playlist.c
@@ -165,8 +165,15 @@ static int vlclua_playlist_move( lua_State * L )
     int i_ret;
     if( p_target->i_children != -1 )
         i_ret = playlist_TreeMove( p_playlist, p_item, p_target, 0 );
-    else
-        i_ret = playlist_TreeMove( p_playlist, p_item, p_target->p_parent, p_target->i_id - p_target->p_parent->pp_children[0]->i_id + 1 );
+    else {
+        i_ret = -1;
+        for (int i = 0; i < p_target->p_parent->i_children; ++i)
+            if (p_target->p_parent->pp_children[i]->i_id == p_target->i_id) {
+                i_ret = playlist_TreeMove( p_playlist, p_item, p_target->p_parent, i + 1 );
+                break;
+            }
+    }
+//        i_ret = playlist_TreeMove( p_playlist, p_item, p_target->p_parent, p_target->i_id - p_target->p_parent->pp_children[0]->i_id + 1 );
     PL_UNLOCK;
     return vlclua_push_ret( L, i_ret );
 }

then rebuild:
sudo emerge -av media-video/vlc
"""
