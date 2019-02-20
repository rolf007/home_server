#!/usr/bin/env python3

import argparse
from copy import deepcopy
import curses
from enum import Enum
import eyed3
import locale
import os
import parser
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
        i = 0
        #                   fg                  bg
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        self.style_text_no_cursor = curses.color_pair(1)

        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
        self.style_text_cursor = curses.color_pair(2)

        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        self.style_text_center_cursor = curses.color_pair(3)

        curses.init_pair(4, 11, curses.COLOR_BLUE)
        self.style_text_selected = curses.color_pair(4)|curses.A_BOLD

        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_CYAN)
        self.style_text_cursor_selected = curses.color_pair(5)|curses.A_BOLD

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

        curses.init_pair(11, 15, curses.COLOR_GREEN)
        self.style_edit_ornaments = curses.color_pair(11)

        curses.init_pair(12, curses.COLOR_BLACK, 10)
        self.style_edit_help_line_val = curses.color_pair(12)

        curses.init_pair(13, 15, curses.COLOR_RED)
        self.style_error = curses.color_pair(13)

        curses.init_pair(14, 15, curses.COLOR_BLUE)
        self.style_text_modified = curses.color_pair(14)|curses.A_BOLD

        curses.init_pair(15, 15, curses.COLOR_CYAN)
        self.style_text_cursor_modified = curses.color_pair(15)|curses.A_BOLD

        curses.init_pair(16, 15, curses.COLOR_WHITE)
        self.style_text_center_cursor_modified = curses.color_pair(16)|curses.A_BOLD


        self.dir_cursor = 0
        self.dirs = []
        self.dialog = None
        self.menu = "main"

        self.num_columns = 8
        self.pads = []
        for i in range(self.num_columns):
            self.pads.append(curses.newpad(5,5))

        directory = args.mp3s[0]
        for root, dirs, fils in os.walk(directory):
            if len(fils) > 0:
                self.dirs.append(root)

        self.main_cursor_x = 0
        self.change_dir()
        self.resize()

        c = None
        while self.running:
            try:
                self.draw()
                if self.menu == "edit":
                    self.edit_menu_draw()
                elif self.menu == "main":
                    self.main_menu_draw()
                if self.dialog:
                    self.dialog_draw()
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
            elif c == 353:
                ch = '<s-tab>'
            elif c == 553:
                ch = '<c-left>'
            elif c == 568:
                ch = '<c-right>'
            elif c == 0x0a:
                ch = '<cr>'
            elif c == 0x7f:
                ch = '<bs>'
            elif c == 330:
                ch = '<del>'
            elif c == 0x01:
                ch = '<c-a>'
            elif c == 0x13:
                ch = '<c-s>'
            elif c == 263:
                ch = '<c-h>'
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

            if self.dialog:
                self.dialog_handle_input(ch)
            else:
                if self.menu == "main":
                    self.main_menu_handle_input(ch)
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

    def save(self):
        for file in self.files:
            file["id3"].tag.save()
            if file["url"] != file["old_url"]:
                root = self.dirs[self.dir_cursor]
                old_name = os.path.join(root, file["old_url"])
                new_name = os.path.join(root, file["url"])
                os.rename(old_name, new_name)

    def change_dir(self):
        self.main_scroll = 0
        self.main_scroll_offset = 2
        self.main_cursor_y = 0
        self.files = []
        self.selected = []
        root = self.dirs[self.dir_cursor]
        for file in os.listdir(root):
            url = os.path.join(root, file)
            if os.path.isfile(url):
                audiofile = eyed3.load(url)
                if audiofile and audiofile.tag:
                    self.files.append({
                        "id3": audiofile,
                        "selected": False,
                        "url": file,
                        "old_url": file,
                        "old_album": audiofile.tag.album,
                        "old_track": audiofile.tag.track_num,
                        "old_artist": audiofile.tag.artist,
                        "old_title": audiofile.tag.title,
                        "old_genre": audiofile.tag.genre,
                        "old_release": audiofile.tag.release_date,
                        "old_version": audiofile.tag.version})
        self.files = sorted(self.files, key=itemgetter("url"))

    def repr_item_help(self, s):
        if s is None:
            return ""
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
                return ""
        elif x == 3:
            return self.repr_item_help(file["id3"].tag.artist)
        elif x == 4:
            return self.repr_item_help(file["id3"].tag.title)
        elif x == 5:
            s = file["id3"].tag.genre
            if s:
                if s.id != None:
                    return "(%d)%s" % (s.id, s.name)
                else:
                    return "()%s" % s.name
            else:
                return ""
        elif x == 6:
            s = file["id3"].tag.release_date
            if s is None:
                return ""
            return str(s)
        elif x == 7:
            s = file["id3"].tag.version
            if s is None:
                return ""
            return ".".join("%d" % d for d in s)
        return "unknown column"

    def just(self, s, adj):
        return s.ljust(adj)[:adj]

    def get_column_name(self, x):
        column_names = ["Url", "Album", "Track_num", "Artist", "Title", "Genre", "Release date", "Version"]
        return column_names[x]

    def get_color(self, x, y, star, modified):
        selected = y < len(self.files) and self.files[y]["selected"]
        if self.main_cursor_y == y or self.main_cursor_x == x:
            if self.main_cursor_y == y and self.main_cursor_x == x:
                cursor = 2
            else:
                cursor = 1
        else:
            cursor = 0

        if star:
            if cursor == 2:
                return self.style_text_center_cursor_modified
            elif cursor == 1:
                return self.style_text_cursor_modified
            else:
                return self.style_text_modified

        if selected:
            if cursor == 2:
                return self.style_text_center_cursor_selected
            elif cursor == 1:
                return self.style_text_cursor_selected
            else:
                return self.style_text_selected
        elif modified:
            if cursor == 2:
                return self.style_text_center_cursor_modified
            elif cursor == 1:
                return self.style_text_cursor_modified
            else:
                return self.style_text_modified
        else:
            if cursor == 2:
                return self.style_text_center_cursor
            elif cursor == 1:
                return self.style_text_cursor
            else:
                return self.style_text_no_cursor

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
            return False
        return True

    def modified(self, file, column):
        if column == 0:
            return file["url"] != file["old_url"]
        elif column == 1:
            return file["id3"].tag.album != file["old_album"]
        elif column == 2:
            return file["id3"].tag.track_num != file["old_track"]
        elif column == 3:
            return file["id3"].tag.artist != file["old_artist"]
        elif column == 4:
            return file["id3"].tag.title != file["old_title"]
        elif column == 5:
            return file["id3"].tag.genre != file["old_genre"]
        elif column == 6:
            return file["id3"].tag.release_date != file["old_release"]
        elif column == 7:
            return file["id3"].tag.version != file["old_version"]
        return False

    def anything_modified(self):
        for file in self.files:
            for column in range(self.num_columns):
                if self.modified(file, column):
                    return True
        return False

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
                text = self.just(self.repr_item(column, file), self.adj[column]-1)
                modified = self.modified(file, column)

                if modified:
                    text = text[:-1]
                    pad.addstr(i, self.adj[column]-2, "*", self.get_color(column, i, True, modified))
                pad.addstr(i, 0, text, self.get_color(column, i, False, modified))
                i = i + 1
            while i < pad_height-1:
                pad.addstr(i, 0, self.just("", self.adj[column]-1), self.get_color(column, i, False, False))
                i = i + 1
            column = column + 1

        if len(self.files):
            cur_file = self.files[self.main_cursor_y]
            win.addstr(self.main_max_rows+3, 1, self.just(self.repr_item(self.main_cursor_x, cur_file), self.width-2), self.style_text_no_cursor)
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


    def main_menu_draw(self):
        self.draw_help_line(self.screen, self.height-1, self.width, self.style_help_line_val, {"<space>": "toggle select", "<c-a>": "select all/none", "<c-s>": "save", "e": "edit id3 for selected column", "<c-y>": "copy", "n/p": "next/previous dir", "q": "quit"})

    def main_menu_handle_input(self, ch):
        if ch == 'q':
            def f(self): self.running = False
            self.dialog = {"title":" Really Quit? ", "options":{'y':("Quit", f), 'n': ("Don't quit", None)}}
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
                def cd(self):
                    self.dir_cursor += 1
                    self.change_dir()
                def save(self):
                    self.save()
                    cd(self)
                if self.anything_modified():
                    self.dialog = {"title":" There are Modifications. Really go to next? ", "options":{'s':("Save modifications", save), 'd': ("Discard modifications", cd), 'c': ("Cancel", None)}}
                else:
                    cd(self)
        elif ch == 'p':
            if self.dir_cursor > 0:
                def cd(self):
                    self.dir_cursor -= 1
                    self.change_dir()
                def save(self):
                    self.save()
                    cd(self)
                if self.anything_modified():
                    self.dialog = {"title":" There are Modifications. Really go to prev? ", "options":{'s':("Save modifications", save), 'd': ("Discard modifications", cd), 'c': ("Cancel", None)}}
                else:
                    cd(self)
        elif ch == ' ':
            self.files[self.main_cursor_y]["selected"] = not self.files[self.main_cursor_y]["selected"]
        elif ch == '<c-a>':
            if len(self.files) > 0:
                b = self.files[0]["selected"]
                for f in self.files:
                    f["selected"] = not b
        elif ch == '<c-s>':
            self.save()
            self.change_dir()
        elif ch == '<c-y>':
            self.clipboard = self.repr_item(self.main_cursor_x, self.files[self.main_cursor_y])
        elif ch == 'e':
            if self.main_cursor_x != 7:
                ss = self.set_selected_set()
                self.edit_scroll = 0
                if self.main_cursor_x == 0:
                    self.edit_value = ["\\u", "(.*)(\.[a-z0-9]+)$", "\\(\"%02d \" % c if c else \"\")\\r\\(\" - \" if r and t else \"\")\\t\\2"]
                elif self.main_cursor_x == 1:
                    self.edit_value = ["\\l", "(.*)", "\\(d0)"]
                elif self.main_cursor_x == 2:
                    self.edit_value = ["\\u", "(.*)", "\\(\"%d/%d\"% (num, sel))"]
                elif self.main_cursor_x == 3:
                    self.edit_value = ["\\u", "(.*)[ _]-[ _](.*)(\.[a-z0-9]+)$", "\\1"]
                elif self.main_cursor_x == 4:
                    self.edit_value = ["\\u", "(.*)[ _]-[ _](.*)(\.[a-z0-9]+)$", "\\2"]
                elif self.main_cursor_x == 5:
                    self.edit_value = ["\\g", "(.*)", "\\1"]
                elif self.main_cursor_x == 6:
                    self.edit_value = ["\\e", "(.*)", "\\1"]
                if not ss:
                    self.edit_value[2] = self.repr_item(self.main_cursor_x, self.selected[0])
                self.edit_cursor_y = 2
                self.edit_cursor_x0 = [-1, -1, -1]
                self.edit_cursor_x1 = [-1, -1, -1]
                self.menu = "edit"

    def dialog_draw(self):
        title = self.dialog["title"]
        options = self.dialog["options"]
        texts = []
        for key, value in options.items():
            texts.append("(%s) %s" % (key, value[0]))
        h = len(options)+3
        w = max(len(max(texts, key=len))+25, len(title)+4)
        y = 6
        x = 10
        dialog_win = curses.newwin(h,w,y,x)
        dialog_win.addch(0,0,curses.ACS_ULCORNER, self.style_edit_ornaments)
        dialog_win.hline(0,1,curses.ACS_HLINE,w-2, self.style_edit_ornaments)
        dialog_win.addch(0,w-1,curses.ACS_URCORNER, self.style_edit_ornaments)
        dialog_win.addstr(0,int((w-len(title))/2),title, self.style_edit_help_line_val)

        dialog_win.hline(1,1,' ',w-2, self.style_edit_ornaments)
        dialog_win.hline(2,1,' ',w-2, self.style_edit_help_line_val)
        dialog_win.hline(3,1,' ',w-2, self.style_edit_help_line_val)
        dialog_win.hline(4,1,' ',w-2, self.style_edit_ornaments)

        dialog_win.vline(1,0,curses.ACS_VLINE,h-2, self.style_edit_ornaments)
        dialog_win.vline(1,w-1,curses.ACS_VLINE,h-2, self.style_edit_ornaments)
        for i in range(len(texts)):
            dialog_win.addstr(i+2,1,texts[i], self.style_edit_help_line_val)

        dialog_win.addch(h-1,0,curses.ACS_LLCORNER, self.style_edit_ornaments)
        dialog_win.hline(h-1,1,curses.ACS_HLINE,w-2, self.style_edit_ornaments)
        dialog_win.refresh()


    def dialog_handle_input(self, ch):
        options = self.dialog["options"]
        if ch in options:
            cmd = options[ch][1]
            if cmd:
                cmd(self)
            self.dialog = None

    def inc_filename(self, name):
        m = re.match("(.*\()([0-9]+)(\))$", name)
        if m:
            return m.group(1) + str(int(m.group(2))+1) + m.group(3)
        else:
            return name + "(1)"


    def perorm_regex(self):
        root = self.dirs[self.dir_cursor]
        existing_filenames = set()
        for file in os.listdir(root):
            existing_filenames.add(file)
        data = []
        i = 0
        for sel in self.selected:
            cur_val = self.repr_item(self.main_cursor_x, sel)
            error = None
            in_val, e = self.replace_backslash_stuff(self.edit_value[0], sel, i, len(self.selected))
            if e is not None: error = e
            search, e = self.replace_backslash_stuff(self.edit_value[1], sel, i, len(self.selected))
            if e is not None: error = e
            replace, e = self.replace_backslash_stuff(self.edit_value[2], sel, i, len(self.selected))
            if e is not None: error = e
            try:
                if re.match(search, in_val):
                    new_val = re.sub(search, replace, in_val, flags=re.DOTALL)
                else:
                    if error is None: error = "no match"
                    new_val = replace
            except re.error:
                try:
                    re.match(search, in_val)
                    if error is None: error = "bad subst"
                except re.error:
                    if error is None: error = "bad regex"
                new_val = replace
            if error is None: error = e
            if self.main_cursor_x == 0 and '/' in new_val:
                error = "'/' in url"
                new_val = new_val.replace("/", "")
            elif self.main_cursor_x == 0 and not new_val:
                error = "empty url"
                new_val = cur_val
            data.append((cur_val, new_val, error))
            i = i + 1
        errors = True
        num = 0
        while errors:
            errors = False
            data2 = []
            new_filenames = []
            for d in data:
                new_filenames.append(d[1])
            for d in data:
                if not errors and new_filenames.count(d[1]) > 1:
                    f = self.inc_filename(d[1])
                    data2.append((d[0], f, "duplicate filename"))
                    num += 1
                    errors = True
                elif not errors and d[0] != d[1] and d[1] in existing_filenames:
                    f = self.inc_filename(d[1])
                    data2.append((d[0], f, "existing filename"))
                    errors = True
                else:
                    data2.append(d)
            data = data2
        return data

    def get_left_right(self, y):
        if self.edit_cursor_x0[y] == -1 or self.edit_cursor_x1[y] == -1:
            return 0, len(self.edit_value[y])
        left = min(self.edit_cursor_x0[y], self.edit_cursor_x1[y])
        right = max(self.edit_cursor_x0[y], self.edit_cursor_x1[y])
        return left, right

    def edit_menu_draw(self):
        h = self.height-8
        w = self.width-10
        y = 4
        x = 5
        edit_win = curses.newwin(h,w,y,x)
        edit_win.addch(0,0,curses.ACS_ULCORNER, self.style_edit_ornaments)
        edit_win.hline(0,1,curses.ACS_HLINE,w-2, self.style_edit_ornaments)
        edit_win.addch(0,w-1,curses.ACS_URCORNER, self.style_edit_ornaments)
        edit_win.vline(1,0,curses.ACS_VLINE,h-6, self.style_edit_ornaments)
        edit_win.vline(1,w-1,curses.ACS_VLINE,h-6, self.style_edit_ornaments)
        edit_win.addch(h-5,0,curses.ACS_LTEE, self.style_edit_ornaments)
        edit_win.hline(h-5,1,curses.ACS_HLINE,w-2, self.style_edit_ornaments)
        edit_win.addch(h-5,w-1,curses.ACS_RTEE, self.style_edit_ornaments)
        edit_win.vline(h-4,0,curses.ACS_VLINE,3, self.style_edit_ornaments)
        edit_win.addstr(h-4,1,'Input:', self.style_edit_help_line_val)
        edit_win.addstr(h-3,1,'Regex:', self.style_edit_help_line_val)
        edit_win.addstr(h-2,1,'Subst:', self.style_edit_help_line_val)
        edit_win.vline(h-4,w-1,curses.ACS_VLINE,3, self.style_edit_ornaments)
        edit_win.addch(h-1,0,curses.ACS_LLCORNER, self.style_edit_ornaments)
        edit_win.hline(h-1,1,curses.ACS_HLINE,w-2, self.style_edit_ornaments)
        edit_win.addstr(0,int(w/2)-5," Edit Menu ", self.style_edit_ornaments)

        #edit_win.addch(h-1,w-1,curses.ACS_LRCORNER, self.style_edit_ornaments)

        pad_height = max(len(self.selected), h-4)+1
        edit_pad = curses.newpad(pad_height,w-2)
        data = self.perorm_regex()
        max_len_cur_val = 0
        max_len_new_val = 0
        for cur_val, new_val, error in data:
            if len(cur_val) > max_len_cur_val:
                max_len_cur_val = len(cur_val)
            if len(new_val) > max_len_new_val:
                max_len_new_val = len(new_val)

        i = 0
        for cur_val, new_val, error in data:
            edit_pad.addstr(i, 0, self.just("%s -> %s" % (self.just(cur_val, max_len_cur_val), new_val), w-2), self.style_edit_ornaments)
            if error:
                error_x_pos = max_len_cur_val + max_len_new_val + 5
                if error_x_pos > w-3-len(error):
                    error_x_pos = w-3-len(error)
                edit_pad.addstr(i, error_x_pos, error, self.style_error)
            i = i + 1
        while i < pad_height-1:
            edit_pad.addstr(i, 0, self.just("", w-2), self.style_edit_ornaments)
            i = i + 1

        irs_text_y = h-4
        irs_text_x = 7
        irs_text_w = w-8
        irs_text_scroll_offset = 5
        for z in [0, 1, 2]:
            v = self.edit_value[z] + " "
            irs_scroll = 0
            if self.edit_cursor_x1[z] == -1:
                irs_scroll = 0
            elif self.edit_cursor_x1[z] > irs_text_w-irs_text_scroll_offset:
                irs_scroll = min(self.edit_cursor_x1[z]-irs_text_w+irs_text_scroll_offset, max(0, len(v)-irs_text_w))
            else:
                irs_scroll = 0
            v = v[irs_scroll:irs_text_w+irs_scroll]
            if self.edit_cursor_y == z:
                left, right = self.get_left_right(z)
                left -= irs_scroll
                right -= irs_scroll
                edit_win.addstr(irs_text_y+z, irs_text_x, v[:left], self.style_edit_ornaments)
                edit_win.addstr(irs_text_y+z, irs_text_x+left, v[left:right+1], curses.A_REVERSE)
                edit_win.addstr(irs_text_y+z, irs_text_x+right+1, v[right+1:], self.style_edit_ornaments)
            else:
                edit_win.addstr(irs_text_y+z, irs_text_x, v, self.style_edit_ornaments)
            vacuum = w-len(v)-8
            if vacuum > 0:
                edit_win.hline(irs_text_y+z, irs_text_x+len(v), " ", vacuum, self.style_edit_ornaments)
        self.draw_help_line(self.screen, self.height-1, self.width, self.style_edit_help_line_val, {"<c-a>": "Select all", "<tab>": "Input/Search/Replace", "<c-y>":"Copy", "<c-p>":"Paste", "<esc>": "Cancel", "<cr>": "Ok"})
        help_lines = [
                "u = url",
                "l = album",
                "c = track num",
                "k = ...out of",
                "r = artist",
                "t = title",
                "g = genre name",
                "G = genre id",
                "e = release date",
                "num = selected num",
                "sel = ...out of",
                "dn = dir name n",
                "",
                "use \\u for one char",
                "use \\(foo) for expr",
                "use \\1, \\2, ...",
                "   for regex backref"]
        w_help = min(int((w-2)/2), len(max(help_lines, key=len))+0)
        h_help = min(h-2, len(help_lines))
        edit_help_win = curses.newwin(h_help,w_help,y+1,x+w-w_help-1)
        i = 0
        for i in range(h_help):
            help_line = help_lines[i]
            edit_help_win.insstr(i, 0, self.just(help_line, w_help), self.style_edit_help_line_val)
            i = i +1
        edit_win.refresh()
        edit_pad.refresh(self.edit_scroll, 0, y+1, x+1, y+h-6, x+ w-2)
        edit_help_win.refresh()

    def edit_menu_handle_input(self, ch):
        if ch == '<esc>':
            self.menu = "main"
        elif ch == '<tab>':
            self.edit_cursor_y += 1
            if self.edit_cursor_y == 3:
                self.edit_cursor_y = 0
        elif ch == '<s-tab>':
            self.edit_cursor_y -= 1
            if self.edit_cursor_y == -1:
                self.edit_cursor_y = 2
        elif ch == '<up>':
            if self.edit_scroll > 0:
                self.edit_scroll -= 1
        elif ch == '<down>':
            pass
        elif ch == '<right>':
            y = self.edit_cursor_y
            if self.edit_cursor_x0[y] == -1 or self.edit_cursor_x1[y] == -1:
                self.edit_cursor_x1[y] = len(self.edit_value[y])
            elif self.edit_cursor_x1[y] < len(self.edit_value[y]):
                self.edit_cursor_x1[y] += 1
            self.edit_cursor_x0[y] = self.edit_cursor_x1[y]
        elif ch == '<left>':
            y = self.edit_cursor_y
            if self.edit_cursor_x0[y] == -1 or self.edit_cursor_x1[y] == -1:
                self.edit_cursor_x1[y] = 0
            elif self.edit_cursor_x1[y] > 0:
                self.edit_cursor_x1[y] -= 1
            self.edit_cursor_x0[y] = self.edit_cursor_x1[y]
        elif ch == '<c-right>':
            y = self.edit_cursor_y
            if self.edit_cursor_x0[y] == -1 or self.edit_cursor_x1[y] == -1:
                self.edit_cursor_x0[y] = len(self.edit_value[y])
                self.edit_cursor_x1[y] = 1
            elif self.edit_cursor_x1[y] < len(self.edit_value[y]):
                self.edit_cursor_x1[y] += 1
        elif ch == '<c-left>':
            y = self.edit_cursor_y
            if self.edit_cursor_x0[y] == -1 or self.edit_cursor_x1[y] == -1:
                self.edit_cursor_x0[y] = 0
                self.edit_cursor_x1[y] = len(self.edit_value[y])-1
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
            self.edit_cursor_x0[y] = -1
            self.edit_cursor_x1[y] = -1
        elif ch == '<c-y>':
            y = self.edit_cursor_y
            left, right = self.get_left_right(y)
            self.clipboard = self.edit_value[y][left:right]
        elif ch == '<c-p>':
            y = self.edit_cursor_y
            left, right = self.get_left_right(y)
            self.edit_value[y] = self.edit_value[y][:left] + self.clipboard + self.edit_value[y][right:]
            self.edit_cursor_x1[y] = left + len(self.clipboard)
            self.edit_cursor_x0[y] = left + len(self.clipboard)
        elif ch == '<cr>':
            self.perform_edit()
            self.menu = "main"
        elif ch == '<bs>':
            y = self.edit_cursor_y
            left, right = self.get_left_right(y)
            if left != right or left != 0:
                if left == right:
                    left = left - 1
                self.edit_value[y] = self.edit_value[y][:left] + self.edit_value[y][right:]
                self.edit_cursor_x1[y] = left
                self.edit_cursor_x0[y] = self.edit_cursor_x1[y]
        elif ch == '<del>':
            y = self.edit_cursor_y
            left, right = self.get_left_right(y)
            if left != right or left != len(self.edit_value[y]):
                if left == right:
                    right = right + 1
                self.edit_value[y] = self.edit_value[y][:left] + self.edit_value[y][right:]
                self.edit_cursor_x1[y] = left
                self.edit_cursor_x0[y] = self.edit_cursor_x1[y]
        elif ch != None and len(ch) == 1 and ch >= ' ' and ch <= '~':
            y = self.edit_cursor_y
            left, right = self.get_left_right(y)
            self.edit_value[y] = self.edit_value[y][:left] + ch + self.edit_value[y][right:]
            self.edit_cursor_x1[y] = left + 1
            self.edit_cursor_x0[y] = left + 1


    def replace_backslash_stuff(self, s, file, e, n):
        track = self.get_item(2, file)
        d = self.dirs[self.dir_cursor]
        path = d.split('/')
        release = file["id3"].tag.release_date
        lcls = {
                "u": file["url"],
                "l": file["id3"].tag.album,
                "c": track[0] if track else None,
                "k": track[1] if track else None,
                "num": e+1,
                "sel": n,
                "r": file["id3"].tag.artist,
                "t": file["id3"].tag.title,
                "g": file["id3"].tag.genre.name,
                "G": file["id3"].tag.genre.id,
                "e": str(release) if release else None,
                "d0": path[-2] if len(path) > 1 else "na",
                "d1": path[-3] if len(path) > 2 else "na",
                "d2": path[-4] if len(path) > 3 else "na",
                "d3": path[-5] if len(path) > 4 else "na",
                "d4": path[-6] if len(path) > 5 else "na",
                }
        ret = ""
        mode = "init"
        error = None
        for c in s:
            if mode == "init":
                if c == '\\':
                    mode = "backslash"
                else:
                    ret += c
            elif mode == "backslash":
                if c in lcls:
                    res = lcls[c]
                    if res is not None:
                        ret += str(res)
                    mode = "init"
                elif c == '(':
                    mode = "paran"
                    expr = ""
                    paran = 0
                elif c == '0':
                    mode = "init"
                else:
                    ret += "\\"
                    ret += c
                    mode = "init"
            elif mode == "paran":
                if c == ')':
                    if paran == 0:
                        try:
                            st = parser.expr(expr)
                            code = st.compile('file.py')
                            res = eval(code, {}, lcls)
                            if res is not None:
                                ret += str(res)
                        except Exception as e:
                            error = str(e)
                        mode = "init"
                    else:
                        expr += c
                        paran -= 1
                elif c == '(':
                    expr += c
                    paran += 1
                else:
                    expr += c
        return ret, error

    def perform_edit(self):
        data = self.perorm_regex()
        i = 0
        for sel in self.selected:
            cur_val, new_val, error =  data[i]
            if not new_val is None:
                self.set_item(self.main_cursor_x, sel, new_val)
            i = i + 1


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('mp3s', nargs='+')
    args = argparser.parse_args()
    id3edit = Id3Edit(args.mp3s)
    s = signal.signal(signal.SIGINT, signal.SIG_IGN)
    curses.wrapper(id3edit.main)
    s = signal.signal(signal.SIGINT, signal.SIG_IGN)
