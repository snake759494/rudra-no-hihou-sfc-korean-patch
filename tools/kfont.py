import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
HERE=os.path.dirname(os.path.abspath(__file__))
F=ImageFont.truetype(os.path.join(HERE,'..','work','fonts','Galmuri11-Bold.ttf'),12)
def glyph(ch):
    im=Image.new('1',(24,24),0); d=ImageDraw.Draw(im); d.fontmode='1'
    d.text((2,2),ch,font=F,fill=1)
    a=np.array(im).astype(np.uint8)
    # Galmuri11 em: rows 3..13 for full glyphs -> target rows 1..11
    g=np.zeros((12,16),np.uint8)
    ys,xs=np.nonzero(a)
    if len(ys)==0: return g
    dy=-2
    if ys.max()+dy>11: dy=11-ys.max()       # descenders (comma) pulled up
    w=xs.max()-xs.min()+1
    if '가'<=ch<='힣': dx=2-xs.min()+ (1 if w<12 else 0)
    else: dx=(16-w)//2-xs.min()
    for y,x in zip(ys,xs):
        yy,xx=y+dy,x+dx
        if 0<=yy<12 and 0<=xx<16: g[yy,xx]=1
    return g
if __name__=='__main__':
    import sys
    for ch in sys.argv[1]:
        print('\n'.join(''.join('#' if v else '.' for v in r) for r in glyph(ch)));print()
