# -*- coding: utf-8 -*-

import os.path
from pathlib import Path

import pytest
import numpy as np
import pandas as pd
from numpy.testing import assert_equal

from freediscovery.utils import dict2type, sdict_keys
from .base import (parse_res, V01, app, get_features, data_dir,
                   get_features_cached)
from freediscovery.exceptions import (NotFound)


# ============================================================================#
#
#                     Feature extraction
#
# ============================================================================#

def test_get_features(app):
    dsid, pars, _ = get_features_cached(app)

    method = V01 + "/feature-extraction/{}".format(dsid)
    data = app.get_check(method)
    for key, val in list(pars.items()):
        if key in ['data_dir', 'dataset_definition']:
            continue
        assert val == data[key]

def test_delete_feature_extraction(app):
    dsid, pars, _ = get_features(app)

    method = V01 + "/feature-extraction/{}".format(dsid)
    app.delete_check(method)


def test_get_feature_extraction_all(app):
    method = V01 + "/feature-extraction/"
    data = app.get_check(method)
    for row in data:
        del row['norm']
        assert sdict_keys(row) == sdict_keys({'analyzer': 'str',
                     'ngram_range': ['int'], 'stop_words': 'NoneType',
                     'n_jobs': 'int', 'chunk_size': 'int',
                     'data_dir': 'str', 'id': 'str', 'n_samples': 'int',
                     'n_features': 'int', 'use_idf': 'bool',
                     'binary': 'bool', 'sublinear_tf': 'bool', 'use_hashing': 'bool'})


@pytest.mark.parametrize('hashed', [True])
def test_get_feature_extraction(app, hashed):
    dsid, _, _ = get_features_cached(app, hashed=hashed)
    method = V01 + "/feature-extraction/{}".format(dsid)
    data = app.get_check(method)
    assert dict2type(data, collapse_lists=True) == {'analyzer': 'str',
                     'ngram_range': ['int'], 'stop_words': 'NoneType',
                     'n_jobs': 'int', 'chunk_size': 'int', 'norm': 'str',
                     'data_dir': 'str', 'n_samples': 'int',
                     'n_features': 'int', 'use_idf': 'bool',
                     'binary': 'bool', 'sublinear_tf': 'bool', 'use_hashing': 'bool',
                     'filenames': ['str'], 'max_df': 'float', 'min_df': 'float',
                     'parse_email_headers': 'bool', 'n_samples_processed': 'int'}

@pytest.mark.parametrize('hashed', [True])
def test_stop_words_integration(app, hashed):
    url = V01 + '/stop-words/'

    sw_name = 'test1w'
    pars = {'name': sw_name,
            'stop_words': ['and', 'or', 'in']}

    res = app.post_check(url, json=pars)
    assert dict2type(res, collapse_lists=True) == {'name': 'str'}
    assert res['name'] == sw_name

    res = app.get_check(url + sw_name)
    assert dict2type(res, collapse_lists=True) == {'name': 'str',
                                                   'stop_words': ['str']}
    assert res['name'] == sw_name
    assert res['stop_words'] == pars['stop_words']

    dsid, pars, _ = get_features(app, hashed=hashed, stop_words=sw_name)



def test_get_search_filenames(app):

    dsid, _, _ = get_features_cached(app)

    method = V01 + "/feature-extraction/{}/id-mapping".format(dsid)

    def _filter_dict(x, filter_field):
        return {key: val for key, val in list(x.items()) if key == filter_field}

    response_ref = {'internal_id': 'int',
                    'file_path': 'str',
                    'document_id': 'int'}

    # Query 1
    file_path_obj = [{'file_path': val} for val in ['00401.txt', '00506.txt']]
    data = app.post_check(method, json={'data': file_path_obj})
    data = data['data']

    for idx in range(len(data)):
        assert dict2type(data[idx]) == response_ref
    assert [_filter_dict(row, 'file_path') for row in data] == file_path_obj
    assert_equal(np.asarray([row['internal_id'] for row in data])**2,
                 [row['document_id'] for row in data])

    with pytest.raises(NotFound):
        res = app.post(method, json={'data': [{'file_path': '00400.txt'}]})

    # Query 2
    file_path_obj = [{'document_id': 4}, {'document_id': 9}]
    data = app.post_check(method, json={'data': file_path_obj})
    data = data['data']

    for idx in range(len(data)):
        assert dict2type(data[idx]) == response_ref
    assert [_filter_dict(row, 'document_id') for row in data] == file_path_obj
    assert_equal(np.asarray([row['internal_id'] for row in data])**2,
                 [row['document_id'] for row in data])


@pytest.mark.parametrize('ingestion_method', ['file_path', 'content'])
def test_append_documents(app, ingestion_method):
    method = V01 + "/feature-extraction/"
    data = app.post_check(method)
    dsid = data['id']
    method += dsid
    app.post_check(method, json={'data_dir': data_dir})

    data = app.get_check(method)

    # check that the file_path is correctly returned by the id-mapping
    data = app.post_check(method + '/id-mapping',
                          json={'return_file_path': False})
    assert dict2type(data['data'][0]) == \
        {'document_id': 'int', 'internal_id': 'int'}

    data = app.post_check(method + '/id-mapping',
                          json={'return_file_path': True})
    assert dict2type(data['data'][0]) == \
        {'document_id': 'int', 'file_path': 'str', 'internal_id': 'int'}
    db_old = data['data']

    dataset_definition = []
    for idx, row in enumerate(db_old):
        row_out = {'document_id': idx + 10}
        if ingestion_method == 'file_path':
            row_out['file_path'] = os.path.join(data_dir, row['file_path'])
        elif ingestion_method == 'content':
            with Path(data_dir, row['file_path']).open('rt', encoding='utf-8') as fh:
                row_out['content'] = fh.read()
        dataset_definition.append(row_out)

    app.post_check(method + '/append',
                   json={'dataset_definition': dataset_definition})
    data = app.post_check(method + '/id-mapping',
                          json={'return_file_path': True})

    db_old = pd.DataFrame(db_old)
    db_new = pd.DataFrame(data['data'])
    assert db_old.shape[0]*2 == db_new.shape[0]

def test_remove_documents(app):
    method = V01 + "/feature-extraction/"
    data = app.post_check(method)
    dsid = data['id']
    method += dsid
    app.post_check(method, json={'data_dir': data_dir})

    data = app.get_check(method)

    data = app.post_check(method + '/id-mapping')
    db_old = pd.DataFrame(data['data'])

    dataset_definition = db_old.iloc[[2, 4]][['document_id']].to_dict(orient='records')
    for row in dataset_definition:
        # convert int64 to int
        row['document_id'] = int(row['document_id'])

    app.post_check(method + '/delete', json={'dataset_definition': dataset_definition})

    data = app.post_check(method + '/id-mapping')

    db_new = pd.DataFrame(data['data'])
    assert db_old.shape[0] - 2 == db_new.shape[0]


@pytest.mark.parametrize('ingestion_method', ['content', 'file_path'])
def test_batch_ingest(app, ingestion_method):
    data_dir1 = Path(data_dir)
    data_dir2 = Path(data_dir).parent.parent / 'ds_002' / 'raw'
    method = V01 + "/feature-extraction/"
    data = app.post_check(method)
    dsid = data['id']
    method += dsid
    for data_dir_k in [data_dir1, data_dir2]:
        # post content from different data dirs
        dd = []
        for fname in data_dir_k.glob('*txt'):
            if ingestion_method == 'content':
                with fname.open('rt', encoding='utf-8') as fh:
                    dd.append({'content': fh.read()})
            elif ingestion_method == 'file_path':
                dd.append({'file_path': str(fname)})
            else:
                raise ValueError('method={} not supported'
                                 .format(ingestion_method))

        app.post_check(method, json={'dataset_definition': dd,
                                     'vectorize': False})
    app.post_check(method, json={'data_dir': str(data_dir1),
                                 'vectorize': False})

    app.post_check(method, json={'vectorize': True})
    data = app.get_check(method)
    assert len(data['filenames']) == 6*3
    assert data['n_samples'] == 6*3
