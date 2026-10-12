from pathlib import Path
import json, hashlib
from PIL import Image,ImageDraw,ImageFont,ImageCms
P=Path(__file__).resolve().parent
FONT=r'C:\Windows\Fonts\NotoSansSC-VF.ttf'
S=2
items=json.loads((P/'内容.json').read_text(encoding='utf-8-sig'))
logo=Image.open(P.parent/'assets'/'logo-original-render.png').convert('RGBA')
def font(sz,w=800):
 f=ImageFont.truetype(FONT,sz*S);f.set_variation_by_axes([w]);return f
records=[]
for item in items:
 im=Image.open(P/'背景'/f"{item['slot']}.png").convert('RGB').resize((2160,2160),Image.Resampling.LANCZOS)
 d=ImageDraw.Draw(im)
 # Original brand logo on a generous white plaque, no redraw.
 d.rounded_rectangle((350*S,30*S,730*S,194*S),radius=12*S,fill='white')
 lw=286*S; lh=round(lw*logo.height/logo.width)
 mark=logo.resize((lw,lh),Image.Resampling.LANCZOS);im.paste(mark,((2160-lw)//2,64*S),mark)
 def center(t,y,sz,color,weight=800,stroke=0,shadow=False):
  f=font(sz,weight);width=d.textlength(t,font=f);x=(2160-width)/2
  assert x>=55*S,(t,x)
  if shadow:
   for dy in range(7*S,0,-2):d.text((x+dy*.35,y*S+dy),t,font=f,fill='#681008',anchor='lt',stroke_width=stroke*S,stroke_fill='#681008')
  d.text((x,y*S),t,font=f,fill=color,anchor='lt',stroke_width=stroke*S,stroke_fill='#FFE7A5')
 center(item['greeting'],218,130,'#FFF6D5',900,1,True)
 for j,t in enumerate(item['title']):center(t,386+j*120,104,'#FFE29A',900,1,True)
 d.rounded_rectangle((155*S,641*S,925*S,716*S),radius=38*S,fill='#8F0711',outline='#EFC375',width=2*S)
 center(item['sub'],657,41,'#FFF7E0',650)
 # Evergreen brand line only. No date, issue, schedule, urgency or countdown.
 d.rectangle((0,1011*S,2160,2160),fill='#870812')
 center('全心全意聚商机  互惠互利赢未来',1026,31,'#FFF0CC',650)
 im=im.resize((1080,1080),Image.Resampling.LANCZOS)
 fn=P/(item['name']+'.png')
 im.save(fn,optimize=True,icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
 assert fn.stat().st_size<2*1024*1024
 (P/(item['name']+'-配文.txt')).write_text(item['caption']+'\n',encoding='utf-8-sig')
 records.append({'file':fn.name,'bytes':fn.stat().st_size,'sha256':hashlib.sha256(fn.read_bytes()).hexdigest()})
preview=Image.new('RGB',(1500,500))
for i,r in enumerate(records):preview.paste(Image.open(P/r['file']).resize((500,500),Image.Resampling.LANCZOS),(500*i,0))
preview.save(P/'三图预览-v2.jpg',quality=95)
(P/'自测记录.json').write_text(json.dumps({'size':[1080,1080],'date_on_image':False,'issue_on_image':False,'style':'用户要求的热烈群发宣传风格','method':'内置 imagegen 无字背景 + 原 Logo 与确定性文字叠加','files':records,'review':'待视觉检查'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(records,ensure_ascii=False))
