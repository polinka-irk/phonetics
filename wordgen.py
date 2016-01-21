# encoding: utf-8
import csv

ENC='cp1251'

class Mistaker(object):
	"""Generates mistake words from an agument
	"""

	def __init__(self, d):
		"""
		"""
		self.d=d
		self.s=list(d.items())
		self.l=len(self.s)
		self.sup=None
		
	def set_sup(self, sup):
		self.sup=sup
		
	def run_sup(self, w):
		if self.sup == None:
			return
		else:
			for _ in self.sup.gen(w):
				yield _

	def gen(self, w, sq_no=0, sidx=0):
		if sq_no>=self.l:
			if self.sup == None:
				return
			else:
				for _ in self.sup.gen(w):
					yield _		
		else:
			s,t=self.s[sq_no]
			idx=w.find(s,sidx)
			if idx<0:
				for _ in self.gen(w, sq_no+1):
					yield _
			else:
				tw=w[sidx:]
				hw=w[:sidx]
				i=idx-sidx
				ntw=tw.replace(s,t,1)
				nw=hw+ntw
				yield nw
				for _ in self.gen(w, sq_no, idx+1):
					yield _
				for _ in self.gen(nw):
					yield _
				if self.sup == None:
					return
				else:
					for _ in self.sup.gen(nw):
						yield _		

	def as_set(self, w):
		"""
		"""
		return set(self.gen(w))

	def __call__(self, *args, **kwargs):
		return self.gen(*args, **kwargs)
	
class Silenter (Mistaker):
	def __init__(self):
		Mistaker.__init__(self, {u'б':u'п', u'г':u'к', u'в':u'ф', 
		    u'д':u'т',u'з':u'c', u'ж':u'ш'})
		self.loud=self.d.keys()
		self.silent=self.d.values()+[u'ц',u'ч',u'щ',u'х']
		self.end=u'ц'
	
	def gen(self, w, sq_no=0, sidx=0):
		if sq_no>=self.l:
			if self.sup == None:
				return
			else:
				for _ in self.sup.gen(w):
					yield _		
		else:
			s,t=self.s[sq_no]
			idx=w.find(s,sidx)
			if idx<0:
				for _ in self.gen(w, sq_no+1):
					yield _
			else:
				ww=w+self.end
				if ww[idx+1] in self.silent:
					tw=w[sidx:]
					hw=w[:sidx]
					i=idx-sidx
					ntw=tw.replace(s,t,1)
					nw=hw+ntw
					yield nw
					for _ in self.gen(w, sq_no, idx+1):
						yield _
					for _ in self.gen(nw):
						yield _
					if self.sup == None:
						return
					else:
						for _ in self.sup.gen(nw):
							yield _		
				else:
					for _ in self.gen(w, sq_no+1):
						yield _

class Louder1(Silenter):
	def __init__(self):
		Mistaker.__init__(self, {u'п':u'б', u'к':u'г', u'ф':u'в', u'т':u'д',u'с':u'з', u'ш':u'ж'})
		self.loud=self.d.keys()
		self.silent=set(self.d.values())
		self.silent.remove(u'в')
		self.end=u'п'

class Louder2(Silenter):
	def __init__(self):
		Mistaker.__init__(self, {u'пь':u'бь', u'кь':u'гь', u'фь':u'вь', u'ть':u'дь',u'сь':u'зь'})
		self.loud=self.d.keys()
		silent=self.d.values()
		self.silent=[w[1] for w in silent]
		self.end=u'п'
	
					
def header(csvf):
	csvf.writerow(['norm_word','err_word'])
	
def write_csv(orig, tab, csvf): # f must be already opened
	enc=ENC
	orig=orig.encode(enc)
	for w in tab:
		csvf.writerow((orig,w.encode(enc)))
		
def to_csv(orig, tab, filename, noclose=False):
	f=open(filename, "wb")
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
oe_dict={u"о":u"а", u"е":u"и"}

def test1():
	w=u"желаниецо"
	print ()

	g=Mistaker(oae_w0)
	#for n in g.gen(w):
	#    print (n)

	for n in g(w):
		print (n)

	print (g.as_set(w))
	
	csvf,f=to_csv (w,g.as_set(w), "a.csv", noclose=True)
	

	w=u"молоко"
	g=Mistaker(oe_dict)
	print (g.as_set(w))
	
	write_csv(w, g.as_set(w),csvf)
	
	f.close()
	
DEFAULT_GENS=[Mistaker(oae_w0), Mistaker(oe_dict), Silenter(), Louder1(), Louder2()]	
# DEFAULT_GENS=[Louder1()]	

def load_and_gen(inp, outp=None, genlist=DEFAULT_GENS):
	if outp == None:
		outp=inp+"_out.csv"
	i=open(inp)
	c,o=to_csv(None, None, outp, noclose=True)
	gl=genlist
	start=genlist[0]
	gl.reverse()
	f1=gl[0]
	for _ in gl[1:]:
		_.set_sup(f1)
		f1=_
		
	for w in i:
		w=w.strip().decode(ENC)
		if not w:
			continue
		se=start.as_set(w)
		write_csv(w, se, c)
		
	i.close()
	o.close()
	


if __name__=="__main__":
	#test1()
	
	#load_and_gen('word_rus_fon.txt')
	load_and_gen('word_rus.txt')
	
	
	quit()
