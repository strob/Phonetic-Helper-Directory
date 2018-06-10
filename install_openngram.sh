cd ext
# wget http://www.opengrm.org/twiki/pub/GRM/NGramDownload/opengrm-ngram-1.3.4.tar.gz
# tar xzvf opengrm-ngram-1.3.4.tar.gz
cd opengrm-ngram-1.3.4
export CPPFLAGS="-I`pwd`/../kaldi/tools/openfst/include"
export LDFLAGS="-L`pwd`/../kaldi/tools/openfst/lib/"
echo $CPPFLAGS
echo $LDFLAGS
./configure
make

