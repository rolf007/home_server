#!/usr/bin/env python3


import argparse
import curses
import curses.textpad
import eyed3
import os
import re
from operator import itemgetter

import locale

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

        self.screen = curses.initscr()
        self.screen.refresh()
        self.height, self.width = self.screen.getmaxyx()
        # don't echo key strokes on the screen
        curses.noecho()
        # read keystrokes instantly, without waiting for enter to ne pressed
        curses.cbreak()
        # enable keypad mode
        #self.screen.keypad(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN);
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE);
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_CYAN);
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLUE);
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE);
        curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_WHITE);

        self.dir_cursor = 0
        self.dirs = []
        self.debug = ""



        directory = args.mp3s[0]
        for root, dirs, fils in os.walk(directory):
            if len(fils) > 0:
                self.dirs.append(root)

        self.change_dir()

        arrow_state = 0
        c = None
        while True:
            self.screen_end = self.draw()
            if self.menu == "fix":
                self.draw_fix_menu()
            if self.menu == "edit":
                self.draw_edit_menu()
            if c:
                self.screen.addstr(0, 0, "%s %s" % (str(c), self.debug), curses.A_BOLD)
            c = self.screen.getch()
            ch = None
            if arrow_state == 0:
                if c == 0x1b:
                    arrow_state = 1
                elif c == 0x0a:
                    ch = '<cr>'
                elif c == 0x7f:
                    ch = '<bs>'
                elif c == 0x01:
                    ch = '<c-a>'
                else:
                    ch = chr(c)
            elif arrow_state == 1:
                arrow_state = 0
                if c == 0x1b:
                    ch = '<esc>'
                if c == 0x5b:
                    arrow_state = 2
            elif arrow_state == 2:
                arrow_state = 0
                if c == 0x41:
                    ch = '<up>'
                elif c == 0x42:
                    ch = '<down>'
                elif c == 0x43:
                    ch = '<right>'
                elif c == 0x44:
                    ch = '<left>'
                elif c == 0x31:
                    arrow_state = 3
                elif c == 0x46:
                    ch = '<end>'
                elif c == 0x48:
                    ch = '<home>'
            elif arrow_state == 3:
                arrow_state = 0
                if c == 0x3b:
                    arrow_state = 4
            elif arrow_state == 4:
                arrow_state = 0
                if c == 0x32:
                    arrow_state = 5
                if c == 0x35:
                    arrow_state = 6
            elif arrow_state == 5:
                arrow_state = 0
                if c == 0x41:
                    ch = '<s-up>'
                elif c == 0x42:
                    ch = '<s-down>'
                elif c == 0x43:
                    ch = '<s-right>'
                elif c == 0x44:
                    ch = '<s-left>'
            elif arrow_state == 6:
                arrow_state = 0
                if c == 0x41:
                    ch = '<c-up>'
                elif c == 0x42:
                    ch = '<c-down>'
                elif c == 0x43:
                    ch = '<c-right>'
                elif c == 0x44:
                    ch = '<c-left>'

            if self.menu == "main":
                if ch == 'q':
                    break
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
                elif ch == 'a':
                    b = self.files[0]["selected"]
                    for f in self.files:
                        f["selected"] = not b
                elif ch == 'f':
                    if self.main_cursor_x != 5 and self.main_cursor_x != 6 and self.main_cursor_x != 7:
                        self.set_selected_set()
                        self.menu = "fix"
                elif ch == 'e':
                    if self.main_cursor_x != 7:
                        self.set_selected_set()
                        self.edit_value = ["(.*)", self.repr_item(self.main_cursor_x, self.selected[0])]
                        self.edit_cursor_y = 1
                        self.edit_cursor_x0 = [0, 0]
                        self.edit_cursor_x1 = [len(self.edit_value[0]), len(self.edit_value[1])]
                        self.menu = "edit"
            elif self.menu == "fix":
                if ch == '<esc>':
                    self.menu = "main"
                elif ch == '<right>':
                    self.fix_cursor_x += 1
                elif ch == '<left>':
                    self.fix_cursor_x -= 1
                elif ch == '<cr>':
                    self.perform_fix()
                    self.menu = "main"
            elif self.menu == "edit":
                if ch == '<esc>':
                    self.menu = "main"
                elif ch == '<up>':
                    if self.edit_cursor_y == 1:
                        self.edit_cursor_y = 0
                elif ch == '<down>':
                    if self.edit_cursor_y == 0:
                        self.edit_cursor_y = 1
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
                elif ch == '<s-right>':
                    y = self.edit_cursor_y
                    if self.edit_cursor_x1[y] < len(self.edit_value[y]):
                        self.edit_cursor_x1[y] += 1
                elif ch == '<s-left>':
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
        curses.endwin()

    def change_dir(self):
        self.main_scroll = 0
        self.main_scroll_offset = 2
        self.main_max_rows = 8
        self.main_cursor_x = 0
        self.main_cursor_y = 0
        self.fix_cursor_x = 0
        self.num_columns = 8
        self.screen_end = 0
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
                if self.files[y]["selected"]:
                    color = curses.color_pair(6)|curses.A_BOLD
                else:
                    color = curses.color_pair(5)
            else:
                if self.files[y]["selected"]:
                    color = curses.color_pair(3)|curses.A_BOLD
                else:
                    color = curses.color_pair(1)
        else:
            if self.files[y]["selected"]:
                color = curses.color_pair(4)|curses.A_BOLD
            else:
                color = curses.color_pair(2)
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

    def column_addstr(self, y, x, foo, s, c, color):
        adj = [30,20,4,10,20,12,8,5]
        for i in range(c):
            x += adj[i]+1
        foo.addstr(y, x, (u"%s\u2502" % self.just(s, adj[c])).encode('utf-8'), color)

    def draw(self):
        self.screen.clear()
        self.screen.refresh()
        y = 1
        self.screen.addstr(y, 2, self.just(self.dirs[self.dir_cursor], 120), curses.A_BOLD)
        y = y + 1
        color = curses.color_pair(1)
        for column in range(self.num_columns):
            self.column_addstr(y, 2, self.screen, self.get_column_name(column), column, color)
        y = y + 1
        i = 0


        self.pad = curses.newpad(15, 200)
        for file in self.files:
            for column in range(self.num_columns):
                self.column_addstr(i+1, 0, self.pad, self.repr_item(column, file), column, self.get_color(column, i))
            i = i + 1
            y = y + 1
        self.pad.refresh(self.main_scroll, 0, 2, 2, 10, 118)

        if len(self.files):
            cur_file = self.files[self.main_cursor_y]
            self.screen.addstr(y, 2, self.just(self.repr_item(self.main_cursor_x, cur_file), 120), curses.A_BOLD)
        y = y + 1
        y = y + 1
        if self.menu == "main":
            self.screen.addstr(y, 2, "<space>: toggle select", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "a:select all/none", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "<up>/<down>/<left>/<right>: cursor", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "f: fix id3 for selected column", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "e: edit id3 for selected column", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "n/p: next/previous dir", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "q: quit", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "Please select an option...", curses.A_BOLD)
        return y+1

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

    def draw_edit_menu(self):
        y = 5
        x = 7
        for file in self.selected[0:self.main_max_rows]:
            current = self.repr_item(self.main_cursor_x, file)
            try:
                suggestion = re.sub(self.edit_value[0], self.edit_value[1], current, flags=re.DOTALL)
            except re.error:
                suggestion = "<bad regex>"

            self.screen.addstr(y, x, "'%s' -> '%s'" % (current, suggestion), curses.A_BOLD)
            y = y + 1
        y = y + 1
        for z in [0, 1]:
            v = self.edit_value[z] + " "
            if self.edit_cursor_y == z:
                left = min(self.edit_cursor_x0[z], self.edit_cursor_x1[z])
                right = max(self.edit_cursor_x0[z], self.edit_cursor_x1[z])+1
                self.screen.addstr(y+z, x, v[:left], curses.A_BOLD)
                self.screen.addstr(y+z, x+left, v[left:right], curses.A_REVERSE)
                self.screen.addstr(y+z, x+right, v[right:], curses.A_BOLD)
            else:
                self.screen.addstr(y+z, x, v, curses.A_BOLD)

    def draw_fix_menu(self):
        y = 5
        x = 7
        num_selected = len(self.selected)
        j = 0
        for file in self.selected[0:self.main_max_rows]:
            current = self.repr_item(self.main_cursor_x, file)
            suggestion = self.get_suggestion(file, j, num_selected)

            self.screen.addstr(y, x, "'%s' -> '%s'" % (current, suggestion), curses.A_BOLD)
            y = y + 1
            j = j + 1

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

