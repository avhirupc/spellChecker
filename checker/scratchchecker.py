import re
import numpy as np
from collections import Counter,defaultdict
from utils import words
from .base import BaseChecker
from memo import memo
from functools import reduce
from textblob import Word
import pickle

class SpellCorrector(object):
	"""SpellCorrector class implements single spell correction algorithm based on token frequency supplied"""
	def __init__(self, corpus_path='WORDS.pkl'):
		super(SpellCorrector, self).__init__()
		self.WORDS=defaultdict(int)
		d = pickle.load(open(corpus_path,"rb"))
		for k,v in d.items():
			self.WORDS[k]=v

		self.N=sum(self.WORDS.values())

			
	def P(self,word): 
		"Probability of `word`."
		try:
			return self.WORDS[word] / self.N        
		except KeyError:
			#prob for word not found is extremely low 
			return -np.inf
	
	def correction(self,word): 
		"Most probable spelling correction for word."
		return max(self.candidates(word), key=self.P)

		
	def candidates(self,word): 
		"Generate possible spelling corrections for word."
		return self.known([word]) or self.known(self.edits1(word)) or self.known(self.edits2(word)) or [word]
			
	def known(self,words): 
		"The subset of `words` that appear in the dictionary of WORDS."
		return (set(w for w in words if w in self.WORDS))

	def edits1(self,word):
		"All edits that are one edit away from `word`."
		letters    = 'abcdefghijklmnopqrstuvwxyz -'
		splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
		deletes    = [L + R[1:]               for L, R in splits if R]
		transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
		replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
		inserts    = [L + c + R               for L, R in splits for c in letters]
		return set(deletes + transposes + replaces + inserts)

	def edits2(self,word): 
		"All edits that are two edits away from `word`."
		return (e2 for e1 in self.edits1(word) for e2 in self.edits1(e1))
		

class WordSegmentor(object):
	"""WordSegmentor implements viterbi algorithm to segment word into multiple words to maximise word likelihood"""
	def __init__(self, corpus_path='WORDS.pkl'):
		super(WordSegmentor, self).__init__()
		self.sc=SpellCorrector(corpus_path)
		self.WORDS=defaultdict(int)
		d = pickle.load(open(corpus_path,"rb"))
		for k,v in d.items():
			self.WORDS[k]=v
		self.max_word_length = max(map(len, self.WORDS))
		self.total = float(sum(self.WORDS.values()))

	def splits(self,text, L=5):
		"Return a list of all possible (first, rem) pairs, len(first)<=L."
		splitsa =  [(text[:i+1], text[i+1:]) for i in range(max(len(text), L))]
		return splitsa

	@memo
	def segment(self,text):
		"Return a list of words that is the best segmentation of text."
		if not text: return []
		candidates = [[first.strip()]+[rem.strip()] for first,rem in self.splits(text)]
		candidates = [[c for c in can if c!=""] for can in candidates ]
		return max(candidates, key=self.Pwords)
	
	def Pwords(self,words):
		"The Naive Bayes probability of a sequence of words."
		prod = 0.0
		prod =  reduce(lambda a,b:a*b,(self.word_prob(self.sc.correction(w)) for w in words))
		return prod

	def word_prob(self,word):
		return self.WORDS[word] / self.total

		
class ScratchChecker(BaseChecker):
	"""ScratchChecker implements spell checker given token frequency"""
	def __init__(self, preproc_rules=None,corpus_path='WORDS.pkl'):
		super(ScratchChecker, self).__init__(preproc_rules)
		self.sc=SpellCorrector(corpus_path)
		self.ws=WordSegmentor(corpus_path)
		self.WORDS=defaultdict(int)
		d = pickle.load(open(corpus_path,"rb"))
		for k,v in d.items():
			self.WORDS[k]=v

	def process(self,word):
		if word in self.WORDS.keys():
		#in case already correct word but segmenting words lead to higher likelihood
			return [word]
		out =  self.ws.segment(word)
		output = []
		for o in range(len(out)):
			output.append(self.sc.correction(out[o]))
		# print(out)
		return output

		

		
