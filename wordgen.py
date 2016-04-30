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

check_re=re.compile("^[а-яА-Я]*$")

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

	def check_gen(self, w, sq_no=0, sidx=0):
		if len(w)<3:
			return
		if not check_re.match(w):
			return
		yield from self.gen(w, sq_no=sq_no, sidx=sidx)

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
		for w in self.check_gen(w):
			w=w.replace("_","")
			if debug:
				rc.add((w,self.__class__.__name__))
			else:
				rc.add(w)
		return rc

	def __call__(self, *args, **kwargs):
		return self.check_gen(*args, **kwargs)

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
	def __init__(self, name, dump_hits=1000):
		self.name=name
		self.fname=self.name+".cache"
		self.dump_hits=dump_hits
		Mistaker.__init__(self)
		self.c={}
		self.miss=0
		self.init()

	def init(self):
		print ("Loading cash!")
		try:
			self.c=pickle.load(open(self.fname,"rb"))
			print ("Done.")
		except Exception:
			self.c={}
			print ("Failed.")

	def done(self):
		self.dump()
	def dump(self):
		if self.miss:
			print ("Dumping cash!")
			f=open(self.fname,"wb")
			pickle.dump(self.c, f)
			f.flush()
			f.close()
			self.miss=0
			print ("Done.")

	def __del__(self):
		self.done()

	def gen(self, w):
		if w in self.c:
			vals=self.c[w]
			for v in vals:
				yield v
		else:
			self.miss+=1
			vals=[]
			for v in self.gen_sup_gen(w, False):
				vals.append(v)
				yield v
			self.c[w]=vals
			if self.miss>=self.dump_hits:
				self.dump()



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
			if 'repl' in self.__class__.__export__:
				try:
					sub=self.d[let]
				except KeyError:
					sub=self.repl
			else:
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
	#
	consonants="хцчшщж"
	regexp="[{c}]([{d}])"
	#gen="SH_REMistaker"


class OA_REMistaker(REMistaker):
	# о - о на конце слова , о-е -льон, ньон....- провлка,
	regexp="о?а?[{c}]([{d}])[{c}]([{d}])[{c}][{v}]?й?$"
	#gen="OA_REM)"


class OJ_REMistaker(REMistaker): # о-ы в -ова, цо - цы, шо-шы (цокотать, шоколад)
	consonants="цш"
	regexp=["^[{c}]([{d}])",
			"([{d}])ват?ь?$"]

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
class TDrop_REMistaker(REMistaker):
	# -стн, -стл, -нтск, -стск, -нтс, -нтк
	regexp=[
		"c([{d}])н",
		"c([{d}])л",
		"с([{d}])ск",
		"н([{d}])с?к",
		]
class LDrop_REMistaker(REMistaker):
	# -лнц
	regexp="([{d}])нц"


class GV_REMistaker(REMistaker):
	#-ого, -его на -ово - ево
	regexp="[ео]([{d}])о$"

class GH_REMistaker(REMistaker):
	# гк---х
	regexp="([{d}])к"

class Z_REMistaker(REMistaker):
	# з-, раз- без- из-
	regexp=["^и?([{d}])",
			"ра([{d}])",
			"бе([{d}])"
			]
class GG_REMistaker(REMistaker):
	# сж, зж - --жж
	regexp="([{d}])ж"

class HH_REMistaker(REMistaker):
	#
	consonants="шч"
	regexp="([{d}])[{c}]"

class CA_REMistaker(REMistaker):
	# -ться - тся ,  на ца
	__export__=('repl',)
	regexp=["(ть[{d}]я)",
			"(т[{d}]я)",
				]

class CH_REMistaker(CA_REMistaker):
	# сч-ш
	regexp="([{d}]ч)"


class SCH_REMistaker(CA_REMistaker):
	# сч----щ, сч----шщ
	regexp="(с[{d}])"

class TSK_REMistaker (CA_REMistaker):
	#нтск--ц "(т[{d}]к)"
	regexp=["(н[{d}]к)",

	"([д][{d}]к)"]

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

class Louder1(Silenter): # озвончение глухой перед звонкой
	def __init__(self):
		Mistaker.__init__(self, {u'п':u'б', u'к':u'г', u'ф':u'в', u'т':u'д',u'с':u'з', u'ш':u'ж'})
		self.loud=self.d.keys()
		self.silent=set(self.d.values())
		self.silent.remove(u'в')
		self.end=u'п'

class Louder2(Silenter): # озвончение глухой с ь
	def __init__(self):
		Mistaker.__init__(self, {u'пь':u'бь', u'кь':u'гь', u'фь':u'вь', u'ть':u'дь',u'сь':u'зь'})
		self.loud=self.d.keys()
		silent=self.d.values()
		self.silent=[w[1] for w in silent]
		self.end=u''


def header(csvf):
	csvf.writerow(['norm_word','err_word','gen'])

def write_csv(orig, tab, csvf): # f must be already opened

	for w in tab:
		csvf.writerow((orig,w))

def to_csv(orig, tab, filename, noclose=False):
	f=open(filename, "w")
	csvf=csv.writer(f,dialect=csv.excel, delimiter=";", quoting=csv.QUOTE_ALL)
	header(csvf)
	if orig == None:
		return csvf,f
	write_csv(orig, tab, gen,csvf)
	if not noclose:
		f.close()
	return csvf,f

oae_w0={ u'же':u'жи', u'ше':u'ши', u'цо':u'ца',
		 u'ча':u'чи', u'че':u'чи', u'чя':u'чи',
		 u'ща':u'щи', u'ще':u'щи'}
oe_dict={u"о":u"а", u"ё":u"о", u"е":u"и"}

DEFAULT_GENS=[
	Mistaker(oae_w0),
	Mistaker(oe_dict,no_end=True),
	Silenter(),
	Louder1(),
	Louder2(),
	OA_REMistaker({"о":["а","_"]}),
	OJ_REMistaker({"ы":"о","о":"ы"}),
	VDrop_REMistaker({"в":["ф","_"]}),
	DDrop_REMistaker({"д":["т","_"]}),
	TDrop_REMistaker({"т":["т","_"]}),
	LDrop_REMistaker({"л":["л","_"]}),
	GV_REMistaker({"г":"в"}),
	GH_REMistaker({"г":"х"}),
	Z_REMistaker({"з":"с"}),
	GG_REMistaker({"з":"ж","с":"ж"}),
	HH_REMistaker({"з":"ш","с":"ш"}),
	CH_REMistaker({"з":"с","с":["с"]}, repl="щ"),
	SCH_REMistaker({"ч":"щ"}, repl="щ"),
	CA_REMistaker({"с":"с"}, repl="ца"),
	TSK_REMistaker ({"с":"ц"},repl="нцк"),
	# {"ться":"ца", "тся":"ца" ,"тск":"ца"}
	REMistaker({"а":"и","я":"и","ы":"и"}),
	SH_REMistaker({"а":"и","о":"е"}),
	Silenter_REMistaker(d={u'б':u'п', u'г':u'к', u'в':u'ф',
		    u'д':u'т',u'з':u'c', u'ж':u'ш'}),
	]

REMOTE_GENS=[
	CacheMistaker(name="url"),
	HTTPMistaker(url="http://4seo.biz/tools/12/"),
]
#DEFAULT_GENS=[
#	CacheMistaker(name="url"),
#	HTTPMistaker(url="http://4seo.biz/tools/12/"),
#	CA_REMistaker({"с":"с"}, repl="ца"),# {"ться":"ца", "тся":"ца" ,"тск":"ца"}
#]

def connect(genlist):
	gl=genlist[:]
	start=genlist[0]
	gl.reverse()
	f1=gl[0]
	for _ in gl[1:]:
		_.set_sup(f1)
		f1=_
	return start


def test1():
	genlist=DEFAULT_GENS

	#import pdb; pdb.set_trace()
	#tw=[u"неясность", u"новгород", u"гвоздь", "часы",u"проволока",u"мясной",u"бульон", u"дрозд", u"обклеить", u"здравствуй"]
	tw=[
	#u"изчезать","визжать", "расщепить", "счастье", "грузчик","сжег",
	#"бездна", "гигантский",
	#"голландский","эсперантист","энский", "щеголеватый", "проволока"
	"цокотать", "шоколад",
	"бульон",
	"ра","и", "без","му-",

	#"здесь", "пробывать","мягкий", "бездна", "аспирантка","моего", "явства", "солнце","праздник", "проволока","гиганстский","бояться"
	]
	#tw=[u"неясность", u"новгород", u"гвоздь",
	#	u"бульон",u"окно", u"бесшумный", u"косьба",
	#	u"часы",,u"мясной",u"безынициативный",		]

	start=connect(genlist)

	for r in tw:

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

def restore_cache():
	cc=open("save/out_tmp.csv","r")
	d={}
	cc.readline()
	pw=None
	q=10
	for l in cc:
		l=l.strip("\n")
		if not l:
			continue
		ls=l.split('";"')
		ls=[x.strip('"') for x in ls]
		w,nw=ls
		d.setdefault(w,[]).append(nw)
		#~ print (d)
		#~ if q<=0:
			#~ break
		#~ q-=1
	oo=open("url.cache","wb")
	pickle.dump(d,oo)
	oo.flush()
	oo.close()
	return

def load_and_gen(outp=None, genlist=DEFAULT_GENS, use_remote=False):
	if outp == None:
		outp="out-noremote.csv"
	c,o=to_csv(None, None, outp, noclose=True)
	start=connect(genlist)
	rem_start=connect(REMOTE_GENS)

	inp=open("data/ozhegov.dic", "rb")
	words=pickle.load(inp)
	print (len(words))

	q=10
	pack=10

	mst=dict() # {}
	keys=list(words.keys())
	keys.sort()
	k=1
	for w in keys:
		if not w: continue
		se=set()
		se.update(start.as_set(w))
		if use_remote:
			se.update(rem_start.as_set(w))

		#print (se)
		mst[w]=se
		write_csv(w,se,c)
		#~ if q<=0:
			#~ break
		#~ q-=1
		if k % pack == 0:
			print (k, 'of', len(keys))
		k+=1


	mst_o=open("data/mst.dic", "wb")
	pickle.dump(mst,mst_o)
	mst_o.close()

	o.close()



if __name__=="__main__":
	test1() # test one word

	#load_and_gen('word_rus_fon.txt')
	#load_and_gen()


	quit()
