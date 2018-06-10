cd ext/MFA
pip3 install --user -r requirements.txt
python3 thirdparty/kaldibinaries.py ../kaldi
python3 thirdparty/opengrm_ngram_binaries.py ../opengrm-ngram-1.3.4
python3 thirdparty/phonetisaurus_binaries.py ../Phonetisaurus
