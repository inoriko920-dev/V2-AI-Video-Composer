from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import zipfile, textwrap, hashlib, json

SOURCE=Path('/mnt/data/step03_r_ui_source/UI-013_ACTUAL.png')
OUT=Path('/mnt/data/V2_AI_Video_Composer_STEP03_R_UI_DRAFT_REVIEW')
OUT.mkdir(parents=True,exist_ok=True)
BASE=Image.open(SOURCE).convert('RGBA')
assert BASE.size==(1920,1080)
FONT_DIR='/usr/share/fonts/opentype/inter'
FONTS={'r':'Inter-Regular.otf','m':'Inter-Medium.otf','sb':'Inter-SemiBold.otf','b':'Inter-Bold.otf'}
def font(size,style='r'):
    return ImageFont.truetype(f'{FONT_DIR}/{FONTS[style]}',size)
C={'ink':'#1D293A','sub':'#475569','muted':'#64748B','border':'#D8E0EA','blue':'#2563EB','blue2':'#E8F1FF','blueDark':'#1E40AF','bg':'#FFFFFF','panel':'#F8FAFC','warn':'#AA6C0B','warn_bg':'#FFF8E8','warn_border':'#F2D79B','error':'#B34339','error_bg':'#FFF6F5','error_border':'#F6C9C4'}
def txt(d,xy,text,size=16,color=None,style='r'):
    d.text(xy,text,fill=color or C['ink'],font=font(size,style))
def lines(d,x,y,ls,size=16,color=None,style='r',leading=10):
    for line in ls:
        txt(d,(x,y),line,size,color,style)
        y+=size+leading
    return y

def rr(d, box, radius=10, fill='white', outline=None,width=1):
    d.rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=width)

def button(d,x,y,w,label,kind='line',size=15,h=44):
    if kind=='solid':
        fill=C['blue']; border=C['blue']; fg='#FFFFFF'; width=1
    elif kind=='warning':
        fill=C['warn_bg'];border='#D69E43';fg='#804B05';width=1
    elif kind=='focus':
        fill='#FFFFFF';border=C['blue'];fg=C['ink'];width=2
    else:
        fill='#FFFFFF';border='#CAD4E1';fg=C['ink'];width=1
    rr(d,(x,y,x+w,y+h),7,fill,border,width)
    b=d.textbbox((0,0),label,font=font(size,'m'))
    tw=b[2]-b[0];th=b[3]-b[1]
    txt(d,(int(x+(w-tw)/2), int(y+(h-th)/2-b[1])),label,size,fg,'m')

def shadowed(base,x,y,w,h):
    sh=Image.new('RGBA',base.size,(0,0,0,0))
    ds=ImageDraw.Draw(sh)
    ds.rounded_rectangle((x+1,y+8,x+w+1,y+h+8),radius=13,fill=(26,44,72,108))
    sh=sh.filter(ImageFilter.GaussianBlur(22))
    base.alpha_composite(sh)

def build(which):
    im=BASE.copy()
    # Absolutely preserve the true editor screenshot as source; only add translucent modal mask + dialog.
    veil=Image.new('RGBA',im.size,(18,32,54,47))
    im.alpha_composite(veil)
    if which==1: x,y,w,h=625,266,670,525
    elif which==2: x,y,w,h=625,266,670,525
    else: x,y,w,h=640,323,640,415
    shadowed(im,x,y,w,h)
    layer=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(layer)
    rr(d,(x,y,x+w,y+h),14,C['bg'],C['border'],1)
    pad=29
    if which==1:
        # Native dialog icon + header
        d.ellipse((x+pad,y+28,x+pad+33,y+61),fill=C['blue2'],outline='#B9D5FF')
        txt(d,(x+pad+11,y+35),'↻',22,C['blue'],'sb')
        txt(d,(x+pad+46,y+28),'Cadangan Proyek Ditemukan',22,C['ink'],'sb')
        d.line((x,y+88,x+w,y+88),fill=C['border'],width=1)
        lines(d,x+pad,y+112,['Ada perubahan proyek yang ditemukan dalam cadangan otomatis.'],15,C['sub'])
        rr(d,(x+pad,y+156,x+w-pad,y+202),8,C['panel'],C['border'])
        txt(d,(x+pad+15,y+171),'Proyek Dokumenter Suez.aavcproj',15,C['ink'],'m')
        # faithful no invented timestamps
        rr(d,(x+pad,y+218,x+w-pad,y+279),8,'#FFFFFF',C['border'])
        d.rectangle((x+pad+1,y+219,x+pad+4,y+278),fill='#97AAC5')
        txt(d,(x+pad+15,y+230),'Proyek tersimpan',15,C['ink'],'sb')
        txt(d,(x+pad+15,y+254),'Versi terakhir yang Anda simpan secara manual',14,C['sub'])
        rr(d,(x+pad,y+290,x+w-pad,y+351),8,'#FFFFFF',C['border'])
        d.rectangle((x+pad+1,y+291,x+pad+4,y+350),fill='#548DF0')
        txt(d,(x+pad+15,y+302),'Cadangan otomatis',15,C['ink'],'sb')
        txt(d,(x+pad+15,y+326),'Perubahan yang belum disimpan manual',14,C['sub'])
        rr(d,(x+pad,y+365,x+w-pad,y+417),8,'#EDF5FF','#CCE0FF')
        txt(d,(x+pad+14,y+383),'Jika dipulihkan, salinan proyek tersimpan dibuat terlebih dahulu.',14,C['blueDark'],'m')
        d.line((x,y+438,x+w,y+438),fill=C['border'],width=1)
        button(d,x+pad,y+457,172,'Pulihkan Cadangan','solid',14)
        button(d,x+pad+181,y+457,235,'Gunakan Proyek Tersimpan','line',14)
        button(d,x+w-pad-101,y+457,101,'Batal','focus',14)
    elif which==2:
        # Native dialog warning, without 'verified' icon/claims
        d.polygon([(x+pad+16,y+27),(x+pad+34,y+60),(x+pad-2,y+60)],fill='#F1B34C')
        txt(d,(x+pad+12,y+33),'!',19,'#5E3F0B','b')
        txt(d,(x+pad+46,y+28),'Cadangan Perlu Diperiksa',22,C['ink'],'sb')
        d.line((x,y+88,x+w,y+88),fill=C['border'],width=1)
        lines(d,x+pad,y+115,['Versi proyek tersimpan mungkin berbeda dari versi','saat cadangan dibuat.'],16,C['sub'],leading=9)
        rr(d,(x+pad,y+188,x+w-pad,y+279),9,C['warn_bg'],C['warn_border'])
        txt(d,(x+pad+15,y+204),'Perlu konfirmasi sebelum pemulihan',15,'#82540C','sb')
        lines(d,x+pad+15,y+232,['Pemulihan hanya dilakukan setelah Anda menyetujuinya.','Proyek tersimpan akan dicadangkan terlebih dahulu.'],14,'#855D1C',leading=8)
        txt(d,(x+pad,y+312),'Pilihan yang aman',15,C['ink'],'sb')
        lines(d,x+pad,y+344,['Tinjau cadangan sebelum menggunakannya. Jika ada perubahan','baru pada proyek tersimpan, Anda akan diminta konfirmasi lagi.'],14,C['sub'],leading=10)
        d.line((x,y+438,x+w,y+438),fill=C['border'],width=1)
        button(d,x+pad,y+457,175,'Periksa dan Pulihkan','warning',14)
        button(d,x+pad+184,y+457,235,'Gunakan Proyek Tersimpan','line',14)
        button(d,x+w-pad-101,y+457,101,'Batal','focus',14)
    else:
        # Native QMessageBox-style modal; no destructive controls
        d.ellipse((x+pad,y+27,x+pad+34,y+61),fill=C['error_bg'],outline=C['error_border'])
        txt(d,(x+pad+12,y+33),'×',22,C['error'],'sb')
        txt(d,(x+pad+46,y+29),'Cadangan Tidak Dapat Dibaca',21,C['ink'],'sb')
        d.line((x,y+86,x+w,y+86),fill=C['border'],width=1)
        lines(d,x+pad,y+112,['Cadangan otomatis tidak dapat dibuka dengan aman.','File proyek tersimpan tidak diubah.'],16,C['sub'],leading=11)
        rr(d,(x+pad,y+194,x+w-pad,y+266),9,C['panel'],C['border'])
        txt(d,(x+pad+15,y+211),'File cadangan tetap disimpan untuk pemeriksaan.',15,C['ink'],'m')
        txt(d,(x+pad+15,y+241),'Tidak ada cadangan yang dihapus otomatis.',14,C['sub'])
        # no restore button
        d.line((x,y+321,x+w,y+321),fill=C['border'],width=1)
        button(d,x+w-pad-348,y+343,236,'Buka Proyek Tersimpan','line',14)
        button(d,x+w-pad-101,y+343,101,'Batal','focus',14)
    im.alpha_composite(layer)
    im=im.convert('RGB')
    filename=f'UI-REC-DLG-0{which}.png'
    dest=OUT/filename
    im.save(dest,optimize=True)
    return dest

files=[build(i) for i in [1,2,3]]
readme='''V2-AI-VIDEO-COMPOSER — STEP 03-R — DRAFT REFERENSI UI UNTUK DITINJAU\n\nStatus: DRAFT / BELUM DISETUJUI. Tidak ada implementasi Qt, perubahan kode, atau pembaruan repository.\n\nAcuan: Screenshot asli UI-013_ACTUAL.png (GitHub Actions STEP09, run 37734080472).\nResolusi setiap gambar: 1920 x 1080 piksel.\n\nUI-REC-DLG-01.png  : Cadangan proyek ditemukan (normal).\nUI-REC-DLG-02.png  : Cadangan perlu diperiksa (konflik).\nUI-REC-DLG-03.png  : Cadangan tidak dapat dibaca (aman).\n\nKetiganya hanya menambahkan modal ke screenshot asli; editor utama tidak dirancang ulang.\nTombol Batal difokuskan sebagai default aman.\nDalam konflik, pemulihan membutuhkan dialog konfirmasi kedua dengan komponen yang sama;\nrevisi ini tidak menambah referensi gambar keempat.\n\nHarus ditinjau dan disetujui pengguna sebelum pembuatan satu DOCX final berisi gambar-gambar UI.\nSTEP04 hingga STEP06 dan coding v0.3.0 tetap terlarang sebelum gate PASS.\n'''
(OUT/'README_DRAFT_UI_REVIEW.txt').write_text(readme,encoding='utf-8')
(OUT/'UI-013_ACTUAL_REFERENCE.png').write_bytes(SOURCE.read_bytes())
zip_path=Path('/mnt/data/V2_AI_Video_Composer_STEP03_R_TIGA_DIALOG_DRAFT_REVIEW.zip')
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for path in sorted(OUT.iterdir()): z.write(path,path.name)
print('Original SHA256:',hashlib.sha256(SOURCE.read_bytes()).hexdigest())
for p in files:
    with Image.open(p) as img: print(p, img.size, p.stat().st_size)
print(zip_path,zip_path.stat().st_size)