import re, sys, zlib

def extract(path):
    data = open(path,'rb').read()
    out = []
    for m in re.finditer(rb'stream\r?\n', data):
        start = m.end()
        end = data.find(b'endstream', start)
        if end < 0: continue
        raw = data[start:end]
        try:
            dec = zlib.decompress(raw)
        except Exception:
            try:
                dec = zlib.decompressobj().decompress(raw)
            except Exception:
                continue
        if b'Tj' not in dec and b'TJ' not in dec:
            continue
        # pull text from Tj and TJ array operators
        buf = []
        for tm in re.finditer(rb'\((?:\\.|[^\\()])*\)|\bTd\b|\bTD\b|\bT\*\b|\bTJ\b|\bTj\b|\bET\b', dec):
            tok = tm.group()
            if tok.startswith(b'('):
                s = tok[1:-1]
                s = re.sub(rb'\\([()\\])', rb'\1', s)
                s = s.replace(b'\\n',b' ').replace(b'\\r',b' ').replace(b'\\t',b' ')
                buf.append(s.decode('latin-1'))
            elif tok in (b'Td', b'TD', b'T*', b'ET'):
                buf.append('\n')
        out.append(''.join(buf))
    return '\n'.join(out)

t = extract(sys.argv[1])
t = re.sub(r'[ \t]+', ' ', t)
t = re.sub(r'\n\s*\n+', '\n', t)
print(t)
