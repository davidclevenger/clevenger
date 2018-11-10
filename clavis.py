#!/usr/bin/python

import os
import sys
import re
import getpass

try:
    import pyaes
except:
    raise ImportError("Please install \'pyaes\' to use Clavis. \n(pip install pyaes)")


class clavis:
    def __init__(self):
        key = str(getpass.getpass())

        if len(key) > 16:
            key = key[:15]
        elif len(key) < 16:
            key += (16 - len(key)) * "x"

        self.key = key
        self.aes = pyaes.AESModeOfOperationCTR(bytes(self.key.encode("utf-8")))
        self.opts = {
            "ignore_files": ["clavis.py", ".clavrc"],  # files to ignore
            "ignore_dirs": [".git"],  # directories to ignore
            "mode": None  # mode of operation
        }

    def build_file_ignore_list(self):
        expr = re.compile('(ignore_files)\s*=\s*(.?\w+\.?\w*)(\s*,\s*(.?\w+\.?\w*))*')
        lines = None
        if os.path.exists("./.clavrc"):  # resource file
            with open("./.clavrc") as f:
                lines = f.readlines()

        for line in lines:
            res = expr.match(line)
            if res is None:
                continue

            for m in res.groups():
                if m == "ignore_files":
                    continue

                # ignore empty matches
                if m is None:
                    continue

                # ignore matches with commas
                if ',' in m:
                    continue

                self.opts["ignore_files"].append(m)

    def build_dir_ignore_list(self):
        expr = re.compile('(ignore_dirs)\s*=\s*(.?\w+\.?\w*)(\s*,\s*(.?\w+\.?\w*))*')
        lines = None
        if os.path.exists("./.clavrc"):  # resource file
            with open("./.clavrc") as f:
                lines = f.readlines()

        for line in lines:
            res = expr.match(line)
            if res is None:
                continue

            for m in res.groups():
                if m == "ignore_dirs":
                    continue

                # ignore empty matches
                if m is None:
                    continue

                # ignore matches with commas
                if ',' in m:
                    continue

                self.opts["ignore_dirs"].append(m)

    def __encrypt_file(self, fname):
        contents = None
        with open(fname, "r") as f:
            contents = f.read()
            contents += (16 - (len(contents) % 16)) * '\n'
            contents = contents.encode("utf-8")

        with open(fname, "wb") as f:
            encrypted = self.aes.encrypt(contents)
            f.write(encrypted)

    def __decrypt_file(self, fname):
        contents = None
        with open(fname, "rb") as f:
            contents = f.read()

        with open(fname, "w") as f:
            decrypted = self.aes.decrypt(contents)
            decrypted = self.__remove_trailing_nl(decrypted.decode("utf-8"))
            f.write(decrypted)

    def __recursive_encrypt(self):
        for root, dirs, files in os.walk('.'):
            skip = False
            for ign_dir in self.opts["ignore_dirs"]:
                if ign_dir in root:
                    skip = True

            if skip:
                continue

            for f in files:
                if f not in self.opts["ignore_files"]:
                    self.__encrypt_file(f)

    def __recursive_decrypt(self):
        for root, dirs, files in os.walk('.'):
            skip = False
            for ign_dir in self.opts["ignore_dirs"]:
                if ign_dir in root:
                    skip = True

            if skip:
                continue

            for f in files:
                if f not in self.opts["ignore_files"]:
                    self.__decrypt_file(f)

    @staticmethod
    def __remove_trailing_nl(string):
        while len(string) > 1:
            hit = False
            if string[-2] == '\n':
                string = string[:len(string) - 1]
                hit = True
            if not hit:
                break

        return string

    def run(self):
        if len(sys.argv) != 2:
            print("Usage: python clavis.py (-e|-d)")
            return 1

        if sys.argv[1] != '-e' and sys.argv[1] != '-d':
            print("Invalid mode flag: {}\n Please use \'-e\' or \'-d\'".format(sys.argv[1]))
            return 1

        self.opts["mode"] = sys.argv[1]
        self.build_file_ignore_list()
        self.build_dir_ignore_list()

        if sys.argv[1] == '-e':
            self.__recursive_encrypt()
        elif sys.argv[1] == '-d':
            self.__recursive_decrypt()

        return 0


def main():
    cl = clavis()
    cl.run()


if __name__ == "__main__":
    sys.exit(main())
