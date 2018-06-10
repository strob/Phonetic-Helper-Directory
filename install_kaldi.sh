cd ext/kaldi
cd tools/
./extras/check_dependencies.sh
make
cd ../src
./configure
make depend
make
