import argparse
import ast
import os
import re
from pathlib import Path
from typing import Iterable
from typing import MutableMapping
from typing import Optional
from typing import Sequence
from typing import Tuple


def _find_relative_depth(parts: Sequence[str], module: str) -> int:
    pass


class Visitor(ast.NodeVisitor):
    def __init__(
            self,
            parts: Sequence[str],
            srcs: Iterable[str],
            *,
            never: bool,
    ) -> None:
        self.parts = parts
        self.srcs = srcs
        self.to_replace: MutableMapping[int, Tuple[str, str]] = {}
        self.never = never

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        pass


def absolute_imports(
        file: str,
        srcs: Iterable[str],
        *,
        never: bool = False,
) -> int:
    relative_paths = []
    possible_srcs = []
    path = Path(file).resolve()
    for src in srcs:
        try:
            path_relative_to_i = path.relative_to(src)
        except ValueError:
            # `relative_path` can't be resolved relative to `i`
            pass
        else:
            relative_paths.append(path_relative_to_i)
            possible_srcs.append(src)
    if not relative_paths:
        raise ValueError(
            f'{file} can\'t be resolved relative to the current directory.\n'
            'Either run absolufy-imports from the project root, or pass\n'
            '--application-directories',
        )
    relative_path = min(relative_paths, key=lambda x: len(x.parts))

    with open(file, 'rb') as fb:
        contents_bytes = fb.read()
    try:
        contents_text = contents_bytes.decode()
    except UnicodeDecodeError:
        print(f'{file} is non-utf-8 (not supported)')
        return 1
    try:
        tree = ast.parse(contents_text)
    except SyntaxError:
        return 0

    visitor = Visitor(
        relative_path.parts,
        srcs,
        never=never,
    )
    visitor.visit(tree)

    if not visitor.to_replace:
        return 0

    newlines = []
    for lineno, line in enumerate(
        contents_text.splitlines(keepends=True), start=1,
    ):
        if lineno in visitor.to_replace:
            re1, re2 = visitor.to_replace[lineno]
            line = re.sub(re1, re2, line)
        newlines.append(line)
    with open(file, 'w', encoding='utf-8', newline='') as fd:
        fd.write(''.join(newlines))
    return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--application-directories', default='.:src')
    parser.add_argument('files', nargs='*')
    parser.add_argument('--never', action='store_true')
    args = parser.parse_args(argv)

    srcs = [
        str(Path(i).resolve())
        for i in args.application_directories.split(':')
    ]
    ret = 0
    for file in args.files:
        ret |= absolute_imports(
            file,
            srcs,
            never=args.never,
        )
    return ret


if __name__ == '__main__':
    main()
