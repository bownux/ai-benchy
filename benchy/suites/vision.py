"""VISION suite — 27 judge-free tasks on SYNTHETIC images rendered here with Pillow.

Because we draw every image from code, the ground truth is exact and the whole suite
is reproducible on any machine (no datasets to download, nothing to license). Tiers:
CORE (13, legible) and HARD (14: dense/rotated/small-print OCR, high-count and
2-attribute counting, chart value-reading, relational spatial, table lookup/sum,
reading comprehension) — the HARD tier is what separates VLMs.

Needs a multimodal endpoint that accepts OpenAI image_url content parts.
Set VL_SAVE_IMAGES=/some/dir to dump the rendered PNGs and eyeball the ground truth.
"""
from __future__ import annotations
import base64, io, json, os, re
from . import Suite, Task, register

try:
    from PIL import Image, ImageDraw, ImageFont
    _HAVE_PIL = True
except Exception:
    _HAVE_PIL = False

SAVE = os.environ.get("VL_SAVE_IMAGES")

def _font(sz, bold=True):
    for p in (f"/usr/share/fonts/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
              f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
              "/Library/Fonts/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

COLORS = {"red": (215, 25, 25), "blue": (30, 60, 220), "green": (20, 150, 40),
          "yellow": (235, 195, 20), "purple": (150, 40, 190), "orange": (240, 135, 20)}

def _b64(img): buf = io.BytesIO(); img.save(buf, "PNG"); return base64.b64encode(buf.getvalue()).decode()
def _canvas(w=560, h=360, bg="white"): img = Image.new("RGB", (w, h), bg); return img, ImageDraw.Draw(img)
def _sh(d, kind, box, fill):
    x0, y0, x1, y1 = box
    if kind == "circle":   d.ellipse(box, fill=fill)
    elif kind == "square": d.rectangle(box, fill=fill)
    else:                  d.polygon([((x0+x1)//2, y0), (x1, y1), (x0, y1)], fill=fill)

# ── image builders ───────────────────────────────────────────────────────────
def im_ocr_code():
    img,d=_canvas(560,160); d.text((24,55),"Order: QX7-4821-ZB",fill="black",font=_font(46)); return _b64(img)
def im_ocr_multiline():
    img,d=_canvas(560,220)
    for i,l in enumerate(["Name: Dana Holt","Total: $137.50","Status: SHIPPED"]): d.text((24,20+i*60),l,fill="black",font=_font(40))
    return _b64(img)
def im_count_circles():
    img,d=_canvas()
    for x,y in [(90,90),(250,90),(410,90),(90,230),(250,230),(410,230),(170,160)]: d.ellipse([x-32,y-32,x+32,y+32],fill="black")
    return _b64(img)
def im_count_red():
    img,d=_canvas()
    for c,x,y in [("red",70,90),("blue",230,90),("red",390,90),("blue",70,250),("red",230,250),("green",390,250),("red",490,170)]:
        d.ellipse([x-34,y-34,x+34,y+34],fill=COLORS[c])
    return _b64(img)
def im_largest():
    img,d=_canvas(); d.rectangle([40,120,140,220],fill=COLORS["blue"]); d.ellipse([220,60,460,300],fill=COLORS["green"]); d.rectangle([470,150,540,220],fill=COLORS["red"]); return _b64(img)
def im_shape():
    img,d=_canvas(360,320); d.polygon([(180,40),(320,280),(40,280)],fill=COLORS["purple"]); return _b64(img)
def im_spatial():
    img,d=_canvas(520,520); d.line([260,0,260,520],fill="black",width=2); d.line([0,260,520,260],fill="black",width=2)
    d.ellipse([70,70,190,190],fill=COLORS["red"]); d.rectangle([330,70,450,190],fill=COLORS["blue"])
    d.polygon([(130,330),(190,450),(70,450)],fill=COLORS["green"]); d.ellipse([330,330,450,450],fill=COLORS["orange"]); return _b64(img)
def im_bar():
    img,d=_canvas(560,380); f=_font(30); x=60
    for lab,h in {"A":80,"B":200,"C":130,"D":290}.items(): d.rectangle([x,320-h,x+90,320],fill=COLORS["blue"]); d.text((x+30,330),lab,fill="black",font=f); x+=120
    d.line([40,320,540,320],fill="black",width=3); return _b64(img)
def im_table():
    img,d=_canvas(520,260); f=_font(30); d.text((40,20),"Item",fill="black",font=f); d.text((340,20),"Qty",fill="black",font=f); d.line([30,60,490,60],fill="black",width=2)
    for i,(a,b) in enumerate([("Apples","12"),("Mangoes","5"),("Pears","9")]): d.text((40,80+i*55),a,fill="black",font=f); d.text((360,80+i*55),b,fill="black",font=f)
    return _b64(img)
def im_compare():
    img,d=_canvas(520,300); d.ellipse([60,90,180,210],fill=COLORS["red"]); d.ellipse([300,40,500,240],fill=COLORS["red"]); return _b64(img)
def im_grid():
    img,d=_canvas(360,360); f=_font(60); g=[["P","Q","R"],["S","K","T"],["U","V","W"]]
    for r in range(3):
        for c in range(3): d.text((50+c*110,30+r*110),g[r][c],fill="black",font=f)
    return _b64(img)
def im_confusable():
    img,d=_canvas(620,150); d.text((20,50),"RX80-9KQ4-7ZW2-J3H6",fill="black",font=_font(44)); return _b64(img)
def im_smallprint():
    img,d=_canvas(620,160)
    for i,l in enumerate(["Terms apply. See reverse for details.","Reference: 99XK-220841-Q8 (keep for your records)","Issued 2026 — non-transferable."]):
        d.text((20,30+i*40),l,fill="black",font=_font(20,bold=False))
    return _b64(img)
def im_rotated():
    sub=Image.new("RGB",(480,90),"white"); ImageDraw.Draw(sub).text((12,24),"PASSCODE 7741",fill="black",font=_font(40))
    sub=sub.rotate(13,expand=True,fillcolor="white"); img,_=_canvas(660,260); img.paste(sub,(70,60)); return _b64(img)
def im_paragraph():
    img,d=_canvas(620,240); f=_font(24,bold=False)
    for i,l in enumerate(["The old stone bridge spans the river near the","village. It was completed in 1932 by local","craftsmen, and today it carries the main road","and a footpath used by hikers each summer."]):
        d.text((24,24+i*48),l,fill="black",font=f)
    return _b64(img)
def im_math():
    img,d=_canvas(420,150); d.text((30,45),"63 + 19 = ?",fill="black",font=_font(54)); return _b64(img)
def im_count_many():
    img,d=_canvas(600,400)
    for x,y in [(80,70),(200,70),(320,70),(440,70),(540,70),(80,170),(200,170),(320,170),(440,170),(540,170),(80,270),(200,270),(320,270),(440,270),(540,270),(140,350),(380,350)]:
        d.ellipse([x-22,y-22,x+22,y+22],fill="black")
    return _b64(img)
def im_count_2attr():
    img,d=_canvas(600,460)
    cells=[("blue","triangle"),("red","circle"),("green","square"),("blue","circle"),("blue","triangle"),("yellow","square"),("red","triangle"),("blue","triangle"),("green","circle"),("blue","square"),("red","square"),("orange","triangle")]
    for i,(c,k) in enumerate(cells):
        cx,cy=90+(i%4)*140,80+(i//4)*140; _sh(d,k,[cx-45,cy-45,cx+45,cy+45],COLORS[c])
    return _b64(img)
def im_chart_labeled():
    img,d=_canvas(620,400); f=_font(26); x=50
    for lab,h in {"A":120,"B":180,"C":90,"D":210,"E":160}.items():
        d.rectangle([x,340-h,x+80,340],fill=COLORS["blue"]); d.text((x+18,345),lab,fill="black",font=f); d.text((x+6,340-h-30),str(h),fill="black",font=_font(22)); x+=110
    d.line([30,340,600,340],fill="black",width=3); return _b64(img)
def im_line():
    img,d=_canvas(560,360); pts=[(60,300),(160,250),(260,210),(360,140),(460,70)]
    d.line([40,330,520,330],fill="black",width=2); d.line([40,40,40,330],fill="black",width=2); d.line(pts,fill=COLORS["red"],width=5)
    for p in pts: d.ellipse([p[0]-5,p[1]-5,p[0]+5,p[1]+5],fill=COLORS["red"])
    return _b64(img)
def im_spatial_rel():
    img,d=_canvas(680,200)
    for i,(c,k) in enumerate([("green","square"),("red","circle"),("blue","triangle"),("yellow","square")]):
        cx=100+i*160; _sh(d,k,[cx-50,50,cx+50,150],COLORS[c])
    return _b64(img)
def im_table_lookup():
    img,d=_canvas(460,320); f=_font(28); d.text((40,20),"Fruit",fill="black",font=f); d.text((280,20),"Price",fill="black",font=f); d.line([30,60,430,60],fill="black",width=2)
    for i,(a,b) in enumerate([("Apple","$3"),("Mango","$7"),("Pear","$4"),("Plum","$6")]): d.text((40,80+i*55),a,fill="black",font=f); d.text((290,80+i*55),b,fill="black",font=f)
    return _b64(img)
def im_table_sum():
    img,d=_canvas(460,320); f=_font(28); d.text((40,20),"Item",fill="black",font=f); d.text((300,20),"Qty",fill="black",font=f); d.line([30,60,430,60],fill="black",width=2)
    for i,(a,b) in enumerate([("Bolts","14"),("Nuts","8"),("Washers","23"),("Screws","11")]): d.text((40,80+i*55),a,fill="black",font=f); d.text((310,80+i*55),b,fill="black",font=f)
    return _b64(img)
def im_odd():
    img,d=_canvas(680,160)
    for i in range(6): d.ellipse([70+i*110-40,40,70+i*110+40,120],fill=COLORS["red" if i==3 else "blue"])
    return _b64(img)

# ── scorers ──────────────────────────────────────────────────────────────────
def _norm(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())
def _has(a,*subs): n=_norm(a); return all(_norm(s) in n for s in subs)
def _ints(a): return [int(x) for x in re.findall(r"-?\d+", a or "")]
def _first(a,v): xs=_ints(a); return len(xs)>0 and xs[0]==v
def _any(a,v): return v in _ints(a)
def _json_rows(a,want):
    try:
        m=re.search(r"[\[{].*[\]}]",a,re.S); obj=json.loads(m.group()) if m else None
    except Exception: return False
    blob=_norm(json.dumps(obj)); return all(_norm(k) in blob and _norm(str(v)) in blob for k,v in want)

# (id, tier, builder, prompt, scorer)
_SPEC = [
    ("ocr_code","core",im_ocr_code,"What order code is shown? Reply with only the code.",lambda a:_has(a,"QX7-4821-ZB")),
    ("ocr_fields","core",im_ocr_multiline,"What is the Total shown? Reply with only the amount.",lambda a:_has(a,"137.50")),
    ("count_circles","core",im_count_circles,"How many black circles are in the image? Reply with only a number.",lambda a:_first(a,7)),
    ("count_red","core",im_count_red,"How many RED circles are in the image? Reply with only a number.",lambda a:_first(a,4)),
    ("largest_color","core",im_largest,"What color is the LARGEST shape? Reply with one word.",lambda a:_has(a,"green")),
    ("shape_id","core",im_shape,"What single shape is shown? Reply with one word.",lambda a:_has(a,"triangle")),
    ("spatial","core",im_spatial,"What color is the shape in the TOP-LEFT quadrant? Reply with one word.",lambda a:_has(a,"red")),
    ("spatial_shape","core",im_spatial,"What shape is in the BOTTOM-LEFT quadrant? Reply with one word.",lambda a:_has(a,"triangle")),
    ("chart_max","core",im_bar,"Which labeled bar is the TALLEST? Reply with only the letter.",lambda a:_norm(a)=="d" or _has(a,"bard")),
    ("chart_min","core",im_bar,"Which labeled bar is the SHORTEST? Reply with only the letter.",lambda a:_norm(a)=="a" or _has(a,"bara")),
    ("table_json","core",im_table,"Extract the table as a JSON object mapping each item to its quantity (numbers).",lambda a:_json_rows(a,[("Apples",12),("Mangoes",5),("Pears",9)])),
    ("compare_size","core",im_compare,"Which circle is bigger, the left one or the right one? Reply 'left' or 'right'.",lambda a:_has(a,"right")),
    ("grid_center","core",im_grid,"What letter is in the CENTER cell of the 3x3 grid? Reply with one letter.",lambda a:_norm(a)=="k"),
    ("ocr_confusable","hard",im_confusable,"Read the full code exactly. Reply with only the code.",lambda a:_has(a,"RX80-9KQ4-7ZW2-J3H6")),
    ("ocr_smallprint","hard",im_smallprint,"What is the reference number? Reply with only the reference.",lambda a:_has(a,"99XK-220841-Q8")),
    ("ocr_rotated","hard",im_rotated,"What is the 4-digit passcode shown? Reply with only the number.",lambda a:_any(a,7741)),
    ("ocr_reading","hard",im_paragraph,"In what year was the bridge completed? Reply with only the year.",lambda a:_any(a,1932)),
    ("ocr_math","hard",im_math,"Compute the sum shown in the image. Reply with only the number.",lambda a:_any(a,82)),
    ("count_many","hard",im_count_many,"Count the black circles. Reply with only a number.",lambda a:_first(a,17)),
    ("count_2attr","hard",im_count_2attr,"How many BLUE TRIANGLES are in the image? Reply with only a number.",lambda a:_first(a,3)),
    ("chart_threshold","hard",im_chart_labeled,"Each bar is labeled with its value. How many bars have a value greater than 150? Reply with only a number.",lambda a:_first(a,3)),
    ("chart_diff","hard",im_chart_labeled,"Each bar is labeled with its value. What is the difference between the highest and lowest bar values? Reply with only a number.",lambda a:_any(a,120)),
    ("line_trend","hard",im_line,"Overall from left to right, is the line increasing or decreasing? Reply with one word.",lambda a:_has(a,"increas")),
    ("spatial_relative","hard",im_spatial_rel,"What COLOR is the shape immediately to the RIGHT of the green square? Reply with one word.",lambda a:_has(a,"red")),
    ("table_cell","hard",im_table_lookup,"What is the price of Mango? Reply with only the price.",lambda a:_has(a,"7")),
    ("table_sum","hard",im_table_sum,"What is the sum of all values in the Qty column? Reply with only a number.",lambda a:_any(a,56)),
    ("odd_one_out","hard",im_odd,"All circles are blue except one. Counting from the left starting at 1, what is the position of the non-blue circle? Reply with only a number.",lambda a:_first(a,4)),
]


def _make(builder, prompt, scorer, tid):
    def run(client):
        if not _HAVE_PIL:
            return (0.0, "Pillow not installed (pip install pillow)")
        b64 = builder()
        if SAVE:
            os.makedirs(SAVE, exist_ok=True); open(os.path.join(SAVE, f"{tid}.png"), "wb").write(base64.b64decode(b64))
        r = client.chat([{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}], max_tokens=160)
        return (1.0 if scorer(r.content) else 0.0, f"ans={r.content.strip()[:50]!r}")
    return run


SUITE = register(Suite(
    name="vision", version="1", needs="vision",
    blurb="27 synthetic-image tasks (CORE 13 + HARD 14): OCR, counting, charts, spatial, tables.",
    tasks=[Task(tid, tier, _make(b, p, s, tid)) for tid, tier, b, p, s in _SPEC],
))
