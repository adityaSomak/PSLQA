# PSL Engine

  This engine is created by building up on the theory presented in the [Hinge-Loss Markov Random Fields and Probabilistic Soft Logic](https://arxiv.org/abs/1505.04406). Even though
  the authors have already published a open-sourced PSL engine, our version offers several advantages:
  - The engine is purely pythonic which makes it easier to interface with many other NLP/Vision libraries.
  - This engine is coded to directly integrate knowledge from ConceptNet and Word2vec. This is the engine that produced the required results in
  [Explicit Reasoning over End-to-End Neural Architectures for Visual Question Answering](https://arxiv.org/abs/1803.08896) which was presented
  in AAAI 2018.
  - We use an off-the-shelf optimization library such as Gurobi engine to run inference and in our experience it is quiet fast.
  - This engine especially built for Q&A. But can be extended to support generic rule-base written in PSL.


## Citation

   If you use or modify this engine for your project, please do not forget to cite:
   ```
   @inproceedings{DBLP:conf/aaai/AdityaYB18,
      author    = {Somak Aditya and Yezhou Yang and Chitta Baral},
      title     = {Explicit Reasoning over End-to-End Neural Architectures for Visual Question Answering},
      booktitle = {Proceedings of the Thirty-Second {AAAI} Conference on Artificial Intelligence,
                   New Orleans, Louisiana, USA, February 2-7, 2018},
      year      = {2018},
      crossref  = {DBLP:conf/aaai/2018},
      url       = {https://www.aaai.org/ocs/index.php/AAAI/AAAI18/paper/view/16446},
      timestamp = {Thu, 03 May 2018 17:03:19 +0200},
      biburl    = {https://dblp.org/rec/bib/conf/aaai/AdityaYB18},
      bibsource = {dblp computer science bibliography, https://dblp.org}
   }
   ```

## Pre-requisites:
   - Gurobi 6.5.0 or Gurobi 6.5.2 (please visit [Gurobi Website](http://www.gurobi.com/academia/for-universities) for license and download information). Please
    note that academic licenses (multiple) are free.
   - install gensim using `pip install gensim` to load word2vec models.
   - install nltk using `pip install nltk`.
   - Other packages to install: `numpy, enum, fuzzywuzzy, sqlite3`

   For ConceptNet and Word2vec, download `conceptnet-numberbatch-201609_en_word.txt` and `GoogleNews-vectors-negative300.bin` and change the paths
   in W2VPredicateSimilarity.py.



**To make changes and run from command Line**:

  Run the following commands:
   - `sudo python setup.py sdist`
   - `sudo pip install --upgrade dist/PSLplus-0.1.tar.gz`

**To Run VQA-model Inference from command-line**:

Use:
   - `python main.py vqa -pslcode <rules-file> -datadir <psl_test_data_dir> -parentDir <pslDataRootDir> -qaData <qaData> -option infer`
   - If you want to run the demo on vqa, use the `test_pslqa.py` under the `vqa_demo/expt2_aaai18` directory:
        - `python2.7 test_pslqa <qatestdir> <pslDataRootDir> <answerFile> -stage 2/3 -split test/dev <startFrom>
        - If you are able to run it successfully and want to produce desired results, play with the summation constraints (`S_ANS` and `S_CAND') in `core/pslground.py'. For example, use
        10.0 for both for the data in expt2_aaai18.

**To Run generic-models Inference from command-line**:

Use:
   - `python main.py generic -pslcode <rules-file> -datadir <psl_test_data_dir> -mention <argument_to_predict> -option infer`
        - The `mention` argument indicates the engine what we want to append a summation constraint for this predicate. For example for the
        vqa the mention argument would be the `ans_candidate`.
   - Note option learn is not implemented for generic pipeline.


**To Run weight-learning from command-line**:
   - Coming Soon

## Disclaimer

   - If you want to augment or fix an issue, please raise an issue in the Issue tab of the project. However, as I am the sole contributor, please note the answers will be infrequent.
   Please feel free to clone and modify based on your needs though. Cheers!
   - If you are looking for all the functionalities of PSL 2.0 in one place, please visit the [original groovy-based Gihub Repo](https://github.com/linqs/psl).


