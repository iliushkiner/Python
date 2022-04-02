# miner_text_generator.py

import io
import urllib.request

from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage


def extract_text_by_page(url):
    f = urllib.request.urlopen(url).read()
    # Cast to StringIO object
    fp = io.BytesIO(f)
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
        resource_manager = PDFResourceManager()
        fake_file_handle = io.StringIO()
        converter = TextConverter(resource_manager, fake_file_handle)
        page_interpreter = PDFPageInterpreter(resource_manager, converter)
        page_interpreter.process_page(page)

        text = fake_file_handle.getvalue()
        yield text

        # close open handles
        converter.close()
        fake_file_handle.close()
    fp.close()

def extract_text(url):
    for page in extract_text_by_page(url):
        print(page)
        print()


if __name__ == '__main__':
    print(extract_text('http://ppoz-filestorage-bal-01.prod.egrn:12088/Other-2021-12-21-347248/02c21401-d13b-40ca-8bd5-6eeb2854d3c3/ZIP_ENTRY/'))
