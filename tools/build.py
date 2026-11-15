import re, json, os, sys, glob, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = os.path.join(ROOT, 'data'); TR = os.path.join(ROOT, 'translation'); WORK = os.path.join(ROOT, 'work')
FONTS = os.path.join(WORK, 'fonts')
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'Rudra no Hihou (Japan).sfc')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, 'Rudra no Hihou (Korean).sfc')
import hashlib
SRC_SHA = '34552e3a1ecad8a6e979432226a49bd810c2f3c7ea3280e5dbb91e4db868a728'
sys.path.insert(0, HERE)
from table import T
from font import enc as fenc
from kfont import glyph as bigglyph
R0 = open(SRC, 'rb').read()
if hashlib.sha256(R0).hexdigest() != SRC_SHA: sys.exit('원본 ROM SHA-256 불일치: ' + SRC)
R = bytearray(R0)
INV = {}
for c, ch in T.items():
    INV.setdefault(ch, c)

def rd(fn):
    out = []
    for l in open(os.path.join(TR, fn), encoding='utf8').read().split('\n'):
        if '\t' in l:
            k, v = l.split('\t', 1); out.append((k, spellko.kor_text(v)))
    return out

# ---------------- charset ----------------
import spellko
BOARD = spellko.board(R0, T)  # hangul mantra syllables + 'ㄴ' + 'ー'
SPELLCODES = {'ー': 0x7A}
for n, ch in enumerate([b for b in BOARD if b != 'ー']): SPELLCODES[ch] = 0x7B + n
LATIN1 = {'E': 0xEA, 'x': 0xE3, 'p': 0xDB, 'L': 0xF1, 'v': 0xE1, 'H': 0xED, 'P': 0xF5, 'M': 0xF2}
assert not set(SPELLCODES.values()) & set(LATIN1.values())
FREE1 = [c for c in range(0x2A, 0x100) if c not in SPELLCODES.values() and c not in LATIN1.values()]
POOL = open(os.path.join(TR, 'menu_base.txt'), encoding='utf8').read().strip()
if os.path.exists(os.path.join(TR, 'menu_extra.txt')): POOL += open(os.path.join(TR, 'menu_extra.txt'), encoding='utf8').read().strip()
EXTRA1 = [ch for ch in open(os.path.join(TR, 'pool_punct.txt'), encoding='utf8').read().strip()] if os.path.exists(os.path.join(TR, 'pool_punct.txt')) else []
CMAP = dict(SPELLCODES)
one = []
for ch in list(POOL) + EXTRA1:
    if ch not in CMAP and ch not in one: one.append(ch)
assert len(one) <= len(FREE1), ('1-byte overflow', len(one), len(FREE1))
for ch, c in zip(one, FREE1): CMAP[ch] = c
for ch, c in LATIN1.items(): CMAP[ch] = c
CMAP[' '] = 0x18; CMAP['　'] = 0x18
for ch, c in {'.': 0x19, ',': 0x1A, '?': 0x1B, '!': 0x1C, '「': 0x1D, '」': 0x1E, '‥': 0x1F}.items(): CMAP[ch] = c
for i in range(10): CMAP[str(i)] = 0x20 + i
KEEP2 = {'『': 0x100, '』': 0x101, '・': 0x106, '～': 0x166, '(': 0x1CA, ')': 0x1CB, '←': 0x39A, ':': 0x39B,
         '→': 0x39C, '+': 0x3A4, '↑': 0x3AA, '↓': 0x3D9}
CMAP.update(KEEP2)
CMAP['-'] = 0x7A; CMAP['ー'] = 0x7A
FREE2 = [c for c in range(0x100, 0x400) if c not in KEEP2.values()]

texts = []
for f in sorted(glob.glob(os.path.join(TR, 'd*_ko.txt'))) + [os.path.join(TR, 'sys_ko.txt')]:
    texts += [v for _, v in rd(os.path.basename(f))]
for f in ['names_t2.txt', 'names_t8.txt', 'names_misc.txt', 'names_big.txt']:
    texts += [v for _, v in rd(f)]
texts += [v for _, v in rd('labels_ko.txt')]
need = collections.Counter()
for t in texts:
    t = re.sub(r'\{[^}]*\}|<[^>]*>|¶', '', t)
    for ch in t:
        if ch not in CMAP: need[ch] += 1
need2 = [ch for ch, _ in need.most_common()]
if len(need2) > len(FREE2):
    print('TOO MANY 2-byte chars', len(need2), len(FREE2)); print(''.join(need2[len(FREE2):])); sys.exit(1)
for ch, c in zip(need2, FREE2): CMAP[ch] = c
print('1byte', len(one), '/', len(FREE1), ' 2byte', len(need2), '/', len(FREE2))

def encode(s, menu=False, nocomp=False):
    o = bytearray(); i = 0
    while i < len(s):
        m = re.match(r'\{0b:([0-9a-f]{2})\}|\{([0-9a-f]{2})\}|<P(\d)>|<W(\d+)>', s[i:])
        if m:
            if m.group(1): o += bytes([0x0B, int(m.group(1), 16)])
            elif m.group(2): o.append(int(m.group(2), 16))
            elif m.group(3): o += bytes([0x12, int(m.group(3))])
            else: o += bytes([0x0E, int(m.group(4))])
            i += m.end(); continue
        if not menu and not nocomp and s.startswith('     ', i):
            o += bytes([0x12, 0x43]); i += 5; continue
        ch = s[i]; i += 1
        if ch == '¶': o.append(4); continue
        c = CMAP[ch]
        if c >= 0x100:
            if menu: raise ValueError('2-byte in menu: %r in %r' % (ch, s))
            o += bytes([c >> 8, c & 0xFF])
        else: o.append(c)
    return bytes(o)

# ---------------- fonts ----------------
F7 = ImageFont.truetype(os.path.join(FONTS, 'Galmuri7.ttf'), 8)
def smallglyph(ch):
    im = Image.new('1', (16, 16), 0); d = ImageDraw.Draw(im); d.fontmode = '1'
    d.text((2, 2), ch, font=F7, fill=1)
    a = np.array(im).astype(np.uint8)
    ys, xs = np.nonzero(a)
    g = np.zeros((8, 16), np.uint8)
    if len(ys) == 0: return g
    w = xs.max() - xs.min() + 1
    dx = (8 - w) // 2 - xs.min() if not ('가' <= ch <= '힣') else 0 - xs.min()
    for y, x in zip(ys, xs):
        yy = y - 3; xx = x + dx
        if 0 <= yy < 8 and 0 <= xx < 8: g[yy, xx * 2] = g[yy, xx * 2 + 1] = 1
    return g
def senc(g):
    o = bytearray(16)
    for r in range(8):
        L = Rr = 0
        for x in range(8): L |= int(g[r, x]) << (7 - x); Rr |= int(g[r, x + 8]) << (7 - x)
        o[r] = L; o[8 + r] = Rr
    return bytes(o)
BIG = 0x1E7F80; SMALL = 0x1E73C0
for ch, c in CMAP.items():
    if ch in KEEP2 or ch in (' ', '　', '-', 'ー') or (c in LATIN1.values()) or ch.isdigit(): continue
    R[BIG + c * 24: BIG + c * 24 + 24] = fenc(bigglyph(ch))
    if 0x20 <= c < 0x100:
        R[SMALL + (c - 0x20) * 16: SMALL + (c - 0x20) * 16 + 16] = senc(smallglyph(ch))
# mantra 'ㄴ' cell: drawn low-left so it reads as a batchim of the previous syllable
_g = bigglyph('은'); _n = np.zeros((12, 16), np.uint8); _n[9:12, 0:12] = _g[9:12, 4:16]
R[BIG + CMAP['ㄴ'] * 24: BIG + CMAP['ㄴ'] * 24 + 24] = fenc(_n)
_s = np.zeros((8, 16), np.uint8)
for _y, _x0, _x1 in ((5, 0, 1), (6, 0, 1), (7, 0, 4)): _s[_y, _x0 * 2:_x1 * 2] = 1
R[SMALL + (CMAP['ㄴ'] - 0x20) * 16: SMALL + (CMAP['ㄴ'] - 0x20) * 16 + 16] = senc(_s)
# 1-byte slots left unused: blank them in small font
for c in FREE1[len(one):]:
    R[SMALL + (c - 0x20) * 16: SMALL + (c - 0x20) * 16 + 16] = bytes(16)

R[0x1EEA00 + 0x18 * 32: 0x1EEA00 + 0x19 * 32] = bytes(32)  # blank small-font space
# ---------------- strings ----------------
starts = sorted(json.load(open(os.path.join(D, 'strings.json'))))
END = 0x3476AB
nxt = {a: (starts[i + 1] if i + 1 < len(starts) else END) for i, a in enumerate(starts)}
ko = {}
for f in sorted(glob.glob(os.path.join(TR, 'd*_ko.txt'))) + [os.path.join(TR, 'sys_ko.txt')]:
    for k, v in rd(os.path.basename(f)): ko[int(k, 16)] = v
assert len(ko) == len(starts), (len(ko), len(starts))

# system strings: in place when fits, else relocate to F0:0000-7FFF
sysref = json.load(open(os.path.join(D, 'sysref.json')))
sysfree = 0x300001; SYSEND = 0x308000
R[0x300000] = 0
TABLES = [(0x398b, 256), (0x72f2, 65), (0x7889, 12), (0x58c2, 4), (0x8ad4, 4), (0x8d62, 4)]
TREF = collections.defaultdict(list)
for t, n in TABLES:
    for i in range(n):
        v = 0x300000 | (R0[t + 2 * i] | R0[t + 2 * i + 1] << 8)
        if v in nxt: TREF[v].append(t + 2 * i)
        else: R[t + 2 * i] = 0; R[t + 2 * i + 1] = 0  # -> F0:0000 (zero byte)
sysbad = []
for a in [x for x in starts if x < 0x30A1A0]:
    b = encode(ko[a]) + b'\0'
    room = nxt[a] - a
    if len(b) <= room:
        R[a:a + room] = b + b'\0' * (room - len(b)); continue
    r16, r24 = sysref['%06x' % a]
    imm = r16; r16 = sorted(TREF[a])
    if imm or (not r16 and not r24):
        sysbad.append((a, len(b), room)); continue
    assert sysfree + len(b) <= SYSEND
    R[sysfree:sysfree + len(b)] = b
    for p in r24:
        assert R0[p:p + 3] == bytes([a & 0xFF, (a >> 8) & 0xFF, 0xF0])
        R[p:p + 3] = bytes([sysfree & 0xFF, (sysfree >> 8) & 0xFF, 0xF0])
    for p in r16:
        assert R0[p] | R0[p + 1] << 8 == a & 0xFFFF
        R[p] = sysfree & 0xFF; R[p + 1] = (sysfree >> 8) & 0xFF
    # old place: keep a copy truncated (for mid-string pointers safety)
    R[a:a + room] = bytes(room)
    sysfree += len(b)
if sysbad:
    for a, n, room in sysbad: print('SYS TOO LONG %06x %d>%d %s' % (a, n, room, ko[a]))
    sys.exit(1)
print('sys reloc used', hex(sysfree - 0x300000))

# dialogue: repack
refs = json.load(open(os.path.join(D, 'refs.json')))
REG = [(0x30A1A0, 0x310000), (0x310000, 0x320000), (0x320000, 0x330000), (0x330000, 0x340000),
       (0x340000, 0x350000), (0x350000, 0x360000)] + [(b, b + 0x10000) for b in range(0x3B0000, 0x400000, 0x10000)] + [(0x3A8000, 0x3B0000)]
for s, e in REG[:6]: R[max(s, 0x30A1A0):e] = b'\xff' * (e - max(s, 0x30A1A0))
ri = 0; pos = REG[0][0]
for a in [x for x in starts if x >= 0x30A1A0]:
    b = encode(ko[a]) + b'\0'
    if pos + len(b) > REG[ri][1]:
        ri += 1; pos = REG[ri][0]
    R[pos:pos + len(b)] = b
    snes = 0xC00000 + pos
    n = 0
    for p in refs['%06x' % a]:
        if R0[p - 1] in (0xD3, 0xD4, 0x13, 0xD5, 0xD6) and (p >> 16) in (0, 4, 5, 6):
            R[p] = snes & 0xFF; R[p + 1] = (snes >> 8) & 0xFF; R[p + 2] = snes >> 16; n += 1
    assert n, hex(a)
    pos += len(b)
print('dialogue end region', ri, hex(pos))

# ---------------- dictionaries ----------------
DICT = {'t0': (0x31008, 12), 't1': (0x31608, 12), 't2': (0x30000, 8), 't6': (0x31C08, 8), 't7': (0x32A08, 8),
        't8': (0x30800, 8), 't9': (0x32CD8, 8), 't10': (0x32EE0, 12), 't11': (0x32FB8, 4)}
entries = [('t2:' + k, v) for k, v in rd('names_t2.txt')] + [('t8:' + k, v) for k, v in rd('names_t8.txt')] + rd('names_misc.txt') + rd('names_big.txt')
for k, v in entries:
    t, i = k.split(':'); i = int(i, 16); off, sz = DICT[t]
    b = encode(v, menu=(t not in ('t0', 't1')), nocomp=True)
    assert len(b) <= sz, (k, v, len(b))
    R[off + i * sz: off + i * sz + sz] = b + b'\0' * (sz - len(b))

# ---------------- menu labels ----------------
LJ = {}
for l in open(os.path.join(D, 'labels.tsv'), encoding='utf8'):
    p = l.rstrip('\n').split('\t'); LJ[int(p[0], 16)] = int(p[1])
for k, v in rd('labels_ko.txt'):
    off = int(k, 16); n = LJ[off]
    b = encode(v, menu=True)
    assert len(b) <= n, (k, v)
    b = b + bytes(n - len(b))
    for j, c in enumerate(b):
        w0 = R0[off + j * 2] | R0[off + j * 2 + 1] << 8
        w = (w0 & 0xFC00) | (0x200 + c * 2)
        R[off + j * 2] = w & 0xFF; R[off + j * 2 + 1] = w >> 8

print('spell', spellko.apply(R, R0, T, CMAP, [CMAP[ch] for ch in BOARD]))
# prologue (graphic text)
PL = open(os.path.join(TR, 'prologue_ko.txt'), encoding='utf8').read().strip().split(chr(10))
orig_n = 0; p = 0x37F711
for _ in range(21):
    while R0[p] != 0xFF: p += 1
    p += 1
orig_n = p - 0x37F711
chars = sorted(set(''.join(PL)) - {'‥'})
slots = [v for v in range(0, 0x100, 2) if v != 0x08]
assert len(chars) + 1 <= len(slots), len(chars)
PV = {'‥': 0x08}
def pslot(v, m):
    o = (v & 0xF) * 8 + (v >> 4) * 0x100
    for base, ro in ((0x37D711, 0), (0x37D791, 8)):
        for t in range(2):
            for r in range(8):
                b = 0
                for x in range(8): b |= int(m[ro + r, t * 8 + x]) << (7 - x)
                R[base + o + t * 8 + r] = b
for ch, v in zip(chars, slots):
    PV[ch] = v
    m = np.zeros((16, 16), np.uint8)
    if ch != ' ':
        g = bigglyph(ch); xs = np.nonzero(g.any(0))[0]
        g = np.roll(g, -xs.min() if len(xs) else 0, axis=1); m[2:14, :] = g
    pslot(v, m)
out = bytearray()
for l in PL: out += bytes(PV[c] for c in l) + bytes([0xFF])
assert len(out) <= orig_n, (len(out), orig_n)
out += bytes([0xFF]) * (orig_n - len(out))
R[0x37F711:0x37F711 + orig_n] = out
print('prologue glyphs', len(chars), 'bytes', len(out), orig_n)
os.makedirs(WORK, exist_ok=True)
# element icons (火水雷風陽陰) 16x16 2bpp at DE:EF80, tiles 0x1C..
for n, ch in enumerate('불물뇌풍양음'):
    g = bigglyph(ch); m = np.zeros((16, 16), np.uint8); m[2:14, :] = g
    for half, (r0) in enumerate((0, 8)):
        for side in range(2):
            o = 0x1EEF80 + (n * 4 + half * 2 + side) * 16
            for r in range(8):
                b = 0
                for x in range(8): b |= int(m[r0 + r, side * 8 + x]) << (7 - x)
                R[o + 2 * r] = b; R[o + 2 * r + 1] = 0
# scenario-select sprite label '旅立ちより' / '日' (OBJ tiles at DE:EE00)
def objput(img, tops, bots):
    for i, t in enumerate(tops):
        for half, tt in ((0, t), (1, bots[i])):
            o = 0x1EEE00 + tt * 16
            for r in range(8):
                b = 0
                for x in range(8): b |= int(img[half * 8 + r, i * 8 + x]) << (7 - x)
                R[o + 2 * r] = b; R[o + 2 * r + 1] = 0
lab = np.zeros((16, 48), np.uint8)
for j, ch in enumerate('여행'):
    g = bigglyph(ch); xs = np.nonzero(g.any(0))[0]; g = g[:, xs.min():xs.max() + 1]
    x0 = 1 + j * 13; lab[2:14, x0:x0 + g.shape[1]] = g
R[0x1EEE00:0x1EEE00 + 8 * 16] = bytes(128)
objput(lab, [8, 9, 0xC, 0xD, 0x10, 0x11], [0xA, 0xB, 0xE, 0xF, 0x12, 0x13])
d = np.zeros((16, 16), np.uint8); g = bigglyph('일'); xs = np.nonzero(g.any(0))[0]; g = g[:, xs.min():xs.max() + 1]
d[2:14, 2:2 + g.shape[1]] = g
objput(d, [0x14, 0x15], [0x16, 0x17])
import title_sub; print('title', title_sub.apply(R))
# checksum
R[0xFFDC:0xFFE0] = bytes([0xFF, 0xFF, 0, 0])
cs = sum(R) & 0xFFFF
R[0xFFDC:0xFFE0] = bytes([(cs ^ 0xFFFF) & 0xFF, (cs ^ 0xFFFF) >> 8, cs & 0xFF, cs >> 8])
open(OUT, 'wb').write(R)
print('SHA-256', hashlib.sha256(bytes(R)).hexdigest())
print('written', OUT)
