import numpy as np
import sys
ROM=sys.argv[1] if len(sys.argv)>1 else 'Rudra no Hihou (Japan).sfc'
FONT=0x1e7f80
def dec(b):
    m=np.zeros((12,16),np.uint8)
    for r in range(12):
        L=b[(0 if r<6 else 12)+r%6]; R=b[(6 if r<6 else 18)+r%6]
        w=L<<8|R
        for x in range(16): m[r,x]=(w>>(15-x))&1
    return m
def enc(m):
    o=bytearray(24)
    for r in range(12):
        L=R=0
        for x in range(8): L|=int(m[r,x])<<(7-x); R|=int(m[r,x+8])<<(7-x)
        o[(0 if r<6 else 12)+r%6]=L; o[(6 if r<6 else 18)+r%6]=R
    return bytes(o)
if __name__=='__main__':
    from PIL import Image
    d=open(ROM,'rb').read()
    n=1600; cols=32
    im=np.zeros(((n//cols)*14,cols*17),np.uint8)
    for i in range(n):
        im[(i//cols)*14:(i//cols)*14+12,(i%cols)*17:(i%cols)*17+16]=dec(d[FONT+i*24:FONT+i*24+24])*255
    Image.fromarray(im).save('fontall.png')
    print(im.shape)
