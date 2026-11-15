"""Korean mantra system: katakana spell words -> Hangul syllable spelling.

Rules (consistent for dictionary, input board, hints, preset lists):
  * one syllable per kana mora; yoon/small vowels merge into the syllable (シャ=샤, ティ=티, ファ=파)
  * ッ is dropped, ン is its own cell 'ㄴ', ー is kept
  * a few rare yoon syllables are spelled out (ギョ=기요 ...) to fit the 99-cell board
"""
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _tl
ODD = set('ァィゥェォャュョッヲヂヅヴ')
CUT = {'교': '기요', '뱌': '비야', '규': '기유', '뷰': '비유', '체': '치에'}
KANA = re.compile('[ァ-ヴ][ァ-ヴー]*')
OVR = {}
RAW = dict(zip('ァィゥェォャュョヲヂヅヴ', '아이우에오야유요오지즈브'))
def kor_raw(w):
    # unmerged spelling: every kana its own cell
    return ''.join(RAW.get(ch) or (kor(ch) if ch not in 'ッ' else '') for ch in w)
def kor(w):
    if w in OVR: return OVR[w]
    out = []
    for seg in re.split('(ー|ン)', w.replace('ッ', '')):
        if seg == 'ン': out.append('ㄴ')
        elif seg == 'ー': out.append('ー')
        elif seg: out.append(_tl.translit(seg))
    s = ''.join(out)
    return ''.join(CUT.get(c, c) for c in s)
WORDS = []; PRESET = []
MASKED = re.compile('[ァ-ヴー?？]*[?？][ァ-ヴー?？]*')
def mask(h):
    """partial hint like フ?ット: find the dictionary word, hide the Korean syllable(s) holding the hidden kana"""
    if not re.search('[ァ-ヴ]', h): return h
    rx = re.compile('^' + re.sub('[?？]', '.', h) + '$')
    cand = [w for w in PRESET if rx.match(w)] + [w for w in WORDS if rx.match(w)]
    if not cand:
        return KANA.sub(lambda m: kor(m.group(0)), h)
    w = cand[0]; k = list(kor(w))
    for i, ch in enumerate(h):
        if ch not in '?？': continue
        a, b = len(kor(w[:i])), len(kor(w[:i + 1]))
        for j in (range(a, b) if b > a else [max(a - 1, 0)]): k[j] = '?'
    return ''.join(k)
def kor_text(s):
    s = MASKED.sub(lambda m: mask(m.group(0)), s)
    return KANA.sub(lambda m: kor(m.group(0)), s)
DICT = 0x1CC000
def words(R0, T):
    out = []
    for i in range(2048):
        r = R0[DICT + i * 8: DICT + i * 8 + 8]
        v = r[6] | r[7] << 8
        if v == 0x7FF8: continue
        out.append((''.join(T[c] for c in r[:6] if c), v, i))
    return out
def init(R0, T):
    """resolve spelling collisions: winner keeps natural spelling, others fall back to unmerged spelling"""
    OVR.clear()
    ws = words(R0, T)
    WORDS[:] = [w for w, v, i in ws]
    PRESET[:] = [''.join(T[c] for c in R0[0x32FDC + 6 * j:0x32FDC + 6 * j + 6] if c) for j in range(64)]
    taken = {}
    groups = {}
    for w, v, i in ws: groups.setdefault(kor(w), []).append((sum(c in ODD for c in w), len(w), i, w, v))
    for k, g in groups.items():
        g.sort(); taken[k] = g[0][3]
    for k, g in groups.items():
        for *_, w, v in g[1:]:
            alt = kor_raw(w)
            if alt and alt not in taken and len(alt) <= 6:
                taken[alt] = w; OVR[w] = alt
CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
def board(R0, T):
    init(R0, T)
    syl = set()
    for w, v, i in words(R0, T): syl.update(kor(w))
    syl.discard('ㄴ'); syl.discard('ー')
    order = 'ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ'
    syl = sorted(syl, key=lambda c: (order.index(_tl.split(c)[0]), c))
    return syl + ['ㄴ', 'ー']

FREE = 0xF1C2  # bank C0 free space (1599 bytes)
def apply(R, R0, T, CMAP, codes):
    """codes: list of board cell codes in board order (None = empty)."""
    rep = {}
    def enc(w, n=6):
        k = kor(w)
        b = bytes(CMAP[c] for c in k)
        assert len(b) <= n and all(c < 0x100 for c in (CMAP[x] for x in k)), (w, k)
        return b
    # ---- dictionary ----
    best = {}
    for w, v, i in words(R0, T):
        b = enc(w)
        if not b: rep.setdefault('dropped', []).append((w, v)); continue
        sc = (sum(c in ODD for c in w), len(w), i)
        if b not in best or sc < best[b][0]: 
            if b in best: rep.setdefault('dropped', []).append(best[b][1])
            best[b] = (sc, (w, v))
        else: rep.setdefault('dropped', []).append((w, v))
    ent = sorted(best.items(), key=lambda kv: bytes(reversed(bytes(6 - len(kv[0])) + kv[0])))
    assert len(ent) <= 2048
    for i in range(2048):
        if i < len(ent):
            b, (_, (w, v)) = ent[i]
            row = bytes(6 - len(b)) + b + bytes([v & 0xFF, v >> 8])
        else:
            row = b'\xff' * 6 + b'\xf8\x7f'
        R[DICT + i * 8: DICT + i * 8 + 8] = row
    rep['dict'] = len(ent)
    # ---- 6-byte spell name tables / preset lists ----
    def conv6(off, n, step=6):
        k = 0
        for j in range(n):
            a = off + j * step; r = R0[a:a + 6]
            body = r.rstrip(b'\0')
            if not body or b'\0' in body or not all(0x7A <= c < 0xCC for c in body): continue
            b = enc(''.join(T[c] for c in body))
            R[a:a + 6] = b + bytes(6 - len(b)); k += 1
        return k
    rep['t5'] = conv6(0x32408, 256)
    rep['t4'] = conv6(0x32A98, 96)
    rep['preset'] = conv6(0x32FDC, 64)
    rep['init'] = sum(conv6(a, 32) for a in (0x3832E, 0x38434, 0x3853A))
    # ---- input board ----
    COLS, ROWS = 11, 9
    grid = [[None] * COLS for _ in range(ROWS)]
    for n, c in enumerate(codes): grid[n // COLS][n % COLS] = c
    pos = {}
    for r in range(ROWS):
        for col in range(COLS):
            if grid[r][col] is not None: pos[grid[r][col]] = (col, r)
    lo, hi = 0x7A, max(pos) + 1
    nav = bytearray(4 * (hi - lo)); pt = bytearray(2 * (hi - lo))
    def rowcells(r): return [c for c in grid[r] if c is not None]
    for c, (col, r) in pos.items():
        i = c - lo
        pt[2 * i] = 3 + 2 * col; pt[2 * i + 1] = 6 + 2 * r
        rc = [x for x in grid[r]]
        # right
        nx = next((rc[k] for k in range(col + 1, COLS) if rc[k] is not None), None)
        if nx is None: nx = r if r < 6 else rowcells(r)[0]
        # left
        pv = next((rc[k] for k in range(col - 1, -1, -1) if rc[k] is not None), None)
        if pv is None: pv = 6 + r if r < 6 else rowcells(r)[-1]
        def vert(d):
            rr = r
            while True:
                rr = (rr + d) % ROWS
                if grid[rr][col] is not None: return grid[rr][col]
                if rr == r: return c
        nav[4 * i:4 * i + 4] = bytes([nx, pv, vert(1), vert(-1)])
    tm = bytearray()
    W = 2 * COLS - 1; H = 2 * ROWS - 1
    for y in range(H):
        for x in range(W):
            c = grid[y // 2][x // 2] if (y % 2 == 0 and x % 2 == 0) else None
            w = 0 if c is None else 0x2000 | (0x200 + c * 2)
            tm += bytes([w & 0xFF, w >> 8])
    blob_nav = FREE; blob_pt = blob_nav + len(nav); blob_tm = blob_pt + len(pt)
    tmrec = bytes([W * 2 - 1, 0, H, 0]) + bytes(tm)
    assert blob_tm + len(tmrec) <= 0xF1C2 + 1599
    assert all(b == 0xFF for b in R0[FREE:blob_tm + len(tmrec)])
    R[blob_nav:blob_nav + len(nav)] = nav; R[blob_pt:blob_pt + len(pt)] = pt
    R[blob_tm:blob_tm + len(tmrec)] = tmrec
    def p24(at, addr, old):
        assert R0[at:at + 3] == bytes([old & 0xFF, old >> 8 & 0xFF, 0xC0]), hex(at)
        R[at:at + 3] = bytes([addr & 0xFF, addr >> 8 & 0xFF, 0xC0])
    for at in (0x7AD1, 0x8BE7): p24(at, blob_nav, 0x8497)
    for at in (0x7CAA, 0x8D17): p24(at, blob_pt, 0x85DF)
    for at in (0x7CB4, 0x8D21): p24(at, blob_pt + 1, 0x85E0)
    for at in (0x7CD2, 0x8D58):
        assert R0[at] | R0[at + 1] << 8 == 0x98C4, hex(at)
        R[at] = blob_tm & 0xFF; R[at + 1] = blob_tm >> 8
    # command column (mantra screen: 6 commands)
    t = bytearray()
    for k in range(6):
        rc = rowcells(k); t += bytes([rc[0], rc[-1], (k + 1) % 6, (k - 1) % 6])
    R[0x7A7D:0x7A95] = t
    # name entry: 2 commands + exit map
    t = bytearray()
    for k in range(2):
        rc = rowcells(k); t += bytes([rc[0], rc[-1], 1 - k, 1 - k])
    R[0x8BA3:0x8BAB] = t
    m = bytearray()
    for r in range(6): m.append(r if r < 2 else rowcells(r)[0])
    for r in range(6): m.append(r if r < 2 else rowcells(r)[-1])
    R[0x8BAB:0x8BB7] = m
    rep['board'] = (len(codes), hex(blob_tm + len(tmrec)))
    return rep
