from aligner.aligner.pretrained import PretrainedAligner
from aligner.corpus import Corpus
from aligner.models import AcousticModel, G2PModel
from aligner.dictionary import Dictionary
from aligner.g2p.generator import PhonetisaurusDictionaryGenerator

from textgrid import TextGrid

import json
import os
import subprocess
import sys
import tempfile

# MFA calls binaries from Phonetisaurus and Kaldi
PATHS = ['ext/Phonetisaurus',
         # 'opengrm-ngram-1.3.4/src/bin/',
         'ext/kaldi/tools/openfst/bin',
         'ext/kaldi/src/bin',
         'ext/kaldi/src/gmmbin',
         'ext/kaldi/src/latbin',
         'ext/kaldi/src/featbin']

os.environ['PATH'] = "%s:%s" % (":".join(PATHS), os.environ['PATH'])

TEXT_PATH = sys.argv[1]
AUDIO_PATH = sys.argv[2]
JSON_OUT = sys.argv[3]

WORDS = set(open(TEXT_PATH).read().split())

corpse_dir = tempfile.mkdtemp()
corpse_dir_in = os.path.join(corpse_dir, 'in')
corpse_dir_out = os.path.join(corpse_dir, 'out')
corpse_dir_tmp = os.path.join(corpse_dir, 'tmp')
os.makedirs(corpse_dir_in)
os.makedirs(corpse_dir_out)
os.makedirs(corpse_dir_tmp)

outdir = tempfile.mkdtemp()

# Encode audio into corpse dir
subprocess.call(['ffmpeg', '-i', AUDIO_PATH,
                 '-ar', '16000', '-ac', '1',
                 os.path.join(corpse_dir_in, '1.wav')])

# Copy text file
open(os.path.join(corpse_dir_in, '1.lab'), 'w').write(open(TEXT_PATH).read())

corpus = Corpus(corpse_dir_in, corpse_dir_out)

acoustic_model = AcousticModel('spanish.zip')
g2p_model = G2PModel('spanish_g2p.zip')

dict_dir = tempfile.mkdtemp()

with tempfile.NamedTemporaryFile() as g2pfh:
    d_gen = PhonetisaurusDictionaryGenerator(g2p_model, WORDS, g2pfh.name)
    d_gen.generate()

    dictionary = Dictionary(g2pfh.name, dict_dir)

acoustic_model.validate(dictionary)

aligner = PretrainedAligner(corpus, dictionary, acoustic_model,
                            outdir, temp_directory=corpse_dir_tmp)

check = aligner.test_utterance_transcriptions()

aligner.do_align()
aligner.export_textgrids()

grid = TextGrid.fromFile(os.path.join(outdir, 'in', '1.TextGrid'))

# Create a simple JSON output
words = [{"word": X.mark,
          "start": float(X.minTime),
          "end": float(X.maxTime)} for X in grid.tiers[0]]

json.dump({"words": words}, open(JSON_OUT, 'w'))
