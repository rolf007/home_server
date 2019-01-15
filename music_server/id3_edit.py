#!/usr/bin/env python3

import argparse
import curses
import eyed3
import os
import re
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('mp3s', nargs='+')#, action=MyAction)
args = parser.parse_args()

screen = curses.initscr()
main_cursor_x = 0
main_cursor_y = 0
fix_cursor_x = 0
num_columns = 7
screen_end = 0
files = []
menu = "main"

def repr_item(s):
    if type(s) is tuple:
        if s[0] and s[1]:
            s = "%d/%d" % (s[0],s[1])
        else:
            s = '/'
    elif type(s) is eyed3.id3.Genre:
        s = s.name
    elif s is None:
        s = "<None>"
    return s;

def just(s, adj):
    s = repr_item(s)
    return s.ljust(adj)[:adj]

def get_color(x, y):
    if main_cursor_y == y or main_cursor_x == x:
        if files[y]["selected"]:
            color = curses.color_pair(3)|curses.A_BOLD
        else:
            color = curses.color_pair(1)
    else:
        if files[y]["selected"]:
            color = curses.color_pair(4)|curses.A_BOLD
        else:
            color = curses.color_pair(2)
    return color

def get_item(x, i):
    file = files[i]
    url = file["url"]
    album = file["id3"].tag.album
    track_num = file["id3"].tag.track_num
    artist = file["id3"].tag.artist
    title = file["id3"].tag.title
    genre = file["id3"].tag.genre
    release_date = file["id3"].tag.release_date
    columns = [url, album, track_num, artist, title, genre, release_date]
    return columns[x]

def set_item(x, i, value):
    file = files[i]
    if x == 0:
        pass
    elif x == 1:
        file["id3"].tag.album = value
    elif x == 2:
        file["id3"].tag.track_num = value
    elif x == 3:
        file["id3"].tag.artist = value
    elif x == 4:
        file["id3"].tag.title = value
    elif x == 5:
        file["id3"].tag.genre = value
    elif x == 6:
        file["id3"].tag.release_date = value


for url in args.mp3s:
    # if not os.path.isabs(scan_path):
    #     print("path must be absolute!")
    #     exit(1)
    if not os.path.exists(url):
        print("path '%s' does not exist!" % url)
        exit(1)
    audiofile = eyed3.load(url)
    if audiofile and audiofile.tag:
        files.append({"id3": audiofile, "selected": False, "url": url})

curses.start_color()
curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN);
curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE);
curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_CYAN);
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLUE);

def column_addstr(y, x, s, c, color):
    adj = [30,20,3,10,20,12,8]
    for i in range(c):
        x += adj[i]+1
    screen.addstr(y, x, "%s " % just(s, adj[c]), color)

def draw():
    screen.clear()
    y = 4
    color = curses.color_pair(1)
    column_addstr(y, 2, "Url", 0, color)
    column_addstr(y, 2, "A(l)bum", 1, color)
    column_addstr(y, 2, "Track_num", 2, color)
    column_addstr(y, 2, "A(r)tist", 3, color)
    column_addstr(y, 2, "(t)itle", 4, color)
    column_addstr(y, 2, "(G)enre", 5, color)
    column_addstr(y, 2, "R(e)lease date", 6, color)
    y = y + 1
    i = 0
    for file in files:
        for col in range(num_columns):
            column_addstr(y, 2, get_item(col, i), col, get_color(col, i))
        i = i + 1
        y = y + 1
    screen.addstr(y, 2, just(get_item(main_cursor_x, main_cursor_y), 120), curses.A_BOLD)
    y = y + 1
    y = y + 1
    if menu == "main":
        screen.addstr(y, 2, "<space>: toggle select a:select all/none", curses.A_BOLD)
        y = y + 1
        screen.addstr(y, 2, "<up>/<down>/<left>/<right>: cursor", curses.A_BOLD)
        y = y + 1
        screen.addstr(y, 2, "q: quit f:fix id3 for selected column", curses.A_BOLD)
        y = y + 1
        screen.addstr(y, 2, "Please select an option...", curses.A_BOLD)
    return y+1

def suggest_algo_fs(i):
    file = files[i]
    suggestion = "xx"
    if fix_cursor_x >= 0:
        filename_items = re.split("[ _]-[ _]", file["url"])
        if fix_cursor_x < len(filename_items):
            suggestion = filename_items[fix_cursor_x]
        else:
            suggestion = filename_items[-1]
    else:
        path = str(os.getcwd()).split('/')
        if -fix_cursor_x < len(path):
            suggestion = path[fix_cursor_x]
        else:
            suggestion = "foo"
    return suggestion

def suggest_algo_from_id3(i):
    file = files[i]
    artist = get_item(3, i)
    title = get_item(4, i)
    filename, ext = os.path.splitext(file["url"])
    track = get_item(2, i)
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

def suggest_algo_track_number(i, n):
    return (i+1,n)

def suggest_algo_genre():
    return eyed3.id3.Genre('Thrash Metal')

def get_suggestion(main_cursor_x, i, j, num_selected):
    if main_cursor_x == 0:
        return suggest_algo_from_id3(i)
    elif main_cursor_x == 1 or main_cursor_x == 3 or main_cursor_x == 4:
        return suggest_algo_fs(i)
    elif main_cursor_x == 2:
        return suggest_algo_track_number(j, num_selected)
    elif main_cursor_x == 5:
        return suggest_algo_genre()
    return "bar"

def draw_fix_menu():
    if menu == "fix":
        y = screen_end
        num_selected = 0
        for file in files:
            if file["selected"]:
                num_selected += 1
        i = 0
        j = 0
        for file in files:
            if file["selected"]:
                current = get_item(main_cursor_x, i)
                suggestion = get_suggestion(main_cursor_x, i, j, num_selected)

                screen.addstr(y, 2, "'%s' -> '%s'" % (repr_item(current), repr_item(suggestion)), curses.A_BOLD)
                y = y + 1
                j = j + 1
            i = i + 1

def perform_fix():
    num_selected = 0
    for file in files:
        if file["selected"]:
            num_selected += 1
    i = 0
    j = 0
    for file in files:
        if file["selected"]:
            suggestion = get_suggestion(main_cursor_x, i, j, num_selected)
            set_item(main_cursor_x, i, suggestion)
            j = j + 1
        i = i + 1

arrow_state = 0
c = None
while True:
    screen_end = draw()
    draw_fix_menu()
    if c:
        screen.addstr(0, 0, str(c), curses.A_BOLD)
    c = screen.getch()
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

    if menu == "main":
        if ch == 'q':
            break
        elif ch == '<up>':
            if main_cursor_y > 0:
                main_cursor_y -= 1
        elif ch == '<down>':
            if main_cursor_y < len(files)-1:
                main_cursor_y += 1
        elif ch == '<right>':
            if main_cursor_x < num_columns - 1:
                main_cursor_x += 1
        elif ch == '<left>':
            if main_cursor_x > 0:
                main_cursor_x -= 1
        elif ch == ' ':
            files[main_cursor_y]["selected"] = not files[main_cursor_y]["selected"]
        elif ch == 'a':
            b = files[0]["selected"]
            for f in files:
                f["selected"] = not b
        elif ch == 'f':
            menu = "fix"
            any_selected = False
            for f in files:
                if f["selected"]:
                    any_selected = True
            if not any_selected:
                files[main_cursor_y]["selected"] = not files[main_cursor_y]["selected"]
    elif menu == "fix":
        if ch == 'q':
            menu = "main"
        elif ch == '<right>':
            fix_cursor_x += 1
        elif ch == '<left>':
            fix_cursor_x -= 1
        elif ch == '<cr>':
            perform_fix()
            menu = "main"
curses.endwin()
