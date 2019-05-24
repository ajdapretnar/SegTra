# Segmentation of Interview Transcripts - SegTra

SegTra is intended for preprocessing of interview transcripts. It splits documents into question-answer paris and joins those pairs that satisfy the condition of the chosen similarity method.

The current implementation is available for Slovenian only, but could be easily adapted to any language that has lemmatization and pos tagging libraries in Python.

## How to run the program

Run segment.py. It executes the following script:

    s = Segmenter()
    s.read('/folder/with/transcripts/')
    s.segment(aq_distance)
    s.save_data('/where/to/save/output.csv')

Segment reads .docx files with interview transcript and outputs a .csv file with segmented question-answer chunks.

## How segments are joined

Available methods:
- aq_distance: joins adjacent segments if Jaccard similarity of the last answer and next question is greater than 0.75.
- chunk_distance: joins adjacent segments if their Jaccard similarity is greater than 0.75.
- aq_cosine: joins adjacent segments if cosine distance of the last answer and next question is below 0.50.
- chunk_cosine: joins adjacent segments if their cosine distance is below 0.50.

## Prerequisites for input

Only .docx files are currently supported. Question-answer identification is done with the following heuristics:

- NameReader reads transcripts that identify speakers with initials/names (e.g. Q:, A:). The first speaker is considered the interviewers, everyone else interviewees.
- ItalicReader considers italicized paragraphs as questions and normal paragraphs as answers.
- BoldReader considers paragraphs in bold as questions and normal paragraphs as answers.
- ListReader considers the first paragraph of the listed item as a question and the following paragraphs as answers.

Transcripts that do not conform to these structures will be ignored.
