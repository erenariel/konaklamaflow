"""Build three animated, fictional KonaklamaFlow README GIFs.

Inputs: the approved offline HTML snapshot from the AI dashboard PR.
Screenshots are captured entirely in Chromium; no vendor UI or real guest data.
Run with: python scripts/build_promo_gifs.py --html PATH --out docs/images
"""
from __future__ import annotations
import argparse
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

PALETTE = [(32, 222, 211), (139, 112, 253), (255, 188, 82), (255, 111, 157)]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def ft(size: int, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

def screen(page, selector):
    el = page.locator(selector).first
    el.scroll_into_view_if_needed()
    return Image.open(BytesIO(el.screenshot())).convert("RGB")

def bg(w, h):
    im = Image.new("RGB", (w, h))
    pix = im.load()
    for y in range(h):
        for x in range(w):
            pix[x, y] = (int(8 + 14*x/w), int(16 + 23*x/w + 4*y/h), int(36 + 29*x/w + 5*y/h))
    return im

def panel(image, snapshot, rect):
    x, y, w, h = rect
    res = snapshot.resize((w, h), Image.Resampling.LANCZOS)
    mask = Image.new("L", (w, h))
    ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1), radius=11, fill=255)
    image.paste(res, (x,y),mask)

def save(frames, path, interval=220):
    frames = [f.quantize(colors=96,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE) for f in frames]
    frames[0].save(path,save_all=True,append_images=frames[1:],
                   duration=[interval]*(len(frames)-1)+[720],loop=0,disposal=2,optimize=True)

def themed(snapshot_series, out, captions, shot_h):
    w=900;h=shot_h+137;frames=[]
    for i in range(15):
        group=i//3;accent=PALETTE[group%4]
        canvas=bg(w,h);d=ImageDraw.Draw(canvas)
        d.rounded_rectangle((13,12,w-13,h-13),radius=22,outline=(60,116,149),width=2)
        d.rounded_rectangle((29,24,38,49),radius=3,fill=accent)
        d.text((52,21),"KONAKLAMAFLOW / AI OPERATIONS",font=ft(20,True),fill=(243,250,255))
        d.text((w-201,28),"OFFLINE  •  DEMO",font=ft(11,True),fill=(152,204,214))
        d.text((31,57),captions[group],font=ft(13,True),fill=(184,229,237))
        d.rounded_rectangle((30,89,w-30,94),radius=3,fill=(43,70,95))
        d.rounded_rectangle((30,89,30+int((w-60)*(i+1)/15),94),radius=3,fill=accent)
        panel(canvas,snapshot_series[group],(31,105,w-62,shot_h-6))
        d=ImageDraw.Draw(canvas)
        yy=108+(i%3)*18
        d.line((39,yy,w-39,yy),fill=accent,width=2)
        d.text((31,h-35),"SENTETIK VERI  •  GERCEK OTEL ISLEMI YAPILMAZ",font=ft(11,True),fill=(166,198,215))
        for j in range(5):
            x=w-142+j*23
            d.ellipse((x,h-34,x+10,h-24),fill=PALETTE[j%4] if j==group else (70,90,117))
        frames.append(canvas)
    save(frames,out)

def overview(snapshot,out):
    w=940;h=540;frames=[]
    labels=("01  ›  KAYNAK","02  ›  KURAL","03  ›  ACIKLAMA","04  ›  PERSONEL")
    for i in range(20):
        canvas=bg(w,h);d=ImageDraw.Draw(canvas);accent=PALETTE[(i//5)%4]
        d.rounded_rectangle((17,13,w-17,h-13),radius=20,outline=(63,143,172),width=2)
        d.text((35,25),"KONAKLAMAFLOW",font=ft(26,True),fill=(246,251,255))
        d.text((35,62),"Otelin operasyonlari, aciklanabilir AI akisinda",font=ft(14),fill=(170,208,223))
        d.rounded_rectangle((w-207,26,w-35,55),radius=14,fill=(9,59,75),outline=(43,207,181))
        d.ellipse((w-195,36,w-186,45),fill=(26,228,189))
        d.text((w-176,33),"SENTETIK DEMO",font=ft(11,True),fill=(205,247,243))
        panel(canvas,snapshot,(35,94,w-70,326))
        d=ImageDraw.Draw(canvas)
        x=48+int((i%10)/9*(w-160))
        d.rounded_rectangle((x,101,x+82,105),radius=2,fill=accent)
        for j,label in enumerate(labels):
            d.text((35+210*j,h-91),label,font=ft(12,True),fill=PALETTE[j])
        d.rounded_rectangle((36,h-62,w-36,h-56),radius=3,fill=(41,77,100))
        d.rounded_rectangle((36,h-62,36+int((w-72)*(i+1)/20),h-56),radius=3,fill=accent)
        d.text((35,h-42),"Kurgusal sunum. PMS / OTA / KBS / canli AI baglantisi yok.",font=ft(11),fill=(174,201,218))
        frames.append(canvas)
    save(frames,out,interval=120)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--html",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("docs/images"))
    a=p.parse_args()
    html=a.html.read_text(encoding="utf-8")
    a.out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1440,"height":980},device_scale_factor=1)
        errors=[];requests=[]
        page.on("pageerror",lambda err:errors.append(str(err)))
        page.on("request",lambda req:requests.append(req.url))
        page.set_content(html,wait_until="domcontentloaded")
        page.locator("#commandReset").click()
        hero=[];rack=[]
        for i in range(5):
            if i: page.locator("#commandNext").click()
            hero.append(screen(page,"#aiCommandCenter"))
            rack.append(screen(page,".rack-panel"))
        page.locator("#commandReset").click()
        whole=screen(page,".main")
        browser.close()
        if errors or requests:raise RuntimeError("Offline capture generated browser errors or network requests: "+str(errors+requests))
    themed(hero,a.out/"ai-command-tour.gif",[
        "KAYNAK   Rezervasyon ve envanter","KURAL   Cakisma ve blokaj",
        "ACIKLAMA   AI senaryo anlatimi","KONTROL   Insan onayi gerekir",
        "SONUC   Guvenli inceleme"],355)
    themed(rack,a.out/"roomplan-story.gif",[
        "ODAK   Ilgili rezervasyonu sec","ODA PLANI   Kurgusal envanteri incele",
        "KANIT   Oda ve kaynak kontrolu","KARAR   Yetkili personel incelemesi",
        "IZ   Gerekceli denetim"],400)
    overview(whole,a.out/"overview-pulse.gif")
    for path in a.out.glob("*.gif"):print(path,path.stat().st_size,"bytes")

if __name__=="__main__":main()
