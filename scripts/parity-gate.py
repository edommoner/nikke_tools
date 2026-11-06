#!/usr/bin/env python3
"""Compare native kernel payloads with a reusable canonical CPU reference."""
import argparse
import multiprocessing
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import parity_gate as gate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    build = commands.add_parser('build-corpus')
    build.add_argument('--output', type=Path, default=gate.ROOT / 'research/parity/corpus.json')
    build.add_argument('--benchmark', type=Path, help='Complete growth-profile benchmark JSON array')
    build.add_argument('--include-character')
    build.add_argument('--cover', choices=['mechanism-pairs'])
    build.add_argument('--multiplicity', type=int, default=1)
    build.add_argument('--extend-for-character')
    build.add_argument('--corpus', type=Path, help='Existing corpus to extend')
    build.add_argument('--minimum-character-squads', type=int, default=3)
    build.add_argument('--count', type=int, default=20)
    build.add_argument('--seed', type=int, default=20261106)
    run = commands.add_parser('run')
    run.add_argument('--corpus', type=Path, default=gate.ROOT / 'research/parity/corpus.json')
    run.add_argument('--output', type=Path, required=True, help='Named run directory; reuse to resume')
    run.add_argument('--cache', type=Path, default=gate.ROOT / 'research/parity/cpu-cache')
    run.add_argument('--previous', type=Path, help='Previous run summary.json')
    run.add_argument('--workers', type=int, default=10)
    run.add_argument('--sample-fraction', type=float, default=0.1)
    run.add_argument('--coverage-spot-check', type=float, default=0.02)
    run.add_argument('--seed', type=int, default=20261106)
    run.add_argument('--full', action='store_true')
    run.add_argument('--require-cache', action='store_true', help='Fail before execution if any current CPU payload is absent')
    run.add_argument('--native-root', type=Path, help='Disposable GPU/native-host source snapshot; Python remains current')
    args = parser.parse_args()
    if args.command == 'build-corpus':
        if args.count < 0 or args.multiplicity < 1 or args.minimum_character_squads < 1:
            parser.error('count must be nonnegative; multiplicity and minimum must be positive')
        gate.build_corpus(args)
        return 0
    if args.workers < 1:
        parser.error('workers must be positive')
    return gate.run(args)


if __name__ == '__main__':
    multiprocessing.set_start_method('spawn', force=True)
    sys.exit(main())
