import jinja2

import os
from filetypes import is_diffable,get_lang

hon_colors = ["00","1C","38","54","70","8C","A8","C4","E0","FF"]
def isDigit(c):
    return c in ['0','1','2','3','4','5','6','7','8','9']
def key2dir(path):
    return '/'.join(path.split('|')[1].split('/')[:-1]) + '/'
def divall(cd,d):
    return [c/d for c in cd]
def hon2html(msg):
    msg = msg.replace('\\n','<br>')
    parts = msg.split('^')
    base = '<span>'
    #msg = '<span style="color: white;">' + parts[0]
    msg = base + parts[0]
    for part in parts[1:]:
        if len(part) < 1:
            msg += '^'
        elif part[0] == 'w' or part[0] == 'W':
            msg += '</span><span style="color: white;">' + part[1:]
        elif part[0] == 'r' or part[0] == 'R':
            msg += '</span><span style="color: #FF4C4C;">' + part[1:]
        elif part[0] == 'y' or part[0] == 'Y':
            msg += '</span><span style="color: #FFFF19;">' + part[1:]
        elif part[0] == 'g' or part[0] == 'G':
            msg += '</span><span style="color: #008000;">' + part[1:]
        elif part[0] == 'k' or part[0] == 'K':
            msg += '</span><span style="color: #000000;">' + part[1:]
        elif part[0] == 'c' or part[0] == 'C':
            msg += '</span><span style="color: #00FFFF;">' + part[1:]
        elif part[0] == 'b' or part[0] == 'B':
            msg += '</span><span style="color: #4C4CFF;">' + part[1:]
        elif part[0] == 't' or part[0] == 'T':
            msg += '</span><span style="color: teal;">' + part[1:]
        elif part[0] == 'o' or part[0] == 'O':
            msg += '</span><span style="color: orange;">' + part[1:]
        elif part[0] == 'm' or part[0] == 'M':
            msg += '</span><span style="color: #FF00FF;">' + part[1:]
        elif len(part) >= 3 and isDigit(part[0]) and isDigit(part[1]) and isDigit(part[2]):
            msg += '</span><span style="color: #%s%s%s;">' % (hon_colors[int(part[0])],hon_colors[int(part[1])],hon_colors[int(part[2])]) + part[3:]
        elif part[0] == '*':
            msg += '</span>' + base + part[1:]
        elif part[0] in [';',':']:
            msg += part[1:]
        else:
            msg += part
    return msg + '</span>'

def dmgreduction(armor):
    if armor >= 0:
        r = (0.06 * armor) / ( 1 + 0.06 * armor )
    else:
        r = 0.94**abs(armor) - 1
    return '{0}%'.format(round(r,5) * 100)

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
jinja_environment.filters['hon2html'] = hon2html
jinja_environment.filters['key2dir'] = key2dir
jinja_environment.filters['divall'] = divall
jinja_environment.filters['dmgreduction'] = dmgreduction
jinja_environment.filters['get_lang'] = get_lang
jinja_environment.tests['is_diffable'] = is_diffable

def get_template(path):
    return jinja_environment.get_template(path)
 
