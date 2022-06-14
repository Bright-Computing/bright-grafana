#!/cm/local/apps/python3/bin/python3
#
# Show the current settings, for advanced and global config
#    ./cm-manipulate-advanced-config.py -s
#    ./cm-manipulate-advanced-config.py -s -g
#
# Add/update two fields to advanced config but do not save (dry-run)
#    ./cm-manipulate-advanced-config.py -d Hello=World It=Works
#
# Remove the fields witht the given keys
#    ./cm-manipulate-advanced-config.py -r Hello It
#


import os
import sys

from socket import gethostname
from argparse import ArgumentParser, REMAINDER


class Config:
    def __init__(self,
                 name: str,
                 prefix: str,
                 filename: str = '/cm/local/apps/cmd/etc/cmd.conf'):
        self.name = name
        self.prefix = prefix
        self.filename = filename
        self.data = None
        self.pre = None
        self.post = None
        self.changed = False
        self.fields = []
        self._read()
        self._parse()

    @property
    def path(self):
        return f'{self.prefix}{self.filename}'

    def _read(self):
        with open(self.path, 'r') as fd:
            self.data = fd.read()

    def _parse(self):
        index = 0
        while True:
            index = self.data.find(self.name, index)
            if index < 0:
                self.pre = self.data + '\n' + self.name + ' = {\n'
                self.post = '}'
                return
            newline = self.data.rfind('\n', 0, index)
            comment = self.data.rfind('#', 0, index)
            if comment < newline:
                break
            index += len(self.name)
        index += len(self.name)
        while index < len(self.data):
            if self.data[index] == '{':
                break
            index += 1
        index += 1
        self.pre = self.data[0:index]
        if self.pre[-1] != '\n':
            self.pre += '\n'
        quote = False
        slash = 0
        start = 0
        while index < len(self.data):
            if self.data[index] == '"':
                if slash % 2 == 0:
                    if quote:
                        self.fields.append(self.data[start:index])
                    else:
                        start = index + 1
                    quote = not quote
                slash = 0
            elif self.data[index] == '\\':
                slash += 1
            elif self.data[index] == '}':
                if slash % 2 == 0 and not quote:
                    break
                slash = 0
            else:
                slash = 0
            index += 1
        self.post = self.data[index:]

    def write(self):
        with open(self.path, 'w') as fd:
            fd.write(str(self))

    def __str__(self):
        result = self.pre
        size = len(self.name) + 5
        for field in self.fields:
            result += f'{" "*size}"{field}",\n'
        size -= 2
        result += f'{" "*size}'
        result += self.post
        return result

    def remove(self, fields):  # fields: list[str]):
        old = self.fields
        self.fields = [it for it in self.fields
                       if not any(it.startswith(jt + '=') for jt in fields)]
        self.changed = old != self.fields

    def update(self, fields):  # fields: list[str]):
        for it in fields:
            index = it.find('=')
            if index > 0:
                name = it[0:index+1]
                found = False
                for index, jt in enumerate(self.fields):
                    if jt.startswith(name):
                        if self.fields[index] != it:
                            self.fields[index] = it
                            self.changed = True
                        found = True
                        break
                if not found:
                    self.fields.append(it)
                    self.changed = True
            else:
                print(f'Invalid: {it}')
                sys.exit(1)


def main():
    parser = ArgumentParser(description='Manage advanced config')
    parser.add_argument('-i',
                        '--image',
                        dest='image',
                        default='',
                        type=str,
                        help='Image to update, * for all including head node')
    parser.add_argument('-r', '--remove',
                        dest='remove',
                        action='store_true',
                        help='Remove')
    parser.add_argument('-d', '--dry-run',
                        dest='dry_run',
                        action='store_true',
                        help='Dry run')
    parser.add_argument('-s', '--show',
                        dest='show',
                        action='store_true',
                        help='Show fields')
    parser.add_argument('-q', '--quiet',
                        dest='quiet',
                        action='store_true',
                        help='Quiet, set exit code to 1 if changed')
    parser.add_argument('-g', '--globalconfig',
                        dest='globalconfig',
                        action='store_true',
                        help='Manipulate GlobalConfig')
    parser.add_argument('fields', nargs=REMAINDER)
    args = parser.parse_args()

    if args.image == '*':
        image_base = '/cm/images/'
        directories = ['']
        for name in os.listdir(image_base):
            directories.append(image_base + name)
    else:
        directories = [args.image]

    changed = False
    for directory in directories:
        config = Config(
            'GlobalConfig' if args.globalconfig else 'AdvancedConfig',
            directory
        )
        if args.remove:
            config.remove(args.fields)
        else:
            config.update(args.fields)
        if args.dry_run:
            print(config)
        elif args.show:
            print(f'=== {config.path} ===')
            for field in config.fields:
                print(field)
        elif config.changed:
            config.write()
            if args.quiet:
                changed = True
            else:
                print(f'Updated: {config.path}')
        elif not args.quiet:
            print(f'Keep: {config.path}')

    return 1 if args.quiet and changed else 0


if __name__ == '__main__':
    sys.exit(main())
