git submodule init
git submodule update
pip3 install --user -r requirements.txt
sh install/install_kaldi.sh
#sh install/install_openngram.sh
sh install/install_phonetisaurus.sh
sh install/install_mfa.sh
