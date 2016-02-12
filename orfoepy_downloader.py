# encoding: utf-8
import csv
import pickle
import sys,os,codecs
import re
import pprint
import requests
if os.name=='nt':
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

PTEXT="""<a title="Орфографический словарь буква А" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-a.htm">А</a>
<a title="Орфографический словарь буква Б" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-b.htm">Б</a>
<a title="Орфографический словарь буква В" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-v.htm">В</a>
<a title="Орфографический словарь буква Г" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-g.htm">Г</a>
<a title="Орфографический словарь буква Д" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-d.htm">Д</a>
<a title="Орфографический словарь буква Е" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-e.htm">Е</a>
<a title="Орфографический словарь буква Ё" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-jo.htm">Ё</a>
<a title="Орфографический словарь буква Ж" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-zh.htm">Ж</a>
<a title="Орфографический словарь буква З" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-z.htm">З</a>
<a title="Орфографический словарь буква И" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-i.htm">И</a>
<a title="Орфографический словарь буква Й" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-j.htm">Й</a>
<a title="Орфографический словарь буква К" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-k.htm">К</a>
<a title="Орфографический словарь буква Л" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-l.htm">Л</a>
<a title="Орфографический словарь буква М" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-m.htm">М</a>
<a title="Орфографический словарь буква Н" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-n.htm">Н</a>
<a title="Орфографический словарь буква О" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-o.htm">О</a>
<a title="Орфографический словарь буква П" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-p.htm">П</a>
<a title="Орфографический словарь буква Р" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-r.htm">Р</a>
<a title="Орфографический словарь буква С" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-s.htm">С</a>
<a title="Орфографический словарь буква Т" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-t.htm">Т</a>
<a title="Орфографический словарь буква У" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-y.htm">У</a>
<a title="Орфографический словарь буква Ф" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-f.htm">Ф</a>
<a title="Орфографический словарь буква Х" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-x.htm">Х</a>
<a title="Орфографический словарь буква Ц" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-cs.htm">Ц</a>
<a title="Орфографический словарь буква Ч" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-ch.htm">Ч</a>
<a title="Орфографический словарь буква Ш" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-sh.htm">Ш</a>
<a title="Орфографический словарь буква Щ" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-sch.htm">Щ</a>
<a title="Орфографический словарь буква Ы" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-ji.htm">Ъ Ы Ь</a>
<a title="Орфографический словарь буква Э" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-je.htm">Э</a>
<a title="Орфографический словарь буква Ю" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-jy.htm">Ю</a>
<a title="Орфографический словарь буква Я" href="http://dazor.narod.ru/russkie/slovari/orfograficheskij/orfograficheskij-slovar-ja.htm">Я</a>"""

ENC='cp1251'

_mark=object()

d={}

def load_url(url):
    print (url)
    rq=requests.get(url)
    c=rq.content.decode("utf-8")
    start=c.find('<!--***. ****************** LETTER')
    stop =c.find('<!--***. ****************** /////// LETTER')
    for l in c[start:stop].split("\n"):
        if not l.startswith("<BIG>"):
            continue
        l=l.strip()
        l=l.split("<BIG>")[1].split("</BIG>")[0]
        ls=l.lower().split("<b>")
        ls=[l2.split('</b>') for l2 in ls]
        sts=[]
        pos=0
        w=''
        for p in ls:
            if len(p)==1:
                pos+=len(p[0])
                w+=p[0]
            else:
                sts.append(pos)
                pos+=len(p[0])+len(p[1])
                w+=p[0]+p[1]
        d[w]=sts

for l in PTEXT.split("\n"):
    l=l.split('href="')[1]
    l=l.split('">')[0]
    load_url(l)

o=open('data/stress.dic', 'wb')
pickle.dump(d,o)
print (len(d))
o.close()

