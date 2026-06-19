import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.search_service import (
    SEARCH_FILTER_GROUPS_META,
    SEARCH_FILTER_OPTIONS,
    SEARCH_SORT_OPTIONS,
)


def main():
    payload = {
        'search_sorts': SEARCH_SORT_OPTIONS,
        'search_filter_groups_meta': SEARCH_FILTER_GROUPS_META,
        'search_filter_static_options': SEARCH_FILTER_OPTIONS,
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == '__main__':
    main()
