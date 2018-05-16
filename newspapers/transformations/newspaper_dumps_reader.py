#!/usr/bin/env python
# Usage: python newspaper_dumps_reader.py <newspaper_library_directory>

import os

from SolrClient import SolrClient, SolrError
from metadata_reader import load_edm_in_xml
from alto_ocr_text import extract_fulltext_4_issue

solrClient = SolrClient("http://144.76.218.178:9192/solr/fulltext")


def load_all_issues_fulltext(newspaper_dir):
    """
    load fulltext file path from newspaper issue directory

    usage: le_temps_full_text = load_issue_alto_files("/europeana-research-newspapers-dump-2nd/National_Library_of_France/Le_Temps")

    :param issue_dir:
    :return:
    """
    all_alto_files = []
    for file in os.listdir(newspaper_dir):
        if file.endswith(".alto.zip"):
            # skip entire issue alto zip file
            if file[0].isdigit():
                all_alto_files.append(os.path.join(newspaper_dir, file))
    return all_alto_files


def load_all_newspapers_from_library(library_dir):
    all_newspapers_dir = []
    for newspaper_dir in os.listdir(library_dir):
        newspaper_abs_dir = os.path.join(library_dir, newspaper_dir)
        if os.path.isdir(newspaper_abs_dir):
            all_newspapers_dir.append(newspaper_abs_dir)
    return all_newspapers_dir


def _get_edm_xml_file(alto_zip_file_path):
    return alto_zip_file_path.replace("alto.zip", "edm.xml")


def index_whole_library_newspapers(library_dir):
    """

    :param library_dir: library directory path that contains all the issues datasets
    :return: None
    """
    all_newspaper_dir = load_all_newspapers_from_library(library_dir)
    print("total [%s] newspapers found from library [%s]" % (len(all_newspaper_dir), library_dir))
    for newspaper_dir in all_newspaper_dir:
        index_whole_newspaper_fulltext(newspaper_dir)


def index_whole_newspaper_fulltext(newspaper_dir):
    """

    :param newspaper_dir: issue directory path that contains all the page fulltext datasets of an issue
    :return:
    """
    issue_all_issue_files = load_all_issues_fulltext(newspaper_dir)
    print("total [%s] issues found from newspaper [%s]" % (len(issue_all_issue_files), newspaper_dir))
    for issue_fulltext_path in issue_all_issue_files:
        index_issue_page_fulltext(issue_fulltext_path)


def index_issue_page_fulltext(issue_fulltext_path):
    """

    :param page_fulltext_path: page fulltext file of an issue
    :return:
    """
    issue_fulltext_pages = extract_fulltext_4_issue(issue_fulltext_path)

    print("total [%s] pages loaded for issue [%s]" %(len(issue_fulltext_pages), issue_fulltext_path))

    bb_resource = load_edm_in_xml(_get_edm_xml_file(issue_fulltext_path))

    if bb_resource is None:
        raise Exception("no edm metadata found for issue [%s]" % issue_fulltext_path)

    bb_resource_dict = bb_resource.to_dict()
    issue_id = bb_resource_dict['issue_id']
    bb_resource_dict.pop('issue_id')
    solr_docs = []
    for issue_fulltext_page in issue_fulltext_pages:
        # combine page fulltext with metadata into every individual Solr doc
        solr_doc = {**issue_fulltext_page.to_edm_json(), **bb_resource_dict}
        # set document id as a combination of issue id and page no
        solr_doc['europeana_id'] = issue_id + "_" + str(issue_fulltext_page.page_no)
        solr_docs.append(solr_doc)

    print("total [%s] solr document size to be indexed for issue [%s]: " % (len(solr_docs), issue_fulltext_path))

    # print(solr_docs)
    response = solrClient.batch_update_documents(solr_docs)
    print("indexing done. status: ", response)

    print(">>>>>>>>>>>>>>>>>>>>>>>")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        news_paper_library_directory_path = str(sys.argv[1])
        print("news_paper_library_directory_path: ", news_paper_library_directory_path)
        index_whole_library_newspapers(news_paper_library_directory_path)
