import subprocess
from typing import List


class FramaSection:
    def __init__(self, category: str, status: str, body: str) -> None:
        self.category = category
        self.status = status
        self.body = body

    def __str__(self) -> str:
        return f'Category: {self.category}\nStatus: {self.status}\n{self.body}'


def _frama_c_print_command(filepath: str):
    return ['frama-c', '-wp', '-wp-print', filepath]


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


def get_frama_c_print(filepath: str) -> List[FramaSection]:
    result = subprocess.run(
        _frama_c_print_command(filepath),
        capture_output=True,
        text=True
    )
    
    return _parse_frama_c_print(result.stdout)
