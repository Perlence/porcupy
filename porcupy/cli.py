import argparse
import struct
import sys
import traceback
import warnings

import attr

from . import compiler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='process given Python file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-o', '--output', help='write compiled scenario to given file')
    group.add_argument('-a', '--attach', help='attach compiled scenario to given Yozhiks map')
    parser.add_argument('--encoding', default='cp1251', help='encode scenarios with given code page')
    args = parser.parse_args()

    reader = sys.stdin
    filename = '<stdin>'
    if args.input is not None:
        reader = open(args.input)
        filename = args.input

    writer = sys.stdout
    line_width = 80
    if args.output is not None:
        writer = open(args.output, 'w')
    elif args.attach is not None:
        writer = ScenarioAttacher(args.attach, args.encoding)
        line_width = 255

    status = cli(filename, reader, writer, line_width)

    reader.close()
    writer.close()

    sys.exit(status)


def cli(filename, reader, writer, width=80):
    source = reader.read()
    try:
        compiled = compiler.compile(source, filename, separate_stmts=True)
    except Exception as exc:
        lineno = getattr(exc, '_porcupy_lineno', None)
        if lineno is None:
            raise
        print_exception(exc, filename, lineno)
        return 1
    wrapped = codewrap(compiled, width)
    print(wrapped, file=writer)


def print_exception(exc, filename, lineno):
    te = traceback.TracebackException(type(exc), exc, None)
    fs = traceback.FrameSummary(filename, lineno, '<module>')
    te.stack = traceback.StackSummary.from_list([fs])

    print('Traceback (most recent call last):', file=sys.stderr)
    for line in te.format():
        print(line, end='', file=sys.stderr)


def codewrap(text, width):
    stmts = text.split('  ')
    if width is None:
        return ' '.join(stmts)

    lines = []
    line = []
    for stmt in stmts:
        length = len(' '.join(line + [stmt]))
        if length > width:
            lines.append(' '.join(line))
            line = [stmt]
        else:
            line.append(stmt)
    lines.append(' '.join(line))
    return '\n'.join(lines)


@attr.s
class ScenarioAttacher:
    path = attr.ib()
    encoding = attr.ib(default='cp1251')

    _map = attr.ib(init=False)

    def __attrs_post_init__(self):
        with open(self.path, 'rb') as fp:
            self._map = Map.from_file(fp, self.encoding)
            self._map.scenario = ''

    def write(self, data):
        self._map.scenario += data

    def close(self):
        with open(self.path, 'wb') as fp:
            self._map.save(fp, self.encoding)


@attr.s
class Map:
    header = attr.ib()
    scenario = attr.ib()
    rest = attr.ib()

    @classmethod
    def from_file(cls, r, encoding='cp1251'):
        header = r.read(7)
        lines = ord(r.read(1))
        scenario = ''
        for _ in range(lines):
            line_length = ord(r.read(1))
            scenario += r.read(line_length).decode(encoding) + '\n'
        rest = r.read()

        return cls(header, scenario, rest)

    def save(self, writer, encoding='cp1251'):
        if len(self.scenario) > 10000:
            warnings.warn('scenario is over 10000 characters, extra characters will be discarded by Yozhiks')

        lines = self.scenario.splitlines()
        if len(lines) > 255:
            warnings.warn("scenario is over 255 lines, extra lines won't be saved")
            lines = lines[:255]
        elif len(lines) > 100:
            warnings.warn('scenario is over 100 lines, extra lines will be discarded by Yozhiks')

        writer.write(self.header)
        writer.write(struct.pack('B', len(lines)))
        for line in lines:
            writer.write(struct.pack('B', len(line)))
            writer.write(line.encode(encoding))
        writer.write(self.rest)


if __name__ == '__main__':
    main()
