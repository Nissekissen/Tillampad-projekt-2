# Description: This file contains the ChatInterface class which is used to
# display the chat client in a curses window.

import locale

locale.setlocale(locale.LC_ALL, '')

import curses

class ChatInterface:
    def __init__(self, username) -> None:
        self.stdscr: curses.window = curses.initscr()

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, -1, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_CYAN, -1)

        self.username = username
        curses.noecho()

    def get_input(self, string: str) -> str:
        'gets input from user'
        self.stdscr.addstr(string)
        self.stdscr.refresh()
        curses.echo()
        input = self.stdscr.getstr().decode('utf-8')
        curses.noecho()
        return input
    
    def write_message(self, string: str, *attr) -> None:
        'writes a message to the chat interface'
        row, col = self.stdscr.getyx()
        self.stdscr.move(row, 0)
        self.stdscr.clrtoeol()
        done = False
        while not done:
            try:
                self.stdscr.addstr(f"{string}\n", *attr)
                self.stdscr.addstr("> ")
                done = True
            except:
                self.stdscr.scrollok(True)
                self.stdscr.scroll()
                pass
        self.stdscr.refresh()
    
    def write_message_no_prompt(self, string: str, *attr) -> None:
        'writes a message to the chat interface without a prompt'
        row, col = self.stdscr.getyx()
        self.stdscr.move(row, 0)
        self.stdscr.clrtoeol()
        done = False
        while not done:
            try:
                self.stdscr.addstr(f"{string}\n", *attr)
                done = True
            except:
                self.stdscr.scrollok(True)
                self.stdscr.scroll()
                pass
        self.stdscr.refresh()
    
    def clear(self) -> None:
        'clears the chat interface'
        self.stdscr.clear()
    
    def clear_last_line(self) -> None:
        'clears the last line of the chat interface'
        row, col = self.stdscr.getyx()
        try:
            self.stdscr.move(row - 1, 0)
            self.stdscr.clrtoeol()
        except:
            # best error handling
            pass

    def loop(self) -> str:
        'loops the chat interface'
        self.stdscr.refresh()
        row, col = self.stdscr.getyx()
        self.stdscr.addstr(row, 0, "> ", curses.color_pair(1))

        message = ''

        while True:
            row, col = self.stdscr.getyx()
            self.stdscr.addstr(row, 0, "> " + message)
            key = self.stdscr.getkey()

            if key == "\x00":
                continue
            if key == "KEY_ENTER" or key == "\n":
                if len(message) == 0:
                    continue
                break
            elif key == "KEY_BACKSPACE" or key == "\b":
                self.stdscr.addstr("\b \b")
                message = message[:-1]
            elif key == '\x7f':
                for _ in range(len(message)):
                    self.stdscr.addstr("\b \b")
                message = ''
                self.stdscr.addstr(row, 0, "> ", curses.color_pair(1))
            else:
                self.stdscr.addstr(key)
                message += key
            

        self.stdscr.refresh()
        self.stdscr.move(row, 0)
        self.stdscr.clrtoeol()
        done = False
        while not done:
            try:
                self.stdscr.addstr(f"{self.username}: {message}\n", curses.color_pair(3))
                done = True
            except:
                self.stdscr.scrollok(True)
                self.stdscr.scroll()
                pass

        return message

        