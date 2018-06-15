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

import lm

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
LANGUAGE = sys.argv[4] if len(sys.argv) > 4 else 'spanish'

TEXT = open(TEXT_PATH).read()
WORD_SEQ = [X.strip() for X in TEXT.split()]
WORDS = set(WORD_SEQ)

corpse_dir = 'rush'#tempfile.mkdtemp()
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

acoustic_model = AcousticModel('%s.zip' % (LANGUAGE))
g2p_model = G2PModel('%s_g2p.zip' % (LANGUAGE))

dict_dir = 'rush/dict'#tempfile.mkdtemp()
os.makedirs(dict_dir)
g2pname = 'rush/g2p'

with tempfile.NamedTemporaryFile() as g2pfh:
    d_gen = PhonetisaurusDictionaryGenerator(g2p_model, WORDS, g2pname)#g2pfh.name)
    d_gen.generate()

    dictionary = Dictionary(g2pname, dict_dir)#g2pfh.name, dict_dir)

acoustic_model.validate(dictionary)

aligner = PretrainedAligner(corpus, dictionary, acoustic_model,
                            outdir, temp_directory=corpse_dir_tmp)

#mkgraph needs: 'phones/silence.csl'
open(os.path.join(dict_dir, 'dictionary', 'phones', 'silence.csl'), 'w').write(dictionary.silence_csl)

graph_dir = os.path.abspath(os.path.join(corpse_dir_tmp, 'tri'))

print('lm.getLanguageModel(', os.path.join(dict_dir, 'dictionary'), graph_dir, WORD_SEQ)
lmret = lm.getLanguageModel(os.path.join(dict_dir, 'dictionary'), graph_dir, WORD_SEQ)
print("lmret", lmret)

#words_path = os.path.join(aligner.tri_directory, 'words.txt')
#mdl_path = os.path.join(aligner.tri_directory, 'final.mdl')
#feat_path = os.path.join(split_directory, 'cmvndeltafeats.{}'.format(job_name))
#graphs_path = os.path.join(directory, 'utterance_graphs.{}.fst'.format(job_name))

mdl_path = os.path.join(aligner.tri_directory, 'final.mdl')
#dict_dir = aligner.dictionary.output_directory
dict_dir = lmret
feats_path = 'ark:'+os.path.join(aligner.corpus.split_directory, 'cmvndeltafeats.0')

lat_out_path = 'ark:' + os.path.join(aligner.tri_directory, 'lat.1')
#lat_out_path = 'ark:out.lat'

print(['./gmm-transcribe',
       mdl_path,
       dict_dir,
       feats_path,
       lat_out_path])
subprocess.call(['./gmm-transcribe',
                 mdl_path,
                 dict_dir,
                 feats_path,
                 lat_out_path])

# check = aligner.test_utterance_transcriptions()

aligner.do_align()

aligner.export_textgrids()

grid = TextGrid.fromFile(os.path.join(outdir, 'in', '1.TextGrid'))

# Create a simple JSON output
words = [{"word": X.mark,
          "start": float(X.minTime),
          "end": float(X.maxTime)} for X in grid.tiers[0]]

json.dump({"words": words}, open(JSON_OUT, 'w'))
