import os
import subprocess
from typing import List

from django.conf import settings


class FramaSection:
    def __init__(self, category: str, status: str, body: str) -> None:
        self.category = category
        self.status = status
        self.body = body

    def __str__(self) -> str:
        return f'Category: {self.category}\nStatus: {self.status}\n{self.body}'


def _frama_c_print_command(filepath: str, result_filepath: str):
    return ['frama-c', '-wp', '-wp-print', '-wp-log', f'r:{result_filepath}', filepath]


def _parse_frama_c_print(body: str) -> List[FramaSection]:
    sections = body.split(
        '------------------------------------------------------------\n')
    objs = []
    # Don't look at first and last "sections" - those are not
    # sections related to proving.
    for section in sections[1:-1]:
        section = section.strip()
        lines = section.split('\n')
        if len(lines) < 2:
            # Section with category and status has at least 2 lines.
            continue

        body = section

        # Category is either before first '(' or is a whole line without ':'.
        category = lines[0].split('(')[0].strip()
        category = category[:-1] if category[-1] == ':' else category

        # Last line contains status, that is present after word 'returns'.
        # If cannot be found, status is set to 'Unknown'.
        last_line = lines[-1].split(' ')
        try:
            status = last_line[last_line.index('returns') + 1]
        except ValueError:
            status = 'Unknown'

        objs.append(FramaSection(category, status, body))

    return objs


def get_frama_c_print(filepath: str):
    result_directory = os.path.join(settings.BASE_DIR, 'files', 'temp')
    try:
        os.mkdir(result_directory)
    except FileExistsError:
        # Directory already exists.
        pass

    result_filepath = os.path.join(result_directory, 'result.txt')
    result = subprocess.run(
        _frama_c_print_command(filepath, result_filepath),
        capture_output=True,
        text=True
    )
    sections = _parse_frama_c_print(result.stdout)
    with open(result_filepath, 'r') as f:
        result_data = f.read()

    return result_data, sections
