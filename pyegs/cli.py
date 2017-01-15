import argparse
import sys

from . import compiler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='process given Python file')
    parser.add_argument('-o', '--output', help='write compiled scenario to this file')
    args = parser.parse_args()

    reader = sys.stdin
    writer = sys.stdout
    if args.input:
        reader = open(args.input)
    if args.output:
        writer = open(args.output, 'w')

    cli(reader, writer)

    reader.close()


def cli(reader, writer):
    source = reader.read()
    print(compiler.compile(source), file=writer)


if __name__ == '__main__':
    main()
