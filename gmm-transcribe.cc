// Based on: gmmbin/gmm-latgen-faster.cc
// & gentle/k3.cc

// Copyright 2009-2012  Microsoft Corporation
//           2013-2014  Johns Hopkins University (author: Daniel Povey)
//                2014  Guoguo Chen
//                2018  RMO

// See ../../COPYING for clarification regarding multiple authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//  http://www.apache.org/licenses/LICENSE-2.0
//
// THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
// WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
// MERCHANTABLITY OR NON-INFRINGEMENT.
// See the Apache 2 License for the specific language governing permissions and
// limitations under the License.


#include "base/kaldi-common.h"
#include "util/common-utils.h"
#include "gmm/am-diag-gmm.h"
#include "tree/context-dep.h"
#include "hmm/transition-model.h"
#include "fstext/fstext-lib.h"
#include "decoder/decoder-wrappers.h"
#include "gmm/decodable-am-diag-gmm.h"
#include "feat/feature-functions.h"  // feature reversal
#include "fstext/fstext-lib.h"
#include "lat/lattice-functions.h"
#include "lat/word-align-lattice.h"


int main(int argc, char *argv[]) {
  using namespace kaldi;
  typedef kaldi::int32 int32;
  using fst::SymbolTable;
  using fst::Fst;
  using fst::StdArc;

  bool allow_partial = false;
  BaseFloat acoustic_scale = 0.1;
  LatticeFasterDecoderConfig config;

  // Blindly adopt config from MFA:
  config.beam = 15.0;		// was 16
  config.lattice_beam = 8.0;	// was 10
  config.max_active = 750;	// was 200

  BaseFloat frame_shift = 0.01;	// XXX: Get from feature_info

  std::string model_in_filename = argv[1],
    dict_dir = argv[2],
    feature_rspecifier = argv[3],
    lattice_wspecifier = argv[4];

  const string word_boundary_filename = dict_dir + "/phones/word_boundary.int";
  const string phone_syms_rxfilename = dict_dir + "/phones.txt";
  const string word_syms_rxfilename = dict_dir + "/words.txt";  
  const string fst_in_str = dict_dir + "/HCLG.fst";
  
  WordBoundaryInfoNewOpts opts; // use default opts
  WordBoundaryInfo word_boundary_info(opts, word_boundary_filename);

  fst::SymbolTable *word_syms =
    fst::SymbolTable::ReadText(word_syms_rxfilename);

  fst::SymbolTable* phone_syms =
    fst::SymbolTable::ReadText(phone_syms_rxfilename);

  TransitionModel trans_model;
  AmDiagGmm am_gmm;
  {
    bool binary;
    Input ki(model_in_filename, &binary);
    trans_model.Read(ki.Stream(), binary);
    am_gmm.Read(ki.Stream(), binary);
  }

  std::string words_wspecifier = "";
  Int32VectorWriter words_writer(words_wspecifier);

  std::string alignment_wspecifier = "";
  Int32VectorWriter alignment_writer(alignment_wspecifier);

  SequentialBaseFloatMatrixReader feature_reader(feature_rspecifier);

  Fst<StdArc> *decode_fst = fst::ReadFstKaldiGeneric(fst_in_str);

  LatticeFasterDecoder decoder(*decode_fst, config);

  decoder.InitDecoding();  
  for (; !feature_reader.Done(); feature_reader.Next()) {
    Matrix<BaseFloat> features (feature_reader.Value());

    DecodableAmDiagGmmScaled gmm_decodable(am_gmm, trans_model, features,
					   acoustic_scale);
    decoder.AdvanceDecoding(&gmm_decodable);
  }
  
  decoder.FinalizeDecoding();

  Lattice final_lat;
  decoder.GetBestPath(&final_lat);
  CompactLattice clat;
  ConvertLattice(final_lat, &clat);

  CompactLattice aligned_clat;

  std::vector<int32> words, times, lengths;
  std::vector<std::vector<int32> > prons;
  std::vector<std::vector<int32> > phone_lengths;

  WordAlignLattice(clat, trans_model, word_boundary_info,
		   0, &aligned_clat);

  CompactLatticeToWordProns(trans_model, aligned_clat, &words, &times,
			    &lengths, &prons, &phone_lengths);

  for (int i = 0; i < words.size(); i++) {
    if(words[i] == 0) {
      // <eps> links - silence
      continue;
    }
    fprintf(stdout, "word: %s / start: %f / duration: %f\n",
	    word_syms->Find(words[i]).c_str(),
	    times[i] * frame_shift,
	    lengths[i] * frame_shift);
    // Print out the phonemes for this word
    for(size_t j=0; j<phone_lengths[i].size(); j++) {
      fprintf(stdout, "phone: %s / duration: %f\n",
	      phone_syms->Find(prons[i][j]).c_str(),
	      phone_lengths[i][j] * frame_shift);
    }
  }

  fprintf(stdout, "done with words\n");
}
