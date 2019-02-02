#!/usr/bin/env python3

import argparse
import curses
from enum import Enum
import eyed3
import locale
import os
import re
import signal
from operator import itemgetter

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

#configure midnight commander:
#sudo vi /etc/mc/mc.ext
#line 482
#shell/i/.mp3
#Open=home/<user>/home_server/music_server/id3_edit.py %u

class Id3Edit:
    def __init__(self, mp3s):
        if len(args.mp3s) != 1 or not os.path.isdir(args.mp3s[0]):
            print("argument must be exactly one directory!")

    def main(self, screen):
        self.running = True
        self.debug = ""
        self.screen = screen
        self.screen.refresh()
        self.height, self.width = self.screen.getmaxyx()
        # don't echo key strokes on the screen
        curses.noecho()
        # read keystrokes instantly, without waiting for enter to ne pressed
        curses.cbreak()
        # enable keypad mode
        self.screen.keypad(1)
        # disable drawing of cursor
        curses.curs_set(0)
        curses.start_color()
        #                   fg                  bg
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        self.style_text_cursor = curses.color_pair(1)

        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
        self.style_text_none = curses.color_pair(2)

        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_CYAN)
        self.style_text_cursor_selected = curses.color_pair(3)|curses.A_BOLD

        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        self.style_text_selected = curses.color_pair(4)|curses.A_BOLD

        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)
        self.style_text_center_cursor = curses.color_pair(5)

        curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_WHITE)
        self.style_text_center_cursor_selected = curses.color_pair(6)|curses.A_BOLD

        curses.init_pair(7, 15, curses.COLOR_BLUE)
        self.style_ornaments = curses.color_pair(7)

        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE)
        self.style_dir = curses.color_pair(8)

        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_CYAN)
        self.style_help_line_val = curses.color_pair(9)

        curses.init_pair(10, 15, curses.COLOR_BLACK)
        self.style_help_line_key = curses.color_pair(10)

        curses.init_pair(11, 15, curses.COLOR_RED)
        self.style_edit_ornaments = curses.color_pair(11)

        curses.init_pair(12, curses.COLOR_BLACK, 9)
        self.style_edit_help_line_val = curses.color_pair(12)

        curses.init_pair(13, 15, curses.COLOR_GREEN)
        self.style_fix_ornaments = curses.color_pair(13)

        self.dir_cursor = 0
        self.dirs = []

        self.num_columns = 8
        self.pads = []
        for i in range(self.num_columns):
            self.pads.append(curses.newpad(5,5))

        directory = args.mp3s[0]
        for root, dirs, fils in os.walk(directory):
            if len(fils) > 0:
                self.dirs.append(root)

        self.change_dir()
        self.resize()

        c = None
        while self.running:
            try:
                self.draw()
                if self.menu == "fix":
                    self.fix_menu_draw()
                elif self.menu == "edit":
                    self.edit_menu_draw()
                elif self.menu == "main":
                    self.main_menu_draw()
                if c:
                    self.screen.addstr(0, 30, "%s %s" % (str(c), self.debug), curses.A_BOLD)
            except curses.error:
                pass
            c = self.screen.getch()
            if c == curses.KEY_RESIZE:
                self.resize()
            ch = None
            if c == 0x1b:
                ch = '<esc>'
            elif c == 0x09:
                ch = '<tab>'
            elif c == 262:
                ch = '<home>'
            elif c == 360:
                ch = '<end>'
            elif c == 553:
                ch = '<c-left>'
            elif c == 568:
                ch = '<c-right>'
            elif c == 0x0a:
                ch = '<cr>'
            elif c == 0x7f:
                ch = '<bs>'
            elif c == 0x01:
                ch = '<c-a>'
            elif c == 0x10:
                ch = '<c-p>'
            elif c == 0x19:
                ch = '<c-y>'
            elif c == 258:
                ch = '<down>'
            elif c == 259:
                ch = '<up>'
            elif c == 261:
                ch = '<right>'
            elif c == 260:
                ch = '<left>'
            else:
                ch = chr(c)

            if self.menu == "main":
                self.main_menu_handle_input(ch)
            elif self.menu == "fix":
                self.fix_menu_handle_input(ch)
            elif self.menu == "edit":
                self.edit_menu_handle_input(ch)

    def resize(self):
        self.screen.clear()
        self.height, self.width = self.screen.getmaxyx()
        self.main_max_rows = self.height-6
        c2 = 5
        c6 = 9
        c7 = 6
        w = self.width - c2 - c6 - c7 -5*4-1
        c0 = int(w*20/100+0.2) + 5
        c1 = int(w*20/100+0.4) + 5
        c3 = int(w*20/100+0.6) + 5
        c4 = int(w*20/100+0.8) + 5
        c5 = self.width - c0 - c1 - c2 - c3 - c4 - c6 - c7-1
        self.adj = [c0,c1,c2,c3,c4,c5,c6,c7]

    def change_dir(self):
        self.main_scroll = 0
        self.main_scroll_offset = 2
        self.main_cursor_x = 0
        self.main_cursor_y = 0
        self.fix_cursor_x = 0
        self.files = []
        self.menu = "main"
        self.selected = []
        for root, dirs, fils in os.walk(self.dirs[self.dir_cursor]):
            for file in fils:
                url = os.path.join(root, file)
                audiofile = eyed3.load(url)
                if audiofile and audiofile.tag:
                    self.files.append({"id3": audiofile, "selected": False, "url": file})
            self.files = sorted(self.files, key=itemgetter("url"))

    def repr_item_help(self, s):
        if s is None:
            return "<None>"
        return s

    def repr_item(self, x, file):
        if x == 0:
            return self.repr_item_help(file["url"])
        elif x == 1:
            return self.repr_item_help(file["id3"].tag.album)
        elif x == 2:
            s = file["id3"].tag.track_num
            if s[0] and s[1]:
                return "%d/%d" % (s[0],s[1])
            elif s[0]:
                return "%d" % s[0]
            else:
                return '/'
        elif x == 3:
            return self.repr_item_help(file["id3"].tag.artist)
        elif x == 4:
            return self.repr_item_help(file["id3"].tag.title)
        elif x == 5:
            s = file["id3"].tag.genre
            if s.id != None:
                return "(%d)%s" % (s.id, s.name)
            else:
                return "()%s" % s.name
        elif x == 6:
            s = file["id3"].tag.release_date
            if s is None:
                return "<None>"
            return str(s)
        elif x == 7:
            s = file["id3"].tag.version
            if s is None:
                return "<None>"
            return ".".join("%d" % d for d in s)
        return "unknown column"

    def just(self, s, adj):
        return s.ljust(adj)[:adj]

    def get_column_name(self, x):
        column_names = ["Url", "Album", "Track_num", "Artist", "Title", "Genre", "Release date", "Version"]
        return column_names[x]

    def get_color(self, x, y):
        if self.main_cursor_y == y or self.main_cursor_x == x:
            if self.main_cursor_y == y and self.main_cursor_x == x:
                if y < len(self.files) and self.files[y]["selected"]:
                    color = self.style_text_center_cursor_selected
                else:
                    color = self.style_text_center_cursor
            else:
                if y < len(self.files) and self.files[y]["selected"]:
                    color = self.style_text_cursor_selected
                else:
                    color = self.style_text_cursor
        else:
            if y < len(self.files) and self.files[y]["selected"]:
                color = self.style_text_selected
            else:
                color = self.style_text_none
        return color

    def get_item(self, x, file):
        url = file["url"]
        album = file["id3"].tag.album
        track_num = file["id3"].tag.track_num
        artist = file["id3"].tag.artist
        title = file["id3"].tag.title
        genre = file["id3"].tag.genre
        release_date = file["id3"].tag.release_date
        version = file["id3"].tag.version
        columns = [url, album, track_num, artist, title, genre, release_date, version]
        return columns[x]

    def set_item(self, x, file, value):
        try:
            if x == 0:
                file["url"] = value
            elif x == 1:
                file["id3"].tag.album = value
            elif x == 2:
                if '/' in value:
                    file["id3"].tag.track_num = tuple([int(x) for x in value.split('/')])
                elif value == "":
                    file["id3"].tag.track_num = (None, None)
                else:
                    file["id3"].tag.track_num = int(value)
            elif x == 3:
                file["id3"].tag.artist = value
            elif x == 4:
                file["id3"].tag.title = value
            elif x == 5:
                file["id3"].tag.genre = value
            elif x == 6:
                file["id3"].tag.release_date = value
        except ValueError:
            pass

    def set_selected_set(self):
        self.selected = []
        for f in self.files:
            if f["selected"]:
                self.selected.append(f)
        if len(self.selected) == 0:
            self.selected = [self.files[self.main_cursor_y]]

    def draw(self):
        self.screen.erase()
        win = curses.newwin(self.height, self.width)
        win.addch(0,0, curses.ACS_ULCORNER, self.style_ornaments)
        win.addch(0,1, 60, self.style_ornaments)
        win.addch(0,2, curses.ACS_HLINE, self.style_ornaments)
        win.addch(0,self.width-1, curses.ACS_URCORNER, self.style_ornaments)
        dir_repr = (" %s " % self.dirs[self.dir_cursor])[:self.width-10]
        dir_repr_len = len(dir_repr)
        win.hline(0,dir_repr_len+3, curses.ACS_HLINE, self.width-5-dir_repr_len, self.style_ornaments)
        win.addch(0,self.width-2, 62, self.style_ornaments)
        win.addstr(0, 3, dir_repr, self.style_dir)
        color = self.style_text_selected
        x = 1
        for column in range(self.num_columns):
            win.addstr(1, x, self.just(self.get_column_name(column), self.adj[column]-1), color)
            x += self.adj[column]

        x = 0
        for k in range(self.num_columns + 1):
            win.vline(1,x,curses.ACS_VLINE,self.height-5,self.style_ornaments)
            if k < len(self.adj):
                x += self.adj[k]
        win.hline(self.main_max_rows+2,1, curses.ACS_HLINE, self.width-2, self.style_ornaments)
        win.addch(self.main_max_rows+2,0, curses.ACS_LTEE, self.style_ornaments)
        win.addch(self.main_max_rows+2,self.width-1, curses.ACS_RTEE, self.style_ornaments)
        win.addch(self.main_max_rows+3,0, curses.ACS_VLINE, self.style_ornaments)
        win.addch(self.main_max_rows+3,self.width-1, curses.ACS_VLINE, self.style_ornaments)
        win.addch(self.main_max_rows+4,0, curses.ACS_LLCORNER, self.style_ornaments)
        win.addch(self.main_max_rows+4,self.width-1, curses.ACS_LRCORNER, self.style_ornaments)
        win.hline(self.main_max_rows+4,1, curses.ACS_HLINE, self.width-2, self.style_ornaments)

        pad_height = max(len(self.files), self.height-6)+1
        for i in range(self.num_columns):
            self.pads[i].resize(pad_height, self.adj[i]-1)
        column = 0
        for pad in self.pads:
            i = 0
            for file in self.files:
                pad.addstr(i, 0, self.just(self.repr_item(column, file), self.adj[column]-1), self.get_color(column, i))
                i = i + 1
            while i < pad_height-1:
                pad.addstr(i, 0, self.just("", self.adj[column]-1), self.get_color(column, i))
                i = i + 1
            column = column + 1

        if len(self.files):
            cur_file = self.files[self.main_cursor_y]
            win.addstr(self.main_max_rows+3, 1, self.just(self.repr_item(self.main_cursor_x, cur_file), self.width-2), self.style_text_none)
        self.screen.refresh()
        win.refresh()
        x = 0
        column = 0
        for pad in self.pads:
            pad.refresh(self.main_scroll, 0, 2, x+1, self.height-5, x+self.adj[column]-1)
            x += self.adj[column]
            column = column + 1

    def draw_help_line(self, win, y, w, style, help_dict):
        num_items = len(help_dict)
        keys_len = 0
        vals_len = 0
        for key, val in help_dict.items():
            keys_len += len(key)
            vals_len += len(val)
        extra_room = w - keys_len - vals_len
        key_len = [0]*num_items
        val_len = [0]*num_items
        i = 0
        if extra_room >= 0:
            for key, val in help_dict.items():
                key_len[i] = len(key)
                val_len[i] = len(val) + int(len(val)*extra_room/vals_len)
                i = i + 1
        else:
            extra_room2 = w - keys_len
            if extra_room2 >= 0:
                for key, val in help_dict.items():
                    key_len[i] = len(key)
                    val_len[i] = int(len(val) + len(val)*extra_room/vals_len)
                    i = i + 1
            else:
                for key, val in help_dict.items():
                    key_len[i] = len(key) + int(len(key)*extra_room2/keys_len)
                    i = i + 1
        x = 0
        i = 0
        for key, val in help_dict.items():
            win.addstr(y, x, self.just(key, key_len[i]), self.style_help_line_key)
            x += key_len[i]
            if i == num_items-1:
                vl = w-x-1
            else:
                vl = val_len[i]
            win.addstr(y, x, self.just(val, vl), style)
            x += val_len[i]
            i = i + 1

    def suggest_algo_fs(self, file):
        suggestion = "xx"
        if self.fix_cursor_x >= 0:
            filename_items = re.split("[ _]-[ _]", file["url"])
            if self.fix_cursor_x < len(filename_items):
                suggestion = filename_items[self.fix_cursor_x]
            else:
                suggestion = filename_items[-1]
        else:
            path = str(os.getcwd()).split('/')
            if -self.fix_cursor_x < len(path):
                suggestion = path[self.fix_cursor_x]
            else:
                suggestion = "foo"
        return suggestion

    def suggest_algo_from_id3(self, file):
        artist = self.get_item(3, file)
        title = self.get_item(4, file)
        filename, ext = os.path.splitext(file["url"])
        track = self.get_item(2, file)
        if track: track = track[0]
        ret = ""
        if track:
            ret += "%02d" % track
        if artist:
            if ret:
                ret += ' - '
            ret += artist
        if title:
            if ret:
                ret += ' - '
            ret += title
        ret += ext
        return ret

    def suggest_algo_track_number(self, i, n):
        return "%d/%d" % (i+1,n)

    def get_suggestion(self, file, j, num_selected):
        if self.main_cursor_x == 0:
            return self.suggest_algo_from_id3(file)
        elif self.main_cursor_x == 1 or self.main_cursor_x == 3 or self.main_cursor_x == 4:
            return self.suggest_algo_fs(file)
        elif self.main_cursor_x == 2:
            return self.suggest_algo_track_number(j, num_selected)
        return None

    def main_menu_draw(self):
        self.draw_help_line(self.screen, self.height-1, self.width, self.style_help_line_val, {"<space>": "toggle select", "<c-a>": "select all/none", "f": "fix id3 for selected column", "e": "edit id3 for selected column", "<c-y>": "copy", "n/p": "next/previous dir", "q": "quit"})

    def main_menu_handle_input(self, ch):
        if ch == 'q':
            self.running = False
        elif ch == '<up>':
            if self.main_cursor_y > 0:
                self.main_cursor_y -= 1
            if self.main_scroll > 0 and self.main_cursor_y - self.main_scroll < self.main_scroll_offset:
                self.main_scroll -= 1
        elif ch == '<down>':
            if self.main_cursor_y < len(self.files) - 1:
                self.main_cursor_y += 1
            if self.main_scroll < len(self.files) - self.main_max_rows and self.main_cursor_y - self.main_scroll > self.main_max_rows - self.main_scroll_offset - 1:
                self.main_scroll += 1
        elif ch == '<right>':
            if self.main_cursor_x < self.num_columns - 1:
                self.main_cursor_x += 1
        elif ch == '<left>':
            if self.main_cursor_x > 0:
                self.main_cursor_x -= 1
        elif ch == 'n':
            if self.dir_cursor < len(self.dirs) - 1:
                self.dir_cursor += 1
                self.change_dir()
        elif ch == 'p':
            if self.dir_cursor > 0:
                self.dir_cursor -= 1
                self.change_dir()
        elif ch == ' ':
            self.files[self.main_cursor_y]["selected"] = not self.files[self.main_cursor_y]["selected"]
        elif ch == '<c-a>':
            if len(self.files) > 0:
                b = self.files[0]["selected"]
                for f in self.files:
                    f["selected"] = not b
        elif ch == '<c-y>':
            self.clipboard = self.repr_item(self.main_cursor_x, self.files[self.main_cursor_y])
        elif ch == 'f':
            if self.main_cursor_x != 5 and self.main_cursor_x != 6 and self.main_cursor_x != 7:
                self.set_selected_set()
                self.fix_scroll = 0
                self.menu = "fix"
        elif ch == 'e':
            if self.main_cursor_x != 7:
                self.set_selected_set()
                self.edit_scroll = 0
                self.edit_value = ["(.*)", "\\1"]
                self.edit_cursor_y = 1
                self.edit_cursor_x0 = [0, 0]
                self.edit_cursor_x1 = [len(self.edit_value[0]), len(self.edit_value[1])]
                self.menu = "edit"

    def edit_menu_draw(self):
        h = self.height-8
        w = self.width-10
        y = 4
        x = 5
        edit_win = curses.newwin(h,w,y,x)
        edit_win.addch(0,0,curses.ACS_ULCORNER, self.style_edit_ornaments)
        edit_win.hline(0,1,curses.ACS_HLINE,w-2, self.style_edit_ornaments)
        edit_win.addch(0,w-1,curses.ACS_URCORNER, self.style_edit_ornaments)
        edit_win.vline(1,0,curses.ACS_VLINE,h-5, self.style_edit_ornaments)
        edit_win.vline(1,w-1,curses.ACS_VLINE,h-5, self.style_edit_ornaments)
        edit_win.addch(h-4,0,curses.ACS_LTEE, self.style_edit_ornaments)
        edit_win.hline(h-4,1,curses.ACS_HLINE,w-2, self.style_edit_ornaments)
        edit_win.addch(h-4,w-1,curses.ACS_RTEE, self.style_edit_ornaments)
        edit_win.vline(h-3,0,curses.ACS_VLINE,2, self.style_edit_ornaments)
        edit_win.addch(h-3,1,'S', self.style_edit_ornaments)
        edit_win.addch(h-2,1,'R', self.style_edit_ornaments)
        edit_win.vline(h-3,2,58,2, self.style_edit_ornaments)
        edit_win.vline(h-3,3,curses.ACS_VLINE,2, self.style_edit_ornaments)
        edit_win.vline(h-3,w-1,curses.ACS_VLINE,2, self.style_edit_ornaments)
        edit_win.addch(h-1,0,curses.ACS_LLCORNER, self.style_edit_ornaments)
        edit_win.hline(h-1,1,curses.ACS_HLINE,w-2, self.style_edit_ornaments)
        edit_win.addstr(0,int(w/2)-5," Edit Menu ", self.style_fix_ornaments)

        #edit_win.addch(h-1,w-1,curses.ACS_LRCORNER, self.style_edit_ornaments)

        pad_height = max(len(self.selected), h-3)+1
        edit_pad = curses.newpad(pad_height,w-2)
        data = []
        max_len_cur_val = 0
        for sel in self.selected:
            cur_val = self.repr_item(self.main_cursor_x, sel)
            try:
                new_val = re.sub(self.edit_value[0], self.edit_value[1], cur_val, flags=re.DOTALL)
            except re.error:
                new_val = "<bad regex>"
            data.append((cur_val, new_val))
            if len(cur_val) > max_len_cur_val:
                max_len_cur_val = len(cur_val)

        i = 0
        for cur_val, new_val in data:
            edit_pad.addstr(i, 0, self.just("%s -> %s" % (self.just(cur_val, max_len_cur_val), new_val), w-2), self.style_edit_ornaments)
            i = i + 1
        while i < pad_height-1:
            edit_pad.addstr(i, 0, self.just("", w-2), self.style_edit_ornaments)
            i = i + 1

        sr_text_y = h-3
        sr_text_x = 4
        for z in [0, 1]:
            v = self.edit_value[z] + " "
            if self.edit_cursor_y == z:
                left = min(self.edit_cursor_x0[z], self.edit_cursor_x1[z])
                right = max(self.edit_cursor_x0[z], self.edit_cursor_x1[z])+1
                edit_win.addstr(sr_text_y+z, sr_text_x, v[:left], self.style_edit_ornaments)
                edit_win.addstr(sr_text_y+z, sr_text_x+left, v[left:right], curses.A_REVERSE)
                edit_win.addstr(sr_text_y+z, sr_text_x+right, v[right:], self.style_edit_ornaments)
            else:
                edit_win.addstr(sr_text_y+z, sr_text_x, v, self.style_edit_ornaments)
            edit_win.hline(sr_text_y+z, sr_text_x+len(v), " ", w-len(v)-5, self.style_edit_ornaments)
        self.draw_help_line(self.screen, self.height-1, self.width, self.style_edit_help_line_val, {"<c-a>": "Select all", "<tab>": "search/replace", "<esc>": "Cancel", "<cr>": "Ok"})
        edit_win.refresh()
        edit_pad.refresh(self.edit_scroll, 0, y+1, x+1, y+h-5, x+ w-2)

    def edit_menu_handle_input(self, ch):
        if ch == '<esc>':
            self.menu = "main"
        elif ch == '<tab>':
            if self.edit_cursor_y == 1:
                self.edit_cursor_y = 0
            else:
                self.edit_cursor_y = 1
        elif ch == '<up>':
            if self.edit_scroll > 0:
                self.edit_scroll -= 1
        elif ch == '<down>':
            pass
        elif ch == '<right>':
            y = self.edit_cursor_y
            if self.edit_cursor_x1[y] < len(self.edit_value[y]):
                self.edit_cursor_x1[y] += 1
            self.edit_cursor_x0[y] = self.edit_cursor_x1[y]
        elif ch == '<left>':
            y = self.edit_cursor_y
            if self.edit_cursor_x1[y] > 0:
                self.edit_cursor_x1[y] -= 1
            self.edit_cursor_x0[y] = self.edit_cursor_x1[y]
        elif ch == '<c-right>':
            y = self.edit_cursor_y
            if self.edit_cursor_x1[y] < len(self.edit_value[y]):
                self.edit_cursor_x1[y] += 1
        elif ch == '<c-left>':
            y = self.edit_cursor_y
            if self.edit_cursor_x1[y] > 0:
                self.edit_cursor_x1[y] -= 1
        elif ch == '<home>':
            y = self.edit_cursor_y
            self.edit_cursor_x0[y] = 0
            self.edit_cursor_x1[y] = 0
        elif ch == '<end>':
            y = self.edit_cursor_y
            self.edit_cursor_x0[y] = len(self.edit_value[y])
            self.edit_cursor_x1[y] = len(self.edit_value[y])
        elif ch == '<c-a>':
            y = self.edit_cursor_y
            self.edit_cursor_x0[y] = 0
            self.edit_cursor_x1[y] = len(self.edit_value[y])
        elif ch == '<c-y>':
            y = self.edit_cursor_y
            left = min(self.edit_cursor_x0[y], self.edit_cursor_x1[y])
            right = max(self.edit_cursor_x0[y], self.edit_cursor_x1[y])
            self.clipboard = self.edit_value[y][left:right]
        elif ch == '<c-p>':
            y = self.edit_cursor_y
            left = min(self.edit_cursor_x0[y], self.edit_cursor_x1[y])
            right = max(self.edit_cursor_x0[y], self.edit_cursor_x1[y])
            self.edit_value[y] = self.edit_value[y][:left] + self.clipboard + self.edit_value[y][right:]
            self.edit_cursor_x1[y] = left + len(self.clipboard)
            self.edit_cursor_x0[y] = left + len(self.clipboard)
        elif ch == '<cr>':
            self.perform_edit()
            self.menu = "main"
        elif ch == '<bs>':
            y = self.edit_cursor_y
            left = min(self.edit_cursor_x0[y], self.edit_cursor_x1[y])
            right = max(self.edit_cursor_x0[y], self.edit_cursor_x1[y])
            if left != right or left != 0:
                if left == right:
                    left = left - 1
                self.edit_value[y] = self.edit_value[y][:left] + self.edit_value[y][right:]
                self.edit_cursor_x1[y] = left
                self.edit_cursor_x0[y] = self.edit_cursor_x1[y]
        elif ch != None and len(ch) == 1 and ch >= ' ' and ch <= '~':
            y = self.edit_cursor_y
            left = min(self.edit_cursor_x0[y], self.edit_cursor_x1[y])
            right = max(self.edit_cursor_x0[y], self.edit_cursor_x1[y])
            self.edit_value[y] = self.edit_value[y][:left] + ch + self.edit_value[y][right:]
            self.edit_cursor_x1[y] = left + 1
            self.edit_cursor_x0[y] = left + 1

    def fix_menu_draw(self):
        h = self.height-8
        w = self.width-10
        y = 4
        x = 5
        fix_win = curses.newwin(h,w,y,x)
        fix_win.addch(0,0,curses.ACS_ULCORNER, self.style_fix_ornaments)
        fix_win.hline(0,1,curses.ACS_HLINE,w-2, self.style_fix_ornaments)
        fix_win.addch(0,w-1,curses.ACS_URCORNER, self.style_fix_ornaments)
        fix_win.vline(1,0,curses.ACS_VLINE,h-4, self.style_fix_ornaments)
        fix_win.vline(1,w-1,curses.ACS_VLINE,h-4, self.style_fix_ornaments)
        fix_win.addch(h-3,0,curses.ACS_LTEE, self.style_fix_ornaments)
        fix_win.hline(h-3,1,curses.ACS_HLINE,w-2, self.style_fix_ornaments)
        fix_win.addch(h-3,w-1,curses.ACS_RTEE, self.style_fix_ornaments)
        fix_win.vline(h-2,0,curses.ACS_VLINE,1, self.style_fix_ornaments)
        fix_win.addstr(h-2,1,'Algo', self.style_fix_ornaments)
        fix_win.addch(h-2,5,58, self.style_fix_ornaments)
        fix_win.addch(h-2,6,curses.ACS_VLINE, self.style_fix_ornaments)
        fix_win.vline(h-2,w-1,curses.ACS_VLINE,1, self.style_fix_ornaments)
        fix_win.addch(h-1,0,curses.ACS_LLCORNER, self.style_fix_ornaments)
        fix_win.hline(h-1,1,curses.ACS_HLINE,w-2, self.style_fix_ornaments)
        #fix_win.addch(h-2,w-1,curses.ACS_LRCORNER, self.style_fix_ornaments)
        fix_win.addstr(0,int(w/2)-5," Fix Menu ", self.style_fix_ornaments)

        pad_height = max(len(self.selected), h-2)+1
        fix_pad = curses.newpad(pad_height,w-2)
        data = []
        max_len_cur_val = 0
        num_selected = len(self.selected)
        j = 0
        for sel in self.selected:
            cur_val = self.repr_item(self.main_cursor_x, sel)
            new_val = self.get_suggestion(sel, j, num_selected)
            data.append((cur_val, new_val))
            if len(cur_val) > max_len_cur_val:
                max_len_cur_val = len(cur_val)
            j = j + 1

        i = 0
        for cur_val, new_val in data:
            fix_pad.addstr(i, 0, self.just("%s -> %s" % (self.just(cur_val, max_len_cur_val), new_val), w-2), self.style_fix_ornaments)
            i = i + 1
        while i < pad_height-1:
            fix_pad.addstr(i, 0, self.just("", w-2), self.style_fix_ornaments)
            i = i + 1

        self.draw_help_line(self.screen, self.height-1, self.width, self.style_fix_ornaments, {"<left>/<right>": "Select Algo", "<esc>": "Cancel", "<cr>": "Ok"})
        fix_win.refresh()
        fix_pad.refresh(self.fix_scroll, 0, y+1, x+1, y+h-4, x+ w-2)



    def fix_menu_handle_input(self, ch):
        if ch == '<esc>':
            self.menu = "main"
        elif ch == '<right>':
            self.fix_cursor_x += 1
        elif ch == '<left>':
            self.fix_cursor_x -= 1
        elif ch == '<cr>':
            self.perform_fix()
            self.menu = "main"

    def perform_edit(self):
        for file in self.selected:
            current = self.repr_item(self.main_cursor_x, file)
            try:
                suggestion = re.sub(self.edit_value[0], self.edit_value[1], current, flags=re.DOTALL)
            except re.error:
                suggestion = current
            self.set_item(self.main_cursor_x, file, suggestion)

    def perform_fix(self):
        num_selected = len(self.selected)
        j = 0
        for file in self.selected:
            suggestion = self.get_suggestion(file, j, num_selected)
            self.set_item(self.main_cursor_x, file, suggestion)
            j = j + 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mp3s', nargs='+')
    args = parser.parse_args()
    id3edit = Id3Edit(args.mp3s)
    s = signal.signal(signal.SIGINT, signal.SIG_IGN)
    curses.wrapper(id3edit.main)
    s = signal.signal(signal.SIGINT, signal.SIG_IGN)
