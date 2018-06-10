Phonetic Helper Directory (PHD) is a directory of scripts and
instructions for exploring the Montreal Forced Aligner (MFA).

## Installation

A sane build environment is expected, along with ffmpeg and python3.

Pre-trained Spanish language and pronunciation models can be
downloaded by running:

```sh
python3 install/models.py spanish
```

Compilation of Kaldi, Phonetisaurus, and MFA:
```sh
sh install.sh
```

## Usage

```sh
python3 align.py TEXTFILE_IN AUDIOFILE_IN JSON_OUT
```