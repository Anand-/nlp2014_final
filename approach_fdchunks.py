
# coding: utf-8

# In[1]:

from os import path
import cPickle as pickle

import chunking_util
import grouping_util
import display_util


# In[4]:

def chunk_approach(data_path, chunk_start=0, chunk_end=100, min_matches=3):
    p = open(data_path, 'r')
    df=pickle.load(p)
    chunk_map=chunking_util.get_best_chunks(df, fd_start=chunk_start, fd_end=chunk_end)
    df_overlap=grouping_util.get_overlaps(chunk_map, df)
    df['common_chunks']=grouping_util.get_keyphrase_columns(chunk_map, df, make_keyphrase_cols=False)
    groups=grouping_util.get_groups(df_overlap, doc_percents=False,set_filters=df.common_chunks, min_matches=min_matches)
    
    out={
            'group_df':grouping_util.get_grouped_df(df_overlap,groups),
            'keyphrases':chunk_map
        }
    
    group_data=[]
    for g in groups:
        g_dict={}
        g_set=set(g)
        g_dict['keyphrases']=g_set
        url_list = []
        for url in df[df.common_chunks.apply(lambda r: r>=g_set)].url:
            url_list.append(url)
        
        g_dict['urls']=url_list
        
        group_data.append(g_dict)
    
    out['groups']=group_data
    
    return out

