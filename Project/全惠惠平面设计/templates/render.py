import json, pathlib, hashlib, argparse
from PIL import Image, ImageDraw, ImageFont, ImageCms
import pypdfium2 as pdfium
from collections import Counter
ROOT=pathlib.Path(__file__).resolve().parent
FONT=r'C:\Windows\Fonts\NotoSansSC-VF.ttf'
SOURCE=r'E:\260930_全惠惠工作合集\261012_平面设计合集\设计资料\全惠惠logo(1).pdf'
S=2
RED='#B00D15'; BLACK='#231F20'; WHITE='#FFFFFF'
def font(size, weight=600):
    f=ImageFont.truetype(FONT,round(size*S)); f.set_variation_by_axes([weight]); return f

def render(item,out,logo):
    RED=item.get('red','#B00D15'); BLACK=item.get('black','#231F20'); WHITE=item.get('white','#FFFFFF')
    im=Image.new('RGB',(1080*S,1080*S),WHITE); d=ImageDraw.Draw(im)
    def rect(box,c): d.rectangle(tuple(round(v*S) for v in box),fill=c)
    def line(points,c,w=1): d.line([(int(x*S),int(y*S)) for x,y in points],fill=c,width=w*S)
    def ellipse(box,c,outline=None,w=1): d.ellipse(tuple(int(v*S) for v in box),fill=c,outline=outline,width=w*S)
    def text(x,y,t,size=40,color=BLACK,weight=600):
        f=font(size,weight); b=d.textbbox((x*S,y*S),t,font=f,anchor='lt')
        assert b[2]<=1080*S and b[3]<=1080*S, (t,b)
        d.text((x*S,y*S),t,font=f,fill=color,anchor='lt')
    # Intact original logo, consistent size and clear space.
    l=logo.resize((300*S,round(300*logo.height/logo.width)*S),Image.Resampling.LANCZOS)
    im.paste(l,(72*S,60*S),l)
    text(810,76,item['greeting'],42,RED,650)
    text(810,135,item['issue'],23,BLACK,500)
    line([(72,212),(1008,212)],BLACK,2)
    mode=item['slot']
    if mode=='早':
        text(72,263,item['eyebrow'],30,RED)
        for i,t in enumerate(item['title']): text(68,331+i*116,t,96,BLACK,750)
        rect((74,600,148,608),RED)
        for i,t in enumerate(item['body']): text(72,645+i*61,t,42,BLACK,550)
        # Rising circle and steps, geometric brand motif.
        ellipse((784,437,1000,653),RED)
        rect((760,580,1020,680),WHITE)
        for i in range(4):
            x=730+i*68; y=841-i*51
            rect((x,y,x+52,950),RED)
        text(72,841,'全心全意聚商机',34,RED)
        text(72,894,'互惠互利赢未来',34,BLACK)
    elif mode=='中':
        text(72,263,item['eyebrow'],30,RED)
        for i,t in enumerate(item['title']): text(68,331+i*110,t,88,BLACK,750)
        rect((72,595,1008,918),RED)
        for i,t in enumerate(item['body']):
            y=647+i*78
            text(108,y,f'0{i+1}',30,WHITE,500)
            text(188,y-4,t,44,WHITE,650)
    else:
        rect((0,245,1080,938),BLACK)
        text(72,289,item['eyebrow'],30,WHITE)
        for i,t in enumerate(item['title']): text(68,366+i*116,t,96,WHITE,750)
        rect((74,626,148,634),RED)
        for i,t in enumerate(item['body']): text(72,682+i*66,t,42,WHITE,550)
        # Open rectangular frame: steady, architectural geometry.
        line([(782,812),(956,812),(956,626)],RED,12)
    line([(72,982),(1008,982)],BLACK,1)
    text(72,1011,item.get('footer','全惠惠 · 品牌理念'),25,BLACK,600)
    text(807,1011,item['date'],25,BLACK,500)
    im=im.resize((1080,1080),Image.Resampling.LANCZOS)
    name=f"{item['date'].replace('.','')}-{mode}-{item['keyword']}"
    p=out/(name+'.png')
    icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    im.save(p,icc_profile=icc,optimize=True)
    assert p.stat().st_size<2*1024*1024
    (out/(name+'.txt')).write_text(item['caption']+'\n',encoding='utf-8-sig')
    return {'file':p.name,'size':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    a=argparse.ArgumentParser(); a.add_argument('--content',default=str(ROOT/'content.json')); a.add_argument('--out',default=str(ROOT/'20261012')); args=a.parse_args()
    out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    data=json.loads(pathlib.Path(args.content).read_text(encoding='utf-8-sig'))
    rules=json.loads((ROOT/'copy-rules.json').read_text(encoding='utf-8-sig'))
    for item in data:
        text=' '.join([*item['title'],*item['body'],item['caption'],item['eyebrow']])
        hits=[w for w in rules['blocked'] if w in text]
        if hits: raise ValueError(f"文案待修正：{hits}")
        if '权益' in text and not all(w in text for w in ['本人','后续消费抵扣','不可提现','不可变现','不可转让']): raise ValueError('权益限制说明不完整')
    doc=pdfium.PdfDocument(SOURCE)
    logo=doc[0].render(scale=4,fill_color=(0,0,0,0)).to_pil(); bounds=logo.getbbox(); logo=logo.crop(bounds)
    assets=ROOT/'assets'; assets.mkdir(exist_ok=True); logo.save(assets/'logo-original-render.png')
    records=[render(item,out,logo) for item in data]
    preview=Image.new('RGB',(1080,360),'white')
    for n,r in enumerate(records): preview.paste(Image.open(out/r['file']).resize((360,360),Image.Resampling.LANCZOS),(n*360,0))
    preview.save(out/'三图预览.jpg',quality=95)
    report={'logo_source':SOURCE,'logo_crop_at_4x':bounds,'logo_rgba_dominant':Counter(logo.getdata()).most_common(3),'font':'Noto Sans SC variable 500/550/600/650/750','color':RED,'results':records,'checks':['all text bounds inside canvas','blocked words absent','each PNG 1080x1080 and under 2 MiB','sRGB ICC embedded'],'status':'开发自测，待独立复验'}
    (out/'自测记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()

