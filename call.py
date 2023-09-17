from wordle_module import wordle, utils

obj = wordle.Main(colormap = ["#fff", "#c0bcbc", "#14b31c", "#d4bd11", "#fff"], font_size = 45) #init of game. arguments see in docstrings of module

output = obj.check("приве")
print(output)
print(utils.save_from_PIL(output["image"], path = "try1.jpg"))

output = obj.check("aaaws")
print(output)
print(utils.save_from_PIL(output["image"], path = "try2.jpg"))

output = obj.check("worgd")
print(output)
print(utils.save_from_PIL(output["image"], path = "try3.jpg"))

output = obj.check("12345")
print(output)
print(utils.save_from_PIL(output["image"], path = "try4.jpg"))

output = obj.check("12345")
print(output)
print(utils.save_from_PIL(output["image"], path = "try4.jpg"))