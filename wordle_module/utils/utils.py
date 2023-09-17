import json
from PIL import Image, ImageDraw, ImageFont

class utils:

	@staticmethod
	def read_txt(path):
		with open(path, "r", encoding = "utf-8-sig") as f:
			return f.read()

	@staticmethod
	def read_json(path):
		with open(path, "r", encoding = "utf-8-sig") as f:
			return json.loads(f.read())

	@staticmethod
	def save_from_PIL(img, path: str = "test.jpg"):
		img.save(path,  quality=100)
		return path

class Draw:
	def __init__(self, img_size: int = 580, block_size: int = 80, padding: int = 20, margin: int = 50, font_size: int = 36, colormap: list = ["#fff", "#c0bcbc", "green", "yellow", "#fff"]):
		'''
		Inputs:
			img_size - size of image
			block_size - size of letter block
			padding - space between letter blocks
			margin - space between border and last/first blocks in evry axis
			font_size - size of letters
			colormap - colors of image
				0 - color of background
				1 - color of empty block
				2 - color of correct block
				3 - color of partially correct идщсл
				4 - color of letters
		'''
		self.colormap = colormap
		self.block_size = block_size
		self.size = img_size
		self.padding = padding
		self.margin = margin
		self.font_size = font_size

		self.positions = self.generate_positions() #generates positions of letter blocks

		self.img = Image.new(mode = "RGB", size = (img_size, img_size), color = self.colormap[0]) #background image
		self.drawing = self.draw_draft(ImageDraw.Draw(self.img)) #main image

	def generate_positions(self):
		'''
		Description:
			Uses constants defined in __init__ to generate letter block positions

		Outputs:
			pos - array of coordinates of blocks in format [[x1, y1, x2, y2], ... ]
		'''
		padding, block_size, margin = self.padding, self.block_size, self.margin
		pos = []

		for col in range(5):
			_ = [] #cache array

			for line in range(5):
				bias_line, bias_col = margin + (padding + block_size)*line, margin + (padding + block_size)*col

				_.append((bias_line, bias_col, bias_line + block_size, bias_col + block_size))

			pos.append(_)

		return pos

	def draw_draft(self, image):
		'''
		Description:
			Uses positions and image defined in __init__ to generate image

		Output:
			image - image with empty blocks
		'''
		for line in self.positions:
			for cords in line:

				image.rounded_rectangle(
					cords,
					fill = self.colormap[1],
					radius = 15
				)

		return image

	def draw_line(self, word: str, target_word: str, line_num: int):
		'''
		Description:
			Draws line of letters

		Inputs:
			word - user specified word
			target_word - target word
			line_num - index of line (starting from 0)
		'''
		with open('arial.ttf', 'rb') as fp:
			fnt = ImageFont.truetype("arial.ttf", self.font_size)
			image = self.drawing

			for sym, target_sym, pos in zip(word, target_word, self.positions[line_num]):

				#checks status of a block
				color = self.colormap[1]
				if sym == target_sym: color = self.colormap[2]
				elif sym in target_word: color = self.colormap[3]

				#drawing block
				image.rounded_rectangle(
					pos,
					fill = color,
					radius = 15
				)
				
				#adding text
				image.text(
					(pos[0] + self.block_size//2, pos[1] + self.block_size//2),
					sym,
					font = fnt,
					anchor="mm",
					fill = self.colormap[4]
				)

			self.drawing = image
