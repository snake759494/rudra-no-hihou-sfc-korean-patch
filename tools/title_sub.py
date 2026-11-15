# Korean subtitle on title screen (sprites)
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
def apply(R, text='루드라의 비보', X=124, Y=148, col=2):
    F=ImageFont.truetype(os.path.join(HERE,'..','work','fonts','Galmuri11-Bold.ttf'),12)
    W=F.getbbox(text)[2]+1
    cols=(W+7)//8
    im=Image.new('L',(cols*8,16),0); ImageDraw.Draw(im).text((0,1),text,font=F,fill=255)
    a=(np.array(im)>128)
    # trim fully empty tiles is unnecessary; build tiles
    tiles=bytearray()
    spr=[]
    n=0
    for ty in range(2):
        for tx in range(cols):
            blk=a[ty*8:ty*8+8,tx*8:tx*8+8]
            if not blk.any(): continue
            t=bytearray(32)
            for r in range(8):
                b=0
                for x in range(8): b|=int(blk[r,x])<<(7-x)
                for k in range(4):
                    if col>>k&1: t[[0,1,16,17][k]+2*r]=b
            tiles+=t; spr.append((X+tx*8,Y+ty*8,0x10+n)); n+=1
    assert 15+len(spr)<=48
    BASE=0x09F000; TD=0x09F200
    assert all(b==0xFF for b in R[BASE:TD+len(tiles)])
    R[TD:TD+len(tiles)]=tiles
    c=bytearray()
    def lda(v): c.extend([0xA9,v&0xFF,v>>8])
    def sta(a): c.extend([0x8D,a&0xFF,a>>8])
    c+=b'\xC2\x20'
    for i,(x,y,t) in enumerate(spr):
        e=0x400+4*(15+i); lda(x|y<<8); sta(e); lda(t|0x3A00); sta(e+2)
    # high table: entries 8..(15+len) visible small
    last=15+len(spr)
    for w in range(0x602,0x620,2):
        v=0
        for j in range(8):
            ent=(w-0x600)*4+j
            if ent==15 and False: pass
            if ent>=last: v|=1<<(2*j)
        lda(v); sta(w)
    c+=b'\x9C\x00\x06'  # STZ $0600
    # DMA tiles -> VRAM word 0x6100
    c+=b'\xE2\x20'; c+=b'\xA9\x80'; sta(0x2115); c+=b'\xC2\x20'
    lda(0x6100); sta(0x2116); lda(0x1801); sta(0x4370); lda(TD&0xFFFF); sta(0x4372)
    c+=b'\xE2\x20\xA9\xC9'; sta(0x4374); c+=b'\xC2\x20'; lda(len(tiles)); sta(0x4375)
    c+=b'\xE2\x20\xA9\x80'; sta(0x420B); c+=b'\xC2\x20'
    c+=b'\x6B'
    assert len(c)<=TD-BASE, len(c)
    R[BASE:BASE+len(c)]=c
    # hook at C9:08BF (9 bytes: STZ 600 / LDA #4000 / STA 602)
    assert R[0x0908BF:0x0908C8]==bytes.fromhex('9c0006a900408d0206')
    R[0x0908BF:0x0908C8]=bytes([0x22,0x00,0xF0,0xC9,0xEA,0xEA,0xEA,0xEA,0xEA])
    return W,len(spr)
