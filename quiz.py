"""Implements methods related to the quiz commands of mathbot.subs.gastercoin."""
import os
import random
import ujson
import textwrap
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFilter
from PIL import ImageFont

from subs.gastercoin import mathgen
from subs.gastercoin.account import parse_int

QUESTIONS_DIRECTORY = f'./subs/gastercoin/resources/questions/'
QUESTION_FILES = [f for f in os.listdir(QUESTIONS_DIRECTORY)]

QUESTION_CATEGORIES = [filename[:-4] for filename in QUESTION_FILES]

QUIZ_TARGET_SCORE = 5

QUIZ_RULES = 'The rules of the competition are as follows: (1) First person to get to 5 points wins. Each question ' \
             'answered correctly is worth a point. (2) You both have 10 seconds to answer the question. The first to ' \
             'answer correctly will win that round.'

QUESTIONS_JSON = './subs/gastercoin/resources/questions.json'

JEOPARDY_FONT = './subs/gastercoin/resources/Korinna Bold.ttf'
JEOPARDY_BLUE = (6, 12, 233)
JEOPARDY_SHADOW = (68, 68, 68)
JEOPARDY_WIDTH, JEOPARDY_HEIGHT = (400, 300)

OUT_FILE = './subs/gastercoin/resources/out.png'

with open(QUESTIONS_JSON, 'r') as f:
    QUESTIONS = ujson.load(f)


def makeShadow(image, iterations, border, offset, backgroundColour, shadowColour):
    fullWidth = image.size[0] + abs(offset[0]) + 2 * border
    fullHeight = image.size[1] + abs(offset[1]) + 2 * border

    shadow = Image.new(image.mode, (fullWidth, fullHeight), backgroundColour)

    shadowLeft = border + max(offset[0], 0)  # if <0, push the rest of the image right
    shadowTop = border + max(offset[1], 0)  # if <0, push the rest of the image down
    shadow.paste(shadowColour,
                 [shadowLeft, shadowTop,
                  shadowLeft + image.size[0],
                  shadowTop + image.size[1]])

    for i in range(iterations):
        shadow = shadow.filter(ImageFilter.BLUR)

    imgLeft = border - min(offset[0], 0)  # if the shadow offset was <0, push right
    imgTop = border - min(offset[1], 0)  # if the shadow offset was <0, push down
    shadow.paste(image, (imgLeft, imgTop))

    return shadow


def wrap_text(text, font, max_length, max_height):
    text_words = text.split(' ')
    text_line = ''
    new_text = []
    for word in text_words:
        if font.getsize(text_line + word)[0] <= max_length:
            text_line += word + ' '
        else:
            new_text.append(text_line)
            text_line = word + ' '
    else:
        if text_line != '':
            new_text.append(text_line)

    return '\n'.join(new_text)


def draw_jeopardy(text):
    text = text[1:-1].upper()
    text = text.replace('<BR/>', '\n').replace('<BR />', '\n')
    font = ImageFont.truetype(JEOPARDY_FONT, size=24)

    padding = 0
    bounding_box = [padding, padding, JEOPARDY_WIDTH - padding, JEOPARDY_HEIGHT - padding]
    x1, y1, x2, y2 = bounding_box

    background = Image.new('RGBA', (JEOPARDY_WIDTH, JEOPARDY_HEIGHT), JEOPARDY_BLUE)
    text_layer = Image.new('RGBA', (JEOPARDY_WIDTH, JEOPARDY_HEIGHT))
    draw = ImageDraw.Draw(text_layer)

    text = wrap_text(text.upper(), font, JEOPARDY_WIDTH - 50, JEOPARDY_HEIGHT - 50)

    w, h = draw.textsize(text, font=font)
    x = (x2 - x1 - w) / 2 + x1
    y = (y2 - y1 - h) / 2 + y1
    draw.text((x, y), text, align='center', font=font)
    text_layer = makeShadow(text_layer, 3, 10, (10, 10), JEOPARDY_BLUE, JEOPARDY_SHADOW)
    # draw.text(((JEOPARDY_WIDTH - width)/2, (JEOPARDY_HEIGHT - height)/2), text, fill="white", font=font)

    background.paste(text_layer, mask=text_layer)
    background.save(OUT_FILE)
    return 'SUCCESS'


def get_new_question(final_jeopardy=False):
    while True:
        index = random.choice(list(QUESTIONS.keys()))
        if not final_jeopardy:
            break
        elif QUESTIONS[index]['value'] == 2000:
            break
    question = QUESTIONS[index]
    return question['category'], question['value'], question['question'], question['answer']


def write_jeopardy_header(round_number, player1, score1, player2, score2, category, value=0, final_jeopardy=False):
    if not final_jeopardy:
        header = f'__**JEOPARDY!**__\n**' \
                 f'Round {round_number}/10**\n\n' \
                 f'__Current Score__:\n' \
                 f'__{player1}__: {score1}\n' \
                 f'__{player2}__: {score2}\n\n' \
                 f'__Category__: {category}\n' \
                 f'__Value__: {value}\n\n'
    else:
        header = f'__**FINAL JEOPARDY!**__\n**' \
                 f'Round {round_number}/10**\n\n' \
                 f'__Current Score__:\n' \
                 f'__{player1}__: {score1}\n' \
                 f'__{player2}__: {score2}\n\n' \
                 f'__Category__: {category}\n\n' \
                 f'{player1} and {player2}, place your bets!'
    return header
