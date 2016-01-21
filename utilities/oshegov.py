# -*- coding: utf-8 -*-
import sys,os,codecs
if os.name=='nt':
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
import pickle
i=open("OZHEGOV-utf-8.TXT", "rb")
key_s=i.readline()
key_name={}
key_s=key_s.strip()
key_l=key_s.split(b"|")
for j,k in enumerate(key_l):
    key_name[k]=j
    key_name[j]=k.decode('utf-8')

ozh={}
n=20
for l in i:
    l=l.strip().decode('utf-8')
    vals=l.split("|")
    word=vals[0]
    #if n<=0:
    #    break
    #n-=1
    w={}
    for j,v in enumerate(vals):
        v=v
        w[key_name[j]]=v
        w[j]=v
    ozh[word]=w

out=open("ozhegov.dic", "wb")
pickle.dump(ozh, out)

print ("привет1", len(ozh))
print (ozh['курица'])

ii=open("ozhegov.dic", "rb")
ozh=pickle.load(ii)
ozh['аббат']

import pymorphy2
import pprint

morph = pymorphy2.MorphAnalyzer()
rc=morph.parse('стали')
pprint.pprint(rc)


