#!/usr/bin/env python3

import argparse
import urllib.parse
import qrcode
import qrcode.image.svg
import os
import sys
import shutil
from subprocess import run


urlPrefix = 'https://wiki.thu-skyworks.org/'

texPreamable = '''
\\documentclass{minimal}
\\usepackage[UTF8]{ctex}
\\usepackage{hyperref}
\\usepackage{graphicx}
\\usepackage{tikz}
\\usepackage{svg}
'''


class skylabel:
    NEW_CELL = 0
    NEW_PAGE = 1
    NEW_ROW = 2

    def new(self):
        self.counter += 1
        # Time to start a new row
        if self.currentcol % self.matrix[0] == 0:
            # to start a new page
            if self.currentrow % self.matrix[1] == 0:
                self.currentrow = 1
                self.currentcol = 1
                if self.counter != 1:
                    return self.NEW_PAGE
                else:
                    return self.NEW_CELL
            else:
                self.currentcol = 1
                self.currentrow += 1
                return self.NEW_ROW
        else:
            self.currentcol += 1
            return self.NEW_CELL

    def __init__(
            self, pagesize, qrsize, layout, logowidth, logooffset, textoffset,
            textsize, defaultPara, matrix=(1, 1),
            cellsep=(0, 0)):
        self.pagesize = pagesize
        self.qrsize = qrsize
        self.layout = layout
        self.logowidth = logowidth
        self.logooffset = logooffset
        self.textoffset = textoffset
        self.textsize = textsize
        self.matrix = matrix
        self.cellsep = cellsep
        self.defaultPara = defaultPara
        self.counter = 0
        self.currentrow = 0
        self.currentcol = 0

    def genQRImg(self, customUrl, content):
        if customUrl:
            qrstr = urllib.parse.quote(content)
        else:
            qrstr = urlPrefix + urllib.parse.quote(content)
        factory = qrcode.image.svg.SvgPathImage
        qrcode.make(qrstr, image_factory=factory).save(
            './temp/qr{}.svg'.format(self.counter))

    def genCell(self, customUrl, para):
        res = self.new()
        if res == self.NEW_PAGE:
            ret = '\\end{tikzpicture}\\newpage' + \
                '\\begin{tikzpkcture}[remember picture, overlay, shift=' + \
                '{(current page.north west)]\n'
        else:
            ret = ''
        if self.layout == 'A':
            self.genQRImg(customUrl, para[1])
            ret += '\\node (qrcode{}) at ({}mm, -{}mm) [anchor=center] '.\
                format(
                    self.counter,
                    0.5 * self.pagesize[0] +
                    (self.currentcol-1)*self.cellsep[0],
                    0.5 * self.pagesize[0] +
                    (self.currentrow-1)*self.cellsep[1]
                )
            ret += '{{\\includesvg[width={}mm]{{./temp/qr{}}}}};\n'.\
                format(self.qrsize, self.counter)
            ret += '''\\node[anchor=north,inner sep=0,shift={{({s[0]}mm,\
{s[1]}mm)}}] (logo{c}) at (qrcode{c}.south) {{\\includegraphics[width={w}mm]\
{{20110623skyworkslogo}}}};\n'''.format(s=self.logooffset,
                                        c=self.counter,
                                        w=self.logowidth)
            ret += '''\\node[anchor=north,inner sep=0,shift={{({s[0]}mm,\
{s[1]}mm)}}] (text{c}) at (logo{c}.south) {{\\{size}\\sffamily {text}}};
'''.format(s=self.textoffset, c=self.counter, size=self.textsize, text=para[0])
            pass
        elif self.layout == 'B':
            self.genQRImg(customUrl, para[1])
            ret += '\\node (qrcode{}) at ({}mm, -{}mm) [anchor=center] '.\
                format(
                    self.counter,
                    0.5 * self.pagesize[0] +
                    (self.currentcol-1)*self.cellsep[0],
                    0.5 * self.pagesize[0] +
                    (self.currentrow-1)*self.cellsep[1]
                )
            ret += '{' + '\\includesvg[width={}mm]'.format(self.qrsize) + \
                '{./temp/qr' + str(self.counter) + '}};\n'
            pass

        return ret
        pass


types = {
    '8050A':
    skylabel(
        pagesize=(50, 80),
        qrsize=45, layout='A', logowidth=35, logooffset=(0, -1),
        textsize='LARGE', textoffset=(0, -3.5),
        defaultPara=['天空工场', '天空工场']),
    '5030A':
    skylabel(
        pagesize=(30, 50),
        qrsize=26, layout='A', logowidth=23, logooffset=(0, -1),
        textsize='large', textoffset=(0, -2.5),
        defaultPara=['天空工场', '天空工场']),
    '2015TB':  # 20mm x 15mm Triple
    skylabel(
        pagesize=(15, 64),
        qrsize=13, layout='B', logowidth=5, logooffset=(0, 0),
        textsize='small', textoffset=(0, 0), matrix=(1, 3),
        cellsep=(0, 22), defaultPara=['天空工场', '天空工场'])
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate a PDF file for printing on adhesive labels with '
        'thermal printer.')
    parser.add_argument(
        '-i',
        metavar='INPUT',
        help='Input file name.',
        default='input.csv')
    parser.add_argument(
        '-o',
        metavar='OUTPUT',
        help='Output PDF file name prefix.',
        default='output')
    parser.add_argument(
        '-t',
        metavar='TYPE',
        default='8050-A',
        choices=types,
        help='Label size and layout.')
    parser.add_argument('-c', '--custom-url', action='store_true')
    parser.add_argument('--generate-examples', action='store_true')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    shutil.rmtree('./temp')
    os.makedirs('./temp')
    if args.generate_examples:
        os.makedirs('./examples', exist_ok=True)
        for k, v in types.items():
            tex = texPreamable + '\\usepackage[papersize={' + \
                '{}mm, {}mm'.format(v.pagesize[0], v.pagesize[1]) + \
                '}]{geometry}\n' + \
                '\\begin{document}\n' + \
                '\\begin{tikzpicture}[remember picture, overlay, shift=' + \
                '(current page.north west)]\n'
            for i in range(v.matrix[0] * v.matrix[1]):
                tex += v.genCell(args.custom_url, v.defaultPara)
            pass
            tex += '\\end{tikzpicture}\n\\end{document}'
            with open('./temp/' + k + '.tex', 'w') as f:
                f.write(tex)
            # Run twice to get node positions right.
            p = run(['xelatex', '-shell-escape', '-interaction=nonstopmode',
                     '-output-directory=./temp', '-halt-on-error',
                     './temp/' + k + '.tex'], stdout=sys.stdout,
                    encoding='utf-8')
            assert(p.returncode == 0)
            p = run(['xelatex', '-shell-escape', '-interaction=nonstopmode',
                     '-output-directory=./temp', '-halt-on-error',
                     './temp/' + k + '.tex'], stdout=sys.stdout,
                    encoding='utf-8')
            assert(p.returncode == 0)
            p = run(['pdftopng', './temp/' + k + '.pdf', './examples/' + k],
                    stdout=sys.stdout)
            assert(p.returncode == 0)