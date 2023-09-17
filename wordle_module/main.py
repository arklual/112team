from .utils.utils import *
import random, os

class Main:
	def __init__(self, limg=None, attemps_already: int = None, target_word: str = None, dictionary_path: str = "dictionary/dictionary.txt", check_len: bool = True, **kwargs):
		'''
		Inputs:
			target_word - if you specify the target word, it will be used. else it will be selected automatically from the dictionary_dir
			dictionary_dir - path to dictionary. used only if target_word is None
			check_len - must we check len of word

			kwargs - additional kwargs for utils.utils.Draw
		'''
		
		if target_word is None:
			abs_path = os.path.join(
				os.path.dirname(os.path.abspath(__file__)),
				dictionary_path
			) #absolute path of dictionary

			self.target = random.choice(
				utils.read_txt(abs_path).split("\n")[:-1]
			) #selecting random target

		else: self.target = target_word

		self.check_len = check_len
		if not limg:
			self.image = Draw(**kwargs)
		else:
			self.image = limg
		if not attemps_already:
			self.line_num = 0
		else:
			self.line_num = attemps_already

	def check(self, word: str):
		'''
		Description:
			Checking entered word

		Inputs:
			word - word to check
		
		Outputs:
			is_correct - is word correct
			target - target word
			word - user specified word
			attempt - number of current attempt
			image - picture of game
		'''
		if self.check_len and len(word) != 5: raise Exception("The entered word does not match the length!")
		if self.line_num >= 5: raise Exception("More than 5 attempts have been made!")

		self.image.draw_line(word, self.target, self.line_num)
		self.line_num += 1

		return {
			"is_correct": word == self.target,
			"target": self.target,
			"word": word,
			"attempt": self.line_num,
			"image": self.image
		}
