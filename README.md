# Segmentation of Interview Transcripts

Run segment.py. It executes the following script:

    s = Segmenter()
    s.read('/folder/with/transcripts/')
    s.segment()
    s.save_data('/where/to/save/output.csv')

Segment reads .docx files with interview transcript and outputs a .csv file with segmented question-answer chunks.
