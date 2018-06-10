import requests
import subprocess
import sys

model_pattern = "http://mlmlab.org/mfa/mfa-models/%s.zip"
g2p_pattern = "http://mlmlab.org/mfa/mfa-models/g2p/%s_g2p.zip"

LANG_NAME = sys.argv[1]

subprocess.call(['wget', model_pattern % LANG_NAME])
subprocess.call(['wget', g2p_pattern % LANG_NAME])
