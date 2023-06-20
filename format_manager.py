import re

special = '0'
text = '2'
background = '2'
specials = {
    "$$_": '4',   # underscore
    "$$*": '38',  # bold - 38
    "$$i": '3',   # italics
    "$$~": '9',   # strikethrough
    "$$[": '51',  # boxed - 51
    "$$^": '7',   # negative
    "$$s": '0',   # end specials
    "$$$": '0'    # end all
}
texts = {
    "$$b": '30',  # black
    "$$r": '31',  # red
    "$$g": '32',  # green
    "$$y": '33',  # yellow
    "$$a": '34',  # aqua
    "$$p": '35',  # purple
    "$$c": '36',  # cyan
    "$$f": '37',  # faded
    "$$t": '2'    # end text
}
backgrounds = {
    "$$B": '40',  # black
    "$$R": '41',  # red
    "$$G": '42',  # green
    "$$Y": '43',  # yellow
    "$$A": '44',  # aqua
    "$$P": '45',  # purple
    "$$C": '46',  # cyan
    "$$F": '47',  # faded
    "$$E": '91',  # error
    "$$e": '93',  # warning
    '$$0': '2'    # end background
}
all_codes = {**specials, **texts, **backgrounds}

rep = dict((re.escape(k), v) for k, v in all_codes.items())
pattern = re.compile("|".join(rep.keys()))


def c_format(string: str) -> None:
    print(pattern.sub(lambda m: __get_formatted(rep[re.escape(m.group(0))], m.group(0)), "$$$" + string))


def c_input(string: str) -> str:
    return input(pattern.sub(lambda m: __get_formatted(rep[re.escape(m.group(0))], m.group(0)), "$$$" + string))


def __get_formatted(string: str, code: str):
    global special, text, background
    if code == "$$$":
        special = '0'
        text = '2'
        background = '2'
    if code in specials:
        special = string
    if code in texts:
        text = string
    if code in backgrounds:
        background = string
    return '\033[{};{};{}m'.format(special, text, background)
