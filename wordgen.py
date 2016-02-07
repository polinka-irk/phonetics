# encoding: utf-8
import csv
import pickle
import sys,os,codecs
import re
import pprint
import requests
if os.name=='nt':
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


ENC='cp1251'

_mark=object()

class Mistaker(object):
	"""Generates mistake words from an agument
	"""
	__export__=set()

	def __init__(self, d=_mark, **kwargs):
		"""
		"""
		if d==_mark:
			self.d={}
		else:
			self.d=d
		self.s=list(self.d.items())
		self.l=len(self.s)
		self.sup=None
		self.opts=kwargs
		for k,v in kwargs.items():
			if k in self.__class__.__export__:
				setattr(self, k,v)

	def set_sup(self, sup):
		self.sup=sup

	def run_sup(self, w):
		if self.sup == None:
			return
		else:
			yield from self.sup.gen(w)

	def chk_opt(self, name):
		if name in self.opts:
			return self.opts[name]
		else:
			return False

	def done(self):
		pass

	def gen(self, w, sq_no=0, sidx=0):
		if sq_no>=self.l:
			yield from self.gen_sup_gen(w, False)
		else:
			s,t=self.s[sq_no]
			idx=w.find(s,sidx)
			if idx>=0 and self.cond(w, idx, key=s):
				tw=w[sidx:]
				hw=w[:sidx]
				i=idx-sidx
				ntw=tw.replace(s,t,1)
				nw=hw+ntw
				yield nw
				yield from self.gen(w, sq_no, idx+1)
				yield from self.gen_sup_gen(nw, True)
			else:
				yield from self.gen(w, sq_no+1)

	def cond(self, w, idx, key):
		if self.chk_opt("no_end"):
			return idx<len(w)-1
		else:
			return True

	def gen_sup_gen(self, w, gen_self=True):
		if gen_self:
			yield from self.gen(w)
		if self.sup == None:
			return
		else:
			yield from self.sup.gen(w)

	def done_all(self):
		if self.sup != None:
			self.sup.done_all()
		self.done()

	def as_set(self, w, debug=False):
		"""
		"""
		rc=set()
		for w in self.gen(w):
			w=w.replace("_","")
			if debug:
				rc.add((w,self.__class__.__name__))
			else:
				rc.add(w)
		return rc

	def __call__(self, *args, **kwargs):
		return self.gen(*args, **kwargs)

class HTTPMistaker (Mistaker):
	def __init__(self, url):
		Mistaker.__init__(self)
		self.url=url

	def gen_mistakes(self, w):
		req=requests.get(self.url, params = {'words' : w.encode('cp1251')})
		text=req.content.decode('cp1251')
		t1=text.split("</textarea>")[0].split('rows="20">')[-1]
		for l in t1.split("\n"):
			yield l.strip()

	def gen(self, w):
		yield from self.gen_mistakes(w)
		yield from self.gen_sup_gen(w, False)

class CacheMistaker(Mistaker):
	def __init__(self, name):
		Mistaker.__init__(self)
		self.name=name
		self.c={}
		self.miss=False
		self.fname=self.name+".cache"
		self.init()

	def init(self):
		try:
			self.c=pickle.load(open(self.fname,"rb"))
		except IOError:
			self.c={}

	def done(self):
		if self.miss:
			f=open(self.fname,"wb")
			pickle.dump(self.c, f)
			f.flush()
			f.close()
			self.miss=False

	def __del__(self):
		self.done()

	def gen(self, w):
		if w in self.c:
			vals=self.c[w]
			for v in vals:
				yield v
		else:
			self.miss=True
			vals=[]
			for v in self.gen_sup_gen(w, False):
				vals.append(v)
				yield v
			self.c[w]=vals


class REMistaker (Mistaker):
	__export__=("expr")
	vovels="уеёыаоэяию"
	th="яеёюиь"
	consonants="бвгджзклмнпрстфхцчшщж"
	regexp="[{c}]([{d}])[{c}][{t}]"
	def __init__(self, d=_mark, **kwargs):
		Mistaker.__init__(self, d=d, **kwargs)
		res=self.__class__.regexp
		if type(res) != type([]):
			res=[res]
		self.exprs=[]
		for regexp in res:
			fregexp=regexp.format(
					c=self.__class__.consonants,
					d=''.join(self.d.keys()),
					t=self.__class__.th,
					v=self.__class__.vovels
				)
			cregexpr=re.compile(fregexp)
			self.exprs.append(cregexpr)

	def gen(self, w, cregexpr=None):
		if cregexpr == None:
			for cregexpr in self.exprs:
				yield from self.gen(w, cregexpr)
			return
		groups=cregexpr.groups
		def rec_gen(w, m, gro):
			let=m.group(gro)
			sub=self.d[let]
			if not type(sub) in (type([]), type((0,0))):
				sub=[sub]
			for sb in sub:
				nw=w[:m.start(gro)]+sb+w[m.end(gro):]
				yield nw
				if gro<groups:
					yield from rec_gen(nw, m, gro+1)
					yield from self.gen_sup_gen(nw, False)

		for m in cregexpr.finditer(w):
			g_num=1
			while (g_num<=groups):
				yield from rec_gen(w, m, g_num)
				g_num+=1
		yield w
		yield from self.gen_sup_gen(w, False)


class SH_REMistaker (REMistaker):
	consonants="хцчшщж"
	regexp="[{c}]([{d}])"

class OA_REMistaker(REMistaker):
	regexp="[{c}]([{d}])[{c}]([{d}])[{c}]"

class Silenter_REMistaker (REMistaker):
	consonants="бвгджз"
	#consonants_lo="кпстфш"
	regexp="([{d}])([{d}])ь?$"

class VDrop_REMistaker(REMistaker):
	regexp="л?([{d}])ств"

class DDrop_REMistaker(REMistaker):
	# здн, рдц, ндск, - ндс
	regexp=[
		"з([{d}])н",
		"р([{d}])ц",
		"н([{d}])ск?",
		]

class Silenter (Mistaker):
	def __init__(self):
		Mistaker.__init__(self, {u'б':u'п', u'г':u'к', u'в':u'ф',
		    u'д':u'т',u'з':u'c', u'ж':u'ш'})
		self.loud=self.d.keys()
		self.silent=list(self.d.values())+[u'ц',u'ч',u'щ',u'х']
		self.end=u'ц'

	def cond(self, w, idx, key):
		ww=w+self.end
		try:
			return ww[idx+len(key)] in self.silent
		except IndexError:
			return False

class Louder1(Silenter): # оглушение последней буквы на конце слова
	def __init__(self):
		Mistaker.__init__(self, {u'п':u'б', u'к':u'г', u'ф':u'в', u'т':u'д',u'с':u'з', u'ш':u'ж'})
		self.loud=self.d.keys()
		self.silent=set(self.d.values())
		self.silent.remove(u'в')
		self.end=u'п'

class Louder2(Silenter): # озвончение
	def __init__(self):
		Mistaker.__init__(self, {u'пь':u'бь', u'кь':u'гь', u'фь':u'вь', u'ть':u'дь',u'сь':u'зь'})
		self.loud=self.d.keys()
		silent=self.d.values()
		self.silent=[w[1] for w in silent]
		self.end=u''


def header(csvf):
	csvf.writerow(['norm_word','err_word'])

def write_csv(orig, tab, csvf): # f must be already opened

	for w in tab:
		csvf.writerow((orig,w))

def to_csv(orig, tab, filename, noclose=False):
	f=open(filename, "w")
	csvf=csv.writer(f,dialect=csv.excel, delimiter=";", quoting=csv.QUOTE_ALL)
	header(csvf)
	if orig == None:
		return csvf,f
	write_csv(orig, tab, csvf)
	if not noclose:
		f.close()
	return csvf,f

oae_w0={ u'же':u'жи', u'ше':u'ши', u'цо':u'ца',
		 u'ча':u'чи', u'че':u'чи', u'чя':u'чи', u'ща':u'щи', u'ще':u'щи'}
oe_dict={u"о":u"а", u"е":u"и"} # о - о на конце слова , о-е -льон, ньон....- провлка,

DEFAULT_GENS=[
	Mistaker(oae_w0),
	Mistaker(oe_dict,no_end=True),
	Silenter(),
	Louder1(),
	Louder2(),
	OA_REMistaker({"о":["а","_"]}),
	VDrop_REMistaker({"в":["ф","_"]}),
	DDrop_REMistaker({"д":["т","_"]}),
	REMistaker({"а":"и","я":"и","ы":"и"}),
	SH_REMistaker({"а":"и","о":"е"}),
	Silenter_REMistaker(d={u'б':u'п', u'г':u'к', u'в':u'ф',
		    u'д':u'т',u'з':u'c', u'ж':u'ш'}),
]

DEFAULT_GENS=[
	CacheMistaker(name="url"),
	HTTPMistaker(url="http://4seo.biz/tools/12/"),
]

def test1():
	genlist=DEFAULT_GENS
	#tw=[u"неясность", u"новгород", u"гвоздь", "часы",u"проволока",u"мясной",u"бульон", u"дрозд", u"обклеить", u"здравствуй"]
	tw=[u"здравствуй", "явства", "голландский"]
	#tw=[u"неясность", u"новгород", u"гвоздь",
	#	u"бульон",u"окно", u"бесшумный", u"косьба",
	#	u"часы",u"проволока",u"мясной",u"безынициативный",		]
	gl=genlist[:]
	start=genlist[0]
	gl.reverse()
	f1=gl[0]
	for _ in gl[1:]:
		_.set_sup(f1)
		f1=_

	for r in tw:
		#print (r)

	#g=SH_REMistaker({"е":"и"})
		"""
		g=OA_REMistaker({"о":["а","_"]})
		g1=REMistaker({"а":"и","я":"и","ы":"и"})
		g2=SH_REMistaker({"а":"и","о":"е"})
		g3=Silenter_REMistaker(d={u'б':u'п', u'г':u'к', u'в':u'ф',
		    u'д':u'т',u'з':u'c', u'ж':u'ш'})
		"""
		#g1=Mistaker(oe_dict,no_end=True)
		#g=Mistaker(oae_w0)


	#for n in g.gen(w):
	#    print (n)

	#for n in g(w):
	#	print (n)
		"""
		print (g.as_set(r))
		print (g1.as_set(r))
		print (g2.as_set(r))
		"""
		pprint.pprint (start.as_set(r))

	start.done_all()

	"""
	csvf,f=to_csv (w,g.as_set(w), "a.csv", noclose=True)


	w=u"молоко"
	g=Mistaker(oe_dict)
	print (g.as_set(w))

	write_csv(w, g.as_set(w),csvf)

	f.close()
	"""

# DEFAULT_GENS=[Louder1()]

def load_and_gen(outp=None, genlist=DEFAULT_GENS):
	if outp == None:
		outp="out.csv"
	c,o=to_csv(None, None, outp, noclose=True)
	gl=genlist
	start=genlist[0]
	gl.reverse()
	f1=gl[0]
	for _ in gl[1:]:
		_.set_sup(f1)
		f1=_

	inp=open("data/ozhegov.dic", "rb")
	words=pickle.load(inp)

	q=10

	mst=dict() # {}
	keys=list(words.keys())
	keys.sort()
	for w in keys:
		if not w: continue
		se=start.as_set(w)
		mst[w]=se

		#print (se)
		write_csv(w,se,c)
		#~ if q<=0:
			#~ break
		#~ q-=1

	mst_o=open("data/mst.dic", "wb")
	pickle.dump(mst,mst_o)
	mst_o.close()

	o.close()



if __name__=="__main__":
	test1() # test one word

	#load_and_gen('word_rus_fon.txt')
#	load_and_gen()


	quit()
