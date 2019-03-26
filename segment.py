import fnmatch
import os
import re

import docx
import pandas as pd

from simple_distance import simple_distance


class Reader:
    def __init__(self, document):
        self.document = document

    def join_condition(self, document, i):
        raise NotImplementedError

    def join_q_and_a(self, remove=False):
        joined_lines = []
        temp_content = []
        for i, row in enumerate(self.document.paragraphs):
            if not row.text:
                continue
            if i < len(self.document.paragraphs) - 1 and \
                    self.join_condition(self.document, i):
                temp_content.append(row.text.strip(" "))
                if remove:
                    del temp_content[0]
                joined_lines.append('\n'.join(temp_content))
                temp_content.clear()
            else:
                temp_content.append(row.text)
        if temp_content:
            joined_lines.append('\n'.join(temp_content))
        return joined_lines

    def style_mask(self, doc, type=None):
        if type is None:
            return
        mask = []
        for para in doc.paragraphs:
            count = False
            for run in para.runs:
                if type == 'italic' and run.italic:
                    count = True
                if type == 'bold' and run.bold:
                    count = True
            mask.append(count)
        return mask

class NameReader(Reader):
    def __init__(self, document):
        super().__init__(document)
        self.q_label = self.determine_label(self.document)
        self.document = self.remove_empty_paragraphs(document)

    def join_condition(self, document, i):
        return document.paragraphs[i + 1].text.startswith(self.q_label)

    def determine_label(self, document):
        regex = '\w+:'
        return re.match(regex, document.paragraphs[0].text).group()

    def remove_empty_paragraphs(self, document):
        new_doc = docx.Document()
        for paragraph in document.paragraphs:
            if paragraph.text:
                # add just text (does not retain styling)
                new_doc.add_paragraph(paragraph.text)
        return new_doc

class ItalicReader(Reader):
    def __init__(self, document):
        super().__init__(document)

    def join_condition(self, document, i):
        mask = self.style_mask(document, type='italic')
        return mask[i + 1]

class BoldReader(Reader):
    def __init__(self, document):
        super().__init__(document)

    def join_condition(self, document, i):
        mask = self.style_mask(document, type='bold')
        return mask[i + 1]

class ListReader(Reader):
    """docx module does not handle list numbering, so the reader considers
    chunks as List Paragraph sections separated by empty lines"""
    def __init__(self, document):
        super().__init__(document)

    def join_condition(self, document, i):
        # determine if next paragraph is empty
        return not document.paragraphs[i + 1].text


READERS = {'NameReader': NameReader, 'ItalicReader': ItalicReader,
           'BoldReader': BoldReader, 'ListReader': ListReader}

class Segmenter:
    def __init__(self):
        self.corpus = None
        self.remove = None
        self.seg_corpus = None

    def get_paths(self, folder):
        paths = []
        for dirpath, dirnames, filenames in os.walk(folder):
            for file in list(filenames):
                if file.endswith(".docx") and not (fnmatch.fnmatch(file, ".*")
                                                   or file.startswith("~$")):
                    paths.append(os.path.join(dirpath, file))
                else:
                    continue
        return paths

    def sniff_type(self, document):
        "Check first five paragraphs in a document to determine the reader."
        regex = '\w+:'
        reader = {'NameReader': 0, 'ItalicReader': 0, 'BoldReader': 0,
                  'ListReader': 0}
        for i in range(5):
            if re.match(regex, document.paragraphs[i].text):
                reader['NameReader'] += 1
            i = False
            b = False
            for run in document.paragraphs[i].runs:
                if run.italic:
                    i = True
                if run.bold:
                    b = True
            if i:
                reader['ItalicReader'] += 1
            if b:
                reader['BoldReader'] += 1
            if document.paragraphs[i].style.name == 'List Paragraph':
                reader['ListReader'] += 1
        if max(reader) == 0:
            raise TypeError("File cannot be read.")
        else:
            return READERS[max(reader.keys(), key=(lambda k: reader[k]))]

    def read(self, folder, remove=False):
        self.remove = remove
        paths = self.get_paths(folder)
        corpus = {'File': [], 'Content': []}
        for path in paths:
            with open(path, 'rb') as f:
                doc = docx.Document(f)
                reader = self.sniff_type(doc)
                r = reader(doc)
                content = r.join_q_and_a(remove=remove)
                for i in content:
                    corpus['File'].append(path)
                    corpus['Content'].append(i)
        self.corpus = pd.DataFrame.from_dict(corpus)

    def segment(self):
        files = sorted(set(self.corpus['File']))
        seg_corpus = []
        for i in files:
            subset = self.corpus[self.corpus['File'] == i]
            seg_corpus.append(simple_distance(subset))
        seg_corpus = pd.concat(seg_corpus)
        self.seg_corpus = seg_corpus

    def save_data(self, path):
        self.seg_corpus.to_csv(path, index=False)
