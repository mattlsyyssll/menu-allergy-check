"""Contest-specific checks for the mini contest (plug-in example)."""


def score_extra(case, key, status, pages, text):
    """Return [{'field': name, 'verdict': 'right'|'wrong'|'unread', 'group': optional}]."""
    ok = 'password' not in text.lower()
    return [{'field': 'plugin.no_secret_word', 'verdict': 'right' if ok else 'wrong', 'group': 'plugin'}]


def replay_extra(case, key, status, pages, text, transcript):
    """Return [(name, ok, detail)]."""
    return [('plugin_status_line', status is not None, 'STATUS line present' if status else 'no STATUS line')]
