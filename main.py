####################
# main.py
# version 1.0.0
# Python 3.6.2
####################


from more_itertools import unique_everseen
import pandas as pd

from scripts.python.concept_annotator import *
from scripts.python.ontology_explorer import OntologyEx

# import script that downloads and processes ontologies from the PheKnowLator project
import sys
sys.path.insert(0, '/Users/tiffanycallahan/Dropbox/GraduateSchool/PhD/LabWork/PheKnowLator/scripts/python')
import DataSources


def preprocess_sentences(sentence):
    """Preprocesses an input sentence by: lowering the case, removing non-alphanumeric characters, tokenizing,
    and removing English stop words.

    Args:
        sentence: A string representing a sentence of text

    Returns:
        A string of text which has been preprocessed
    """

    # replace all non-alphanumeric characters with spaces
    lower_nopunct = re.sub(' +', ' ', re.sub(r'[^a-zA-Z0-9\s\-]', ' ', sentence.lower()))

    # tokenize & remove punctuation
    token = list(unique_everseen(RegexpTokenizer(r'\w+').tokenize(lower_nopunct)))

    # remove stop words & perform lemmatization
    token_stop = [str(x) for x in token if x not in stopwords.words('english')]
    # token_lemma = [str(WordNetLemmatizer().lemmatize(x)) for x in token if x not in stopwords.words('english')]

    return token


def main():

    ######################
    # PROCESS ONTOLOGIES #
    ######################
    # read in ontologies - using script from PheKnowLator repo (https://github.com/callahantiff/PheKnowLator)
    ont = DataSources.OntData('resources/ontology_source_list.txt')
    ont.file_parser()
    ont.get_data_type()
    ont.get_source_list()
    ont.url_download()
    ont.get_data_files()
    ont.source_metadata()
    ont.get_source_metadata()
    ont.write_source_metadata()

    # obtain classes, DbXRefs, labels, definitions, and Synonyms for each
    ont_explorer = OntologyEx()
    onts = {'DOID': ['resources/ontologies/doid_without_imports.owl', ['SNOMED', 'UMLS']],
            'HP': ['resources/ontologies/hp_without_imports.owl', ['SNOMED', 'UMLS']],
            'VO': ['resources/ontologies/vo_without_imports.owl', [None]],
            'NCBITaxon': ['resources/ontologies/ncbitaxon_without_imports.owl', [None]],
            'PR': ['resources/ontologies/pr_without_imports.owl', ['UniProtKB']],
            'CHEBI': ['resources/ontologies/chebi_without_imports.owl', ['DrugBank', 'ChEMBL', 'UniProt']],
            'NCIT': ['resources/ontologies/ncit_without_imports.owl', [None]]}

    ont_explorer.ont_info_getter(onts)

    # load ontologies
    ont_names = ['NCIT', 'CHEBI', 'PR', 'NCBITaxon', 'VO', 'HP', 'DOID']
    ontology_data = ont_explorer.ont_loader(ont_names)

    # convert dictionaries to pandas data frames (works for synonyms and class information)
    ont_syn = ontology_data['ncit_without_imports_synonyms']
    ont_cls = ontology_data['ncit_without_imports_classes']

    ont_cls = {}
    ont_syn = {}

    for keys in ontology_data.keys():

        if 'classes' in keys:
            ont_cls.update(ontology_data[keys])

        if 'synonyms' in keys:
            ont_syn.update(ontology_data[keys])

    ont_labels = {}
    items = len(ont_cls)
    for k, v in ont_cls.items():
        items -= 1
        print('{0}/{1}'.format(items, len(ont_cls)))
        syn = [x for y in [(key, val[1]) for key, val in ont_syn.items() if v[0] == val[0]] for x in y]
        ont_labels[v[0]] = [k, '|'.join(set([k, v[1]] + syn))]

    ont_id = []
    ont_label = []
    ont_strings = []
    for k,v in ont_labels.items():
        print(k, v)
        ont_id.append(k)
        ont_label.append(v[0])
        ont_strings.append(v[1])

    ont_data = pd.DataFrame({'ont_id': ont_id, 'ont_label': ont_label, 'ont_strings': ont_strings})
    ont_data.to_csv('resources/ontologies/all_onts_dict.csv', index=None, header=True)
    ont_data = pd.read_csv('resources/ontologies/proc_ont_dict.csv', header=0, skiprows=0)

    ####################################
    # DOWNLOAD + PROCESS CLINICAL DATA #
    ####################################
    input_file = ['resources/programming/google_api/client_secret.json',
                  'https://www.googleapis.com/auth/drive',
                  'Procs_Ontology_Mapping',
                  'original_OMOP_download_4.1'
                  '1.2019']

    proc_map = Procedures(input_file)
    proc_map.annotator_type()
    proc_map.read_data()
    data = proc_map.get_data()

    # # pre-process data sources  -  (id: index_VOCAB_CODE_gram#_string.string)
    # identifier = ['Procedure_Vocabulary', 'Procedure_ID']
    # definition = ['Procedure_Label', 'Procedure_Synonym']
    # clinical_corpus_123 = list(set(proc_map.data_pre_process(identifier, definition, '|', [1, 2, 3])))
    # clinical_corpus_0 = list(set(proc_map.data_pre_process(identifier, definition, '|', [])))
    # clinical_corpus_1 = list(set(proc_map.data_pre_process(identifier, definition, '|', [1])))
    # clinical_corpus_2 = list(set(proc_map.data_pre_process(identifier, definition, '|', [2])))
    # clinical_corpus_3 = list(set(proc_map.data_pre_process(identifier, definition, '|', [3])))

    input_text = []

    for i, row in data[['ANCESTOR_LABEL', 'ANCESTOR_SYN', 'Procedure_Label', 'Procedure_Synonym']].iterrows():
        print(i)
        input_text.append(' '.join(preprocess_sentences(row['Procedure_Label'] + ' ' + row['Procedure_Synonym'])))
        input_text.append(' '.join(preprocess_sentences(row['Procedure_Label'] + ' ' + row['Procedure_Synonym'] + ' ' +
                                                        row['ANCESTOR_LABEL'] + ' ' + row['ANCESTOR_SYN'])))

    for i, row in ont_data.iterrows():
        print(i)
        try:
            input_text.append(' '.join(preprocess_sentences(row['ont_label'] + ' ' + row['ont_strings'])))
        except TypeError:
            pass

    processed_data = pd.DataFrame(dict(LABEL=[x for x in input_text]))
    processed_data.to_csv(r'resources/fasttext_input.csv', header=None, index=None)

    ncit = pd.read_csv('resources/NCIT.csv', header=0, skiprows=0, error_bad_lines=False, index_col=False, dtype='unicode')

    ncit_reduced = ncit[['Class ID',
 'Preferred Label',
 'Synonyms',
 'Definitions',
 'Obsolete',
 'CUI',
 'Semantic Types',
 'Parents',
 'ALT_DEFINITION',
 'Anatomic_Structure_Has_Location',
 'Anatomic_Structure_Is_Physical_Part_Of',
 'CHEBI_ID',
 'code',
 'def-definition',
 'def-source',
 'DEFINITION',
 'Display_Name',
 'EntrezGene_ID',
 'FULL_SYN',
 'GenBank_Accession_Number',
 'go-term',
 'GO_Annotation',
 'HGNC_ID',
 'Maps_To',
 'NCBI_Taxon_ID',
 'OMIM_Number',
 'Preferred_Name',
 'Procedure_Has_Completely_Excised_Anatomy',
 'Procedure_Has_Excised_Anatomy',
 'Procedure_Has_Imaged_Anatomy',
 'Procedure_Has_Partially_Excised_Anatomy',
 'Procedure_Has_Target_Anatomy',
 'Procedure_Has_Target_Disease',
 'Procedure_May_Have_Completely_Excised_Anatomy',
 'Procedure_May_Have_Excised_Anatomy',
 'Procedure_May_Have_Partially_Excised_Anatomy',
 'Procedure_Uses_Manufactured_Object',
 'PubMedID_Primary_Reference',
 'Semantic_Type',
 'term-group',
 'term-name',
 'term-source',
 'UMLS_CUI',
 'Use_For',
 'xRef',
 'xRef Source']]

    ncit_reduced = ncit_reduced.loc[ncit_reduced['Obsolete'] != 'true']
    ncit_reduced.to_csv(r'resources/ncit_edit.csv', header=1, index=None)

    # # pre-process data sources - ontology
    # proc_map.set_data(ont_data)
    # ontology_corpus_123 = list(set(proc_map.data_pre_process(['ont_id'], ['ont_strings'], '|', [1, 2, 3])))
    # ontology_corpus_0 = list(set(proc_map.data_pre_process(['ont_id'], ['ont_strings'], '|', [])))
    # ontology_corpus_1 = list(set(proc_map.data_pre_process(['ont_id'], ['ont_strings'], '|', [1])))
    # ontology_corpus_2 = list(set(proc_map.data_pre_process(['ont_id'], ['ont_strings'], '|', [2])))
    # ontology_corpus_3 = list(set(proc_map.data_pre_process(['ont_id'], ['ont_strings'], '|', [3])))
    #
    # # combine sources  (n=)
    # corpus_0 = clinical_corpus_0 + ontology_corpus_0
    # corpus_1 = clinical_corpus_1 + ontology_corpus_1
    # corpus_2 = clinical_corpus_2 + ontology_corpus_2
    # corpus_3 = clinical_corpus_3 + ontology_corpus_3
    # corpus_123 = clinical_corpus_123 + ontology_corpus_123
    #
    # # proc_map.set_data(corpus)
    #
    # ########################
    # # CALCULATE SIMILARITY #
    # ########################
    # # convert data to a tf-idf matrix
    # tf = TfidfVectorizer(preprocessor=None, use_idf=True, norm="l2", lowercase=False, ngram_range=(1, 1))
    # tfidf_matrix_0 = tf.fit_transform([content for var, content in corpus_0])
    # tfidf_matrix_1 = tf.fit_transform([content for var, content in corpus_1])
    # tfidf_matrix_2 = tf.fit_transform([content for var, content in corpus_2])
    # tfidf_matrix_3 = tf.fit_transform([content for var, content in corpus_3])
    # tfidf_matrix_123 = tf.fit_transform([content for var, content in corpus_123])
    #
    # # print(tfidf_matrix.shape)
    # # tf.get_feature_names()
    # # proc_map.set_data(tfidf_matrix)
    #
    # # SCORE DATA + WRITE OUT RESULTS
    # scored = score_variables(var_col, data, filter_data, corpus, tfidf_matrix, len(data)-1)
    # len(scored) #4013114
    #
    #
    #
    #
    #
    #
    # def mapper(data, dic, dict_syn, dict_db):
    #
    #     widgets = [Percentage(), Bar(), FormatLabel('(elapsed: %(elapsed)s)')]
    #     pbar = ProgressBar(widgets=widgets, maxval=len(data))
    #     matches = []
    #
    #     for names, values in pbar(data.iterrows()):
    #         omop = values['OMOP']
    #         sme = values['SNOMED']
    #         sn = str(values['SNOMED_LABEL'].encode("utf-8")).lower().rstrip()
    #         ac_map = values['ANCESTOR']
    #         al = re.sub(r"^\s+|\s+$", "", str(values['ANCESTOR_LABEL'].encode("utf-8")).lower())
    #         cui = values['CUI']
    #         ac_cui = values['ANCESTOR_CUI']
    #
    #         ont0 = []; ont_id0 = []; map0 = []; ont1 = []; ont_id1 = []; map1 = []; ont2 = []; ont_id2 = [];
    #         map2 = [];
    #         ont3 = []; ont_id3 = []; map3 = []; ont4 = []; ont_id4 = []; map4 = []; ont5 = []; ont_id5 = [];
    #         map5 = [];
    #         ont6 = []; ont_id6 = []; map6 = []; ont7 = []; ont_id7 = []; map7 = []
    #
    #         # for ac in str(ac_map).split("|"):
    #         if ("SNOMED:" + str(sme) in dict_db.keys()) or\
    #            (sn in dict_syn.keys()) or (sn in dic.keys()) or \
    #            (cui in dict_db.keys()) or \
    #            (len([x for x in ac_cui.split("|") if str(x) in dict_db.keys()])>0) or \
    #            (len([str(x) for x in str(ac_map).split("|") if "SNOMED:" + str(x) in dict_db.keys()])>0) or \
    #            (len([str(x) for x in str(al).split(" | ") if str(x) in dic.keys()])>0) or \
    #            (len([str(x) for x in str(al).split(" | ") if str(x) in dict_syn.keys()])>0):
    #
    #             if "SNOMED:" + str(sme) in dict_db.keys():
    #                 ont1 += [" | ".join([x for x in dict_db["SNOMED:" + str(sme)] if 'http' in x])]
    #                 ont_id1 += [" | ".join([x for x in dict_db["SNOMED:" + str(sme)] if 'http' not in x])]
    #                 map1 += ["SNOMED_DbXRef"]
    #             if cui in dict_db.keys():
    #                 ont0 += [" | ".join([x for x in dict_db[cui] if 'http' in x])]
    #                 ont_id0 += [" | ".join([x for x in dict_db[cui] if 'http' not in x])]
    #                 map0 += ["UMLS_DbXRef"]
    #             if sn in dict_syn.keys():
    #                 ont2 += [" | ".join([x for x in dict_syn[sn] if 'http' in x])]
    #                 ont_id2 += [" | ".join([x for x in dict_syn[sn] if 'http' not in x])]
    #                 map2 += ["Synonym"]
    #             if sn in dic.keys():
    #                 ont3 += [dic[sn][0]]
    #                 ont_id3 += [sn]
    #                 map3 += ["Label"]
    #
    #             if len(filter(None, [x if "SNOMED:" + str(x) in dict_db.keys() else "" for
    #             x in str(ac_map).split("|")]))>0:
    #                 res = [x for y in [dict_db.get("SNOMED:" + str(x)) for x in str(ac_map).split("|")
    #                 if "SNOMED:"+str(
    #                     x) in  dict_db.keys()] for x in y]
    #                 ont4 += [" | ".join([x for x in res if 'http' in x])]
    #                 ont_id4 += [" | ".join([x for x in res if 'http' not in x])]
    #                 map4 += ["SNOMED_DbXRef - Ancestor"]
    #             if len(filter(None, [x if str(x) in dict_db.keys() else "" for x in ac_cui.split(" | ")]))>0:
    #                 res = [x for y in [dict_db.get(str(x)) for x in ac_cui.split(" | ") if str(x) in dict_db.keys()]
    #                 for x in y]
    #                 ont7 += [" | ".join([x for x in res if 'http' in x])]
    #                 ont_id7 += [" | ".join([x for x in res if 'http' not in x])]
    #                 map7 += ["UMLS_DbXRef - Ancestor"]
    #             if len(filter(None, [x if str(x) in dict_syn.keys() else "" for x in al.split(" | ")]))>0:
    #                 res = [x for y in [dict_syn.get(str(x)) for x in al.split(" | ") if str(x) in dict_syn.keys()]
    #                 for x in y]
    #                 ont5 += [" | ".join([x for x in res if 'http' in x])]
    #                 ont_id5 += [" | ".join([x for x in res if 'http' not in x])]
    #                 map5 += ["Synonym - Ancestor"]
    #             if len(filter(None, [x if x in dic.keys() else [] for x in al.split(" | ")]))>0:
    #                 res = [x for y in [dic.get(x) for x in al.split(" | ") if str(x) in dic.keys()] for x in y]
    #                 ont6 += [" | ".join([x for x in res if 'http' in x])]
    #                 ont_id6 += [" | ".join([x for x in al.split(" | ") if str(x) in dic.keys()])]
    #                 map6 += ["Label - Ancestor"]
    #
    #         # condense and group matches
    #         ids1 = [[x.split(" | ") if len(ont1)>0 else "" for x in ont1]] +\
    #                [[x.split(" | ") if len(ont0)>0 else "" for x in ont0]] +\
    #                [[x.split(" | ") if len(ont3)>0 else "" for x in ont3]] +\
    #                [[x.split(" | ") if len(ont2)>0 else "" for x in ont2]]
    #         nts1 = [[x.lower().split(" | ") if len(ont_id1)>0 else "" for x in ont_id1]] + \
    #                [[x.lower().split(" | ") if len(ont_id0)>0 else "" for x in ont_id0]] + \
    #                [[x.lower().split(" | ") if len(ont_id3)>0 else "" for x in ont_id3]] +\
    #                [[x.lower().split(" | ") if len(ont_id2)>0 else "" for x in ont_id2]]
    #         mps1 = [x.strip() + "(" + str(len(ids1[0][0])) + ")" if len(ids1)>=1 else "" for x in map1]+ \
    #                [x.strip() + "(" + str(len(ids1[1][0])) + ")" if len(ids1)>1 else "" for x in map0]+ \
    #                [x.strip() + "(" + str(len(ids1[2][0])) + ")" if len(ids1)>2 else "" for x in map3] +\
    #                [x.strip() + "(" + str(len(ids1[3][0])) + ")" if len(ids1)>3 else "" for x in map2]
    #         ids2 = [[x.split(" | ") if len(ont4) > 0 else ont4 for x in ont4]] + \
    #                [[x.split(" | ") if len(ont7) > 0 else ont7 for x in ont7]] + \
    #                [[x.split(" | ") if len(ont6) > 0 else ont6 for x in ont6]] + \
    #                [[x.split(" | ") if len(ont5) > 0 else ont5 for x in ont5]]
    #         nts2 = [[x.lower().split(" | ") if len(ont_id4) > 0 else "" for x in ont_id4]] + \
    #                [[x.lower().split(" | ") if len(ont_id7) > 0 else "" for x in ont_id7]] + \
    #                [[x.lower().split(" | ") if len(ont_id6) > 0 else "" for x in ont_id6]] + \
    #                [[x.lower().split(" | ") if len(ont_id5) > 0 else "" for x in ont_id5]]
    #         mps2 = [x.strip() + "(" + str(len(ids2[0][0])) + ")" if len(ont4) > 0 else "" for x in map4] + \
    #                [x.strip() + "(" + str(len(ids2[1][0])) + ")" if len(ont7) > 0 else "" for x in map7] + \
    #                [x.strip() + "(" + str(len(ids2[2][0])) + ")" if len(ont6) > 0 else "" for x in map6] + \
    #                [x.strip() + "(" + str(len(ids2[3][0])) + ")" if len(ont5) > 0 else "" for x in map5]
    #
    #         sn_id = " | ".join(set(filter(None, [x.split("/")[-1] for y in [x for y in ids1 for x in y] for x in y])))
    #         sn_nt = " | ".join(set(filter(None, [x for y in [x for y in nts1 for x in y] for x in y])))
    #         sn_mp = " | ".join(set(filter(None, mps1)))
    #         an_id = " | ".join(set(filter(None, [x.split("/")[-1] for y in [x for y in ids2 for x in y] for x in y])))
    #         an_nt = " | ".join(set(filter(None, [x for y in [x for y in nts2 for x in y] for x in y])))
    #         an_mp = " | ".join(set(filter(None, mps2)))
    #
    #         matches.append([omop, sme, sn, ac_map, ac_cui, al, sn_id, sn_nt, sn_mp, an_id, an_nt, an_mp])
    #
    #     pbar.finish()
    #
    #     # output results
    #     mapped = pd.DataFrame(dict(OMOP_ID=[x[0] for x in matches],
    #                                ANCESTOR=[x[3] for x in matches],
    #                                SNOMED=[x[1] for x in matches],
    #                                SNOMED_LABEL=[x[2] for x in matches],
    #                                ANCESTOR_LABEL=[x[5] for x in matches],
    #                                ANCESTOR_CUI =[x[4] for x in matches],
    #                                ONT_XREF_ID=[x[6] for x in matches],
    #                                ONT_XREF=[x[7] for x in matches],
    #                                ONT_XREF_MAP=[x[8] for x in matches],
    #                                ONT_SYN_ID=[x[9] for x in matches],
    #                                ONT_SYN=[x[10] for x in matches],
    #                                ONT_SYN_MAP=[x[11] for x in matches]))
    #
    #     mapped_terms = mapped[['OMOP_ID', 'SNOMED', 'SNOMED_LABEL', 'ANCESTOR', 'ANCESTOR_LABEL', 'ANCESTOR_CUI',
    #     'ONT_XREF_ID', 'ONT_XREF', 'ONT_XREF_MAP', 'ONT_SYN_ID', 'ONT_SYN', 'ONT_SYN_MAP']]
    #
    #     mapped_terms = mapped_terms.drop_duplicates(['OMOP_ID', 'SNOMED', 'SNOMED_LABEL', 'ANCESTOR',
    #     'ANCESTOR_LABEL', 'ANCESTOR_CUI', 'ONT_XREF_ID', 'ONT_XREF', 'ONT_XREF_MAP', 'ONT_SYN_ID', 'ONT_SYN',
    #     'ONT_SYN_MAP'], keep="first")
    #
    #     return mapped_terms
