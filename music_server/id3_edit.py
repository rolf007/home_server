#!/usr/bin/env python3

import argparse
import curses
import curses.textpad
import eyed3
import os
import re

class Id3Edit:
    def __init__(self, mp3s):

        self.screen = curses.initscr()
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

        self.main_cursor_x = 0
        self.main_cursor_y = 0
        self.fix_cursor_x = 0
        self.num_columns = 7
        self.screen_end = 0
        self.files = []
        self.menu = "main"
        self.selected = []

        if len(args.mp3s) == 1 and os.path.isdir(args.mp3s[0]):
            directory = args.mp3s[0]
            print ("walk mode")
            for root, dirs, fils in os.walk(directory):
                for file in fils:
                    url = os.path.join(root, file)
                    audiofile = eyed3.load(url)
                    if audiofile and audiofile.tag:
                        self.files.append({"id3": audiofile, "selected": False, "url": url})
                break
        else:
            for url in args.mp3s:
                # if not os.path.isabs(scan_path):
                #     print("path must be absolute!")
                #     exit(1)
                if not os.path.exists(url):
                    print("path '%s' does not exist!" % url)
                    exit(1)
                audiofile = eyed3.load(url)
                if audiofile and audiofile.tag:
                    self.files.append({"id3": audiofile, "selected": False, "url": url})


        arrow_state = 0
        c = None
        while True:
            self.screen_end = self.draw()
            self.draw_fix_menu()
            if c:
                self.screen.addstr(0, 0, str(c), curses.A_BOLD)
            c = self.screen.getch()
            ch = None
            if arrow_state == 0:
                if c == 0x1b:
                    arrow_state = 1
                elif c == 0x0a:
                    ch = '<cr>'
                else:
                    ch = chr(c)
            elif arrow_state == 1:
                if c == 0x5b:
                    arrow_state = 2
                else:
                    arrow_state = 0
            elif arrow_state == 2:
                if c == 0x41:
                    ch = '<up>'
                elif c == 0x42:
                    ch = '<down>'
                elif c == 0x43:
                    ch = '<right>'
                elif c == 0x44:
                    ch = '<left>'
                arrow_state = 0

            if self.menu == "main":
                if ch == 'q':
                    break
                elif ch == '<up>':
                    if self.main_cursor_y > 0:
                        self.main_cursor_y -= 1
                elif ch == '<down>':
                    if self.main_cursor_y < len(self.files)-1:
                        self.main_cursor_y += 1
                elif ch == '<right>':
                    if self.main_cursor_x < self.num_columns - 1:
                        self.main_cursor_x += 1
                elif ch == '<left>':
                    if self.main_cursor_x > 0:
                        self.main_cursor_x -= 1
                elif ch == ' ':
                    self.files[self.main_cursor_y]["selected"] = not self.files[self.main_cursor_y]["selected"]
                elif ch == 'a':
                    b = self.files[0]["selected"]
                    for f in self.files:
                        f["selected"] = not b
                elif ch == 'f':
                    if self.main_cursor_x != 5 and self.main_cursor_x != 6:
                        self.select_cursor_line_if_none_selected()
                        self.selected = []
                        for f in self.files:
                            if f["selected"]:
                                self.selected.append(f)
                        if len(self.selected) == 0:
                            self.selected = [self.files[self.main_cursor_y]]
                        self.menu = "fix"
                if ch == 'e':
                    self.select_cursor_line_if_none_selected()
                    value = self.repr_item(self.get_item2(self.main_cursor_x, self.get_first_selected()))
                    text = self.maketextbox(1, 40, self.screen_end+1, 2, "enter %s. Use ^H for backspace, ^A^K to delete line, ^A^K^G to cancel" % self.get_column_name(self.main_cursor_x), value, textColorpair=curses.color_pair(0))
                    if text != "":
                        self.perform_edit(text)
            elif self.menu == "fix":
                if ch == 'q':
                    self.menu = "main"
                elif ch == '<right>':
                    self.fix_cursor_x += 1
                elif ch == '<left>':
                    self.fix_cursor_x -= 1
                elif ch == '<cr>':
                    self.perform_fix()
                    self.menu = "main"
        curses.endwin()

    def maketextbox(self, h,w,y,x,info="",value="",textColorpair=0):
    #Control-A 	Go to left edge of window.
    #Control-B 	Cursor left, wrapping to previous line if appropriate.
    #Control-D 	Delete character under cursor.
    #Control-E 	Go to right edge (stripspaces off) or end of line (stripspaces on).
    #Control-F 	Cursor right, wrapping to next line when appropriate.
    #Control-G 	Terminate, returning the window contents.
    #Control-H 	Delete character backward.
    #Control-J 	Terminate if the window is 1 line, otherwise insert newline.
    #Control-K 	If line is blank, delete it, otherwise clear to end of line.
    #Control-L 	Refresh screen.
    #Control-N 	Cursor down; move down one line.
    #Control-O 	Insert a blank line at cursor location.
    #Control-P 	Cursor up; move up one line.
        nw = curses.newwin(h,w,y,x)
        txtbox = curses.textpad.Textbox(nw, insert_mode=True)

        self.screen.addstr(y-1,x,info,textColorpair)
        nw.addstr(0,0,value,textColorpair)
        nw.attron(textColorpair)
        self.screen.refresh()
        text = txtbox.edit()
        if len(text) > 0 and text[-1] == ' ':
            text = text[:-1]
        return text

    def repr_item(self, s):
        if type(s) is tuple:
            if s[0] and s[1]:
                s = "%d/%d" % (s[0],s[1])
            else:
                s = '/'
        elif type(s) is eyed3.id3.Genre:
            if s.id != None:
                s = "(%d)%s" % (s.id, s.name)
            else:
                s = "()%s" % s.name
        elif type(s) is eyed3.core.Date:
            s = str(s)
        elif s is None:
            s = "<None>"
        return s;

    def just(self, s, adj):
        s = self.repr_item(s)
        return s.ljust(adj)[:adj]

    def get_column_name(self, x):
        column_names = ["Url", "Album", "Track_num", "Artist", "Title", "Genre", "Release date"]
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

    def get_item(self, x, i):
        return self.get_item2(x, self.files[i])

    def get_item2(self, x, file):
        url = file["url"]
        album = file["id3"].tag.album
        track_num = file["id3"].tag.track_num
        artist = file["id3"].tag.artist
        title = file["id3"].tag.title
        genre = file["id3"].tag.genre
        release_date = file["id3"].tag.release_date
        columns = [url, album, track_num, artist, title, genre, release_date]
        return columns[x]

    def set_item(self, x, i, value):
        self.set_item2(x, self.files[i], value)

    def set_item2(self, x, file, value):
        try:
            if x == 0:
                pass
            elif x == 1:
                file["id3"].tag.album = value
            elif x == 2:
                file["id3"].tag.track_num = tuple([int(x) for x in value.split('/')])
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

    def select_cursor_line_if_none_selected(self):
        any_selected = False
        for f in self.files:
            if f["selected"]:
                any_selected = True
        if not any_selected:
            self.files[self.main_cursor_y]["selected"] = not self.files[self.main_cursor_y]["selected"]

    def get_first_selected(self):
        for f in self.files:
            if f["selected"]:
                return f
        return None

    def column_addstr(self, y, x, s, c, color):
        adj = [30,20,3,10,20,12,8]
        for i in range(c):
            x += adj[i]+1
        self.screen.addstr(y, x, "%s " % self.just(s, adj[c]), color)

    def draw(self):
        self.screen.clear()
        y = 4
        color = curses.color_pair(1)
        for column in range(self.num_columns):
            self.column_addstr(y, 2, self.get_column_name(column), column, color)
        y = y + 1
        i = 0
        for file in self.files:
            for column in range(self.num_columns):
                self.column_addstr(y, 2, self.repr_item(self.get_item(column, i)), column, self.get_color(column, i))
            i = i + 1
            y = y + 1
        self.screen.addstr(y, 2, self.just(self.repr_item(self.get_item(self.main_cursor_x, self.main_cursor_y)), 120), curses.A_BOLD)
        y = y + 1
        y = y + 1
        if self.menu == "main":
            self.screen.addstr(y, 2, "<space>: toggle select", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "a:select all/none", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "<up>/<down>/<left>/<right>: cursor", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "q: quit", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "f: fix id3 for selected column", curses.A_BOLD)
            y = y + 1
            self.screen.addstr(y, 2, "e: edit id3 for selected column", curses.A_BOLD)
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
        artist = self.get_item2(3, file)
        title = self.get_item2(4, file)
        filename, ext = os.path.splitext(file["url"])
        track = self.get_item2(2, file)
        if track: track = track[0]
        ret = ""
        if track:
            ret += str(track)
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
        return (i+1,n)

    def get_suggestion(self, file, j, num_selected):
        if self.main_cursor_x == 0:
            return self.suggest_algo_from_id3(file)
        elif self.main_cursor_x == 1 or self.main_cursor_x == 3 or self.main_cursor_x == 4:
            return self.suggest_algo_fs(file)
        elif self.main_cursor_x == 2:
            return self.suggest_algo_track_number(j, num_selected)
        return None

    def draw_fix_menu(self):
        if self.menu == "fix":
            y = self.screen_end
            num_selected = len(self.selected)
            j = 0
            for file in self.selected:
                current = self.get_item2(self.main_cursor_x, file)
                suggestion = self.get_suggestion(file, j, num_selected)

                self.screen.addstr(y, 2, "'%s' -> '%s'" % (self.repr_item(current), self.repr_item(suggestion)), curses.A_BOLD)
                y = y + 1
                j = j + 1

    def perform_fix(self):
        num_selected = len(self.selected)
        j = 0
        for file in self.selected:
            suggestion = self.get_suggestion(file, j, num_selected)
            self.set_item2(self.main_cursor_x, file, suggestion)
            j = j + 1

    def perform_edit(self, new_value):
        i = 0
        for file in self.files:
            if file["selected"]:
                self.set_item(self.main_cursor_x, i, new_value)
            i = i + 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mp3s', nargs='+')
    args = parser.parse_args()
    id3edit = Id3Edit(args.mp3s)

