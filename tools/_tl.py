# katakana spell word -> hangul (1 syllable per kana "mora" unit; ン/ッ as batchim)
CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
JUNG = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
JONG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
def S(c, v, j=''): return chr(0xAC00 + (CHO.index(c) * 21 + JUNG.index(v)) * 28 + JONG.index(j))
def split(s):
    o = ord(s) - 0xAC00; return CHO[o // 588], JUNG[o // 28 % 21], JONG[o % 28]
B = {}
rows = {'': 'ㅇ', 'カ': 'ㅋ', 'ガ': 'ㄱ', 'サ': 'ㅅ', 'ザ': 'ㅈ', 'タ': 'ㅌ', 'ダ': 'ㄷ', 'ナ': 'ㄴ', 'ハ': 'ㅎ', 'バ': 'ㅂ', 'パ': 'ㅍ', 'マ': 'ㅁ', 'ラ': 'ㄹ'}
K = {'ア': 'ㅇㅏ','イ':'ㅇㅣ','ウ':'ㅇㅜ','エ':'ㅇㅔ','オ':'ㅇㅗ',
 'カ':'ㅋㅏ','キ':'ㅋㅣ','ク':'ㅋㅡ','ケ':'ㅋㅔ','コ':'ㅋㅗ','ガ':'ㄱㅏ','ギ':'ㄱㅣ','グ':'ㄱㅡ','ゲ':'ㄱㅔ','ゴ':'ㄱㅗ',
 'サ':'ㅅㅏ','シ':'ㅅㅣ','ス':'ㅅㅡ','セ':'ㅅㅔ','ソ':'ㅅㅗ','ザ':'ㅈㅏ','ジ':'ㅈㅣ','ズ':'ㅈㅡ','ゼ':'ㅈㅔ','ゾ':'ㅈㅗ',
 'タ':'ㅌㅏ','チ':'ㅊㅣ','ツ':'ㅊㅡ','テ':'ㅌㅔ','ト':'ㅌㅗ','ダ':'ㄷㅏ','ヂ':'ㅈㅣ','ヅ':'ㅈㅡ','デ':'ㄷㅔ','ド':'ㄷㅗ',
 'ナ':'ㄴㅏ','ニ':'ㄴㅣ','ヌ':'ㄴㅜ','ネ':'ㄴㅔ','ノ':'ㄴㅗ','ハ':'ㅎㅏ','ヒ':'ㅎㅣ','フ':'ㅎㅜ','ヘ':'ㅎㅔ','ホ':'ㅎㅗ',
 'バ':'ㅂㅏ','ビ':'ㅂㅣ','ブ':'ㅂㅡ','ベ':'ㅂㅔ','ボ':'ㅂㅗ','パ':'ㅍㅏ','ピ':'ㅍㅣ','プ':'ㅍㅡ','ペ':'ㅍㅔ','ポ':'ㅍㅗ',
 'マ':'ㅁㅏ','ミ':'ㅁㅣ','ム':'ㅁㅜ','メ':'ㅁㅔ','モ':'ㅁㅗ','ヤ':'ㅇㅑ','ユ':'ㅇㅠ','ヨ':'ㅇㅛ',
 'ラ':'ㄹㅏ','リ':'ㄹㅣ','ル':'ㄹㅜ','レ':'ㄹㅔ','ロ':'ㄹㅗ','ワ':'ㅇㅘ','ヲ':'ㅇㅗ','ヴ':'ㅂㅡ'}
# yoon / small vowel combos (applied to preceding consonant)
YO = {'ャ': {'ㅣ': 'ㅑ'}, 'ュ': {'ㅣ': 'ㅠ'}, 'ョ': {'ㅣ': 'ㅛ'}}
SMALLV = {'ァ': 'ㅏ', 'ィ': 'ㅣ', 'ゥ': 'ㅜ', 'ェ': 'ㅔ', 'ォ': 'ㅗ'}
def translit(w):
    out = []  # list of [cho, jung, jong]
    for ch in w:
        if ch in K:
            c, v = K[ch]; out.append([c, v, '']); continue
        last = out[-1] if out else None
        if ch in YO:
            if last and last[1] == 'ㅣ' and not last[2]:
                if last[0] in 'ㅈㅊ': last[1] = {'ャ':'ㅏ','ュ':'ㅜ','ョ':'ㅗ'}[ch]
                else: last[1] = YO[ch]['ㅣ']
            else: out.append(['ㅇ', {'ャ':'ㅑ','ュ':'ㅠ','ョ':'ㅛ'}[ch], ''])
            continue
        if ch in SMALLV:
            v = SMALLV[ch]
            if last and not last[2]:
                if ch == 'ゥ' and last[1] in 'ㅜㅡ' : last[1] = 'ㅜ'; continue
                if last[1] in 'ㅜㅡ' and last[0] in 'ㅎㅂ' and v in 'ㅏㅣㅔㅗ':  # ファ フィ フェ フォ ヴァ
                    last[0] = {'ㅎ':'ㅍ','ㅂ':'ㅂ'}[last[0]]; last[1] = v; continue
                if last[1] in 'ㅜㅡ' and v in 'ㅏㅣㅔ' and last[0] in 'ㅇ':  # ウィ ウェ ウァ
                    last[1] = {'ㅏ':'ㅘ','ㅣ':'ㅟ','ㅔ':'ㅞ'}[v]; continue
                if last[1] in 'ㅜㅡ' and v == 'ㅗ' and last[0] == 'ㅇ': last[1] = 'ㅝ'; continue
                if last[1] in 'ㅔㅗㅡ' and v == 'ㅣ' and last[0] in 'ㅌㄷ':  # ティ ディ
                    last[1] = 'ㅣ'; continue
                if last[1] in 'ㅡ' and v in 'ㅏㅔㅗ' and last[0] in 'ㅊㅌㄷ':  # ツァ トゥ
                    last[1] = v; continue
                if last[1] == 'ㅣ' and v == 'ㅔ':  # シェ ジェ チェ イェ
                    last[1] = 'ㅔ' if last[0] in 'ㅅㅈㅊ' else 'ㅖ'; 
                    if last[0] == 'ㅅ': last[0] = 'ㅅ'
                    continue
                if last[1] == v: continue
            out.append(['ㅇ', v, '']); continue
        if ch == 'ン':
            if last and not last[2]: last[2] = 'ㄴ'
            else: out.append(['ㅇ', 'ㅡ', 'ㄴ'])
            continue
        if ch == 'ッ':
            if last and not last[2]: last[2] = 'ㅅ'
            else: out.append(['ㅇ', 'ㅡ', 'ㅅ'])
            continue
        if ch == 'ー':
            continue
        raise ValueError(ch + ' in ' + w)
    return ''.join(S(*x) for x in out)
