import subprocess
import os
import tempfile
import sys
import re

ENV = os.environ
ENV["PATH"] += ":" + os.path.abspath("ext/kaldi/src/fstbin/")
ENV["PATH"] += ":" + os.path.abspath("ext/kaldi/tools/openfst/bin/")
ENV["PATH"] += ":" + os.path.abspath("ext/kaldi/src/bin/")

TXT_FST_SCRIPT = './ext/kaldi/egs/rm/s5/local/make_rm_lm.pl'
MKGRAPH_WD = "ext/kaldi/egs/wsj/s5/utils/"

OOV_SYMBOL = '<unk>'

def wordpair_from_word_sequence(word_sequence, output_file):
    word_sequence = [OOV_SYMBOL, OOV_SYMBOL] + word_sequence + [OOV_SYMBOL]
    print(word_sequence)

    # Create a bigram mapping
    bigram = {}
    prev_word = word_sequence[0]
    for word in word_sequence[1:]:
        bigram.setdefault(prev_word, set()).add(word)
        prev_word = word

    # Dump bigram in ARPA wp format thing
    outf = open(output_file, 'w')
    for key in sorted(bigram.keys()):
        outf.write(">%s\n" % (key))
        for word in sorted(bigram[key]):
            outf.write(" %s\n" % (word))

    outf.close()

PROTOTYPE_LANGUAGE_DIR = 'PROTO_LANGDIR/'

def getLanguageModel(dictdir, modeldir, word_seq):
    "Generates a language model to fit the text"

    # Create a language model directory
    lang_model_dir = os.path.abspath(dictdir)
    print('saving language model to', lang_model_dir)

    words_file = os.path.join(dictdir, 'words.txt')
    # words = list(set(word_seq + [OOV_SYMBOL]))
    # open(words_file, 'w').write('\n'.join(['%s %d' % (wd, idx) for (idx, wd) in enumerate(words)]))

    # Save the wordpair
    wordpair_file = os.path.join(lang_model_dir, 'wordpairs.txt')
    wordpair_from_word_sequence(word_seq, wordpair_file)

    # Generate a textual FST
    txt_fst_file = os.path.join(lang_model_dir, 'G.txt')
    open(txt_fst_file, 'wb').write(
        subprocess.check_output([TXT_FST_SCRIPT, wordpair_file]))

    # Generate a binary FST
    bin_fst_file = os.path.join(lang_model_dir, 'G.fst')
    open(bin_fst_file, 'wb').write(subprocess.check_output([
        'fstcompile',
        '--isymbols=%s' % (words_file),
        '--osymbols=%s' % (words_file),
        '--keep_isymbols=false',
        '--keep_osymbols=false',
        txt_fst_file]))

    # Create the full HCLG.fst graph
    subprocess.call(['./mkgraph.sh',
                     lang_model_dir,
                     modeldir,
                     os.path.abspath('rush/graphdir')],
                    env=ENV, cwd=MKGRAPH_WD)
    # subprocess.call(['./mkgraph.sh',
    #                  os.path.join(lang_model_dir, 'langdir'),
    #                  os.path.join(lang_model_dir, 'modeldir'),
    #                  os.path.join(lang_model_dir, 'graphdir')],
    #                 env=ENV, cwd=MKGRAPH_WD)

    # Return the language model directory
    return 'rush/graphdir'

if __name__=='__main__':
    import sys
    wdseq = [X.strip() for X in open(sys.argv[1]).read().split(' ')]
    getLanguageModel(wdseq)
