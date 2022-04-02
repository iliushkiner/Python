import io
import re
import urllib

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdf.doc_patterns import doc_patterns


def pdf_from_url_to_txt(url):
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    # Open the url provided as an argument to the function and read the content
    # f = urllib3.urlopen(urllib3.Request(url)).read()
    f = urllib.request.urlopen(url).read()
    # Cast to StringIO object
    fp = io.BytesIO(f)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()
    for page in PDFPage.get_pages(fp,
                                  pagenos,
                                  maxpages=maxpages,
                                  password=password,
                                  caching=caching,
                                  check_extractable=True):
        interpreter.process_page(page)
    fp.close()
    device.close()
    str = retstr.getvalue()
    retstr.close()
    return str


def get_doc_details(pdf_content):
    # функция возвращающая реквизиты pdf документа по паттерну из словаря doc_patterns.py
    # (r"выписка\s+№\s+(.+)\s+от\s(\d{2}.\d{2}.\d{4})\sг.", {'name': 'Выписка', 'elements': ['number', 'date']})
    result = {'name': '', 'number': '', 'date': ''}
    for pattern in doc_patterns:
        pattern_val = doc_patterns.get(pattern)
        # print(pattern_val)
        number_key = 0
        date_key = 1
        key = 1
        match = re.search(pattern, pdf_content, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        # match = re.findall(pattern, pdf_content, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        for element in pattern_val['elements']:
            if element == 'number':
                number_key = key
            elif element == 'date':
                date_key = key
            key += 1
            # print(element)
        try:
            # print(f"{pattern_val['name']} № {match[number_key]} от {match[date_key]}")
            result = {'name': '', 'number': '', 'date': ''}
            result['name'] = pattern_val['name']
            # result['number'] = match[number_key]
            # result['date'] = match[date_key]
            result['number'] = match.group(number_key)
            result['date'] = match.group(date_key)
            # # print(pdf_content[match.start(number_key):match.end(number_key)])
            # result['number'] = pdf_content[match.start(number_key):match.end(number_key)]
            # # print(pdf_content[match.start(date_key):match.end(date_key)])
            # result['date'] = pdf_content[match.start(date_key):match.end(date_key)]
            # del result['error']
            break
        except Exception as e:
            print(str(e))
            result = {'error': e}
    return result
