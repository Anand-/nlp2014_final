
# coding: utf-8

# In[2]:

import pandas as pd


# In[3]:

def get_keyphrase_columns(
        keyphrases,
        indf,
        keyphrase_col='common_chunks',
        read_col='article_chunks',
        make_keyphrase_cols=True
        ):
    """
    takes a list of keyphrases, a dataframe, and a column name where
    the rows keyphrases are kept in a list. 
    
    returns a data frame(index is same as indf) with a row for each document and a column for each keyphrase.
    1 if keyphrase is in document, 0 otherwise. 
    """
    df_chunks=pd.DataFrame(index=indf.index)
    df_chunks[keyphrase_col]=indf[read_col].apply(lambda r: set(r)&freqchunks_set).        apply(lambda r: set([c.encode('utf8', 'ignore') for c in r]))
    
    if make_keyphrase_cols:
        for i,v in enumerate(keyphrases):
            df_chunks[v.encode('utf8', 'ignore')]=df_chunks.common_chunks.apply(lambda r: 1 if v in r else 0)
    
    return df_chunks


# In[4]:

def get_overlaps(keyphrases, indf, keyphrase_col='common_chunks', as_percent=False):
    """
    takes a list of keyphrases, a dataframe, and a column name where
    the rows keyphrases are kept in a list. 
    
    returns a df where each keyphrase has a row and column. cells indicate number
    of rows from indf that had both keyphrases in keyphrase col. 
    
    If as percent is true then the df values are the percentage of times documents
    containing the row label contain the column label. 
    """
    df_chunks=get_keyphrase_columns(keyphrases, indf, keyphrase_col)
    
    chunk_overlap = pd.DataFrame(index=df_chunks.columns[1:])
    
    for i,v in enumerate(keyphrases):
        v = v.encode('utf8', 'ignore')
        chunk_overlap[v]=df_chunks[df_chunks[v]==1][df_chunks.columns[1:]].sum()
    
    if as_percent:
        return chunk_overlap.apply(lambda r: r/max(r), axis=1)
    else:
        return chunk_overlap


# In[5]:

def check_sets(inset, filter_sets, min_matches=1):
    "checks if any of the filter sets contain inset"
    m=0
    for s in filter_sets:
        if s>=inset:
            m+=1
            if m>=min_matches:
                return True
    
    return False


# In[6]:

def get_groups(indf, doc_percents=True, set_filters=None, min_matches=1):
    """
    Returns groups from df of key phrase overlaps.
    
    doc_percents - Whether score should be calculated using
                    #term1/#(term1&term2)
                    otherwise it is just a constant/#(term1&term2)
    """
        
    if doc_percents:
        overlap_freqs=indf.apply(lambda r: r/max(r), axis=1)
    else:
        # divide by const to get most frequent coccurences
        overlap_freqs=indf.apply(lambda r: r/100, axis=1)
    
    # create list of relationships between keyphrases
    relationships = []
    for i, c1 in enumerate(overlap_freqs.columns):
        for c2 in overlap_freqs.columns[i:]:
            if c1==c2:
                continue
            val=(c1,c2,overlap_freqs.loc[c1][[c2]][0], overlap_freqs.loc[c2][[c1]][0])

            relationships.append(val)
    
    # sort relationships by weaker of pair,highest first
    relationships.sort(key=lambda r: min([r[2], r[3]]), reverse=True)
    
    
    # build groups
    term_groups = {}
    groups=[]
    
    for r in relationships:
        if r[0] in term_groups.keys() and r[1] in term_groups.keys():
            # check if both terms have been grouped
            continue
            
        elif r[0] not in term_groups.keys() and r[1] not in term_groups.keys():
            # create new group if neither term groupd
            g = len(groups)
            groups.append([r[0], r[1]])
            term_groups[r[0]]=g
            term_groups[r[1]]=g
        
        # next 2: add ungrouped term to other group's term
        elif r[0] not in term_groups.keys():
            g=groups[term_groups[r[1]]]
            if set_filters is not None and not check_sets(set(g+[r[0]]), set_filters, min_matches):
                continue
            g.append(r[0])
            term_groups[r[0]]=term_groups[r[1]]
        
        elif r[1] not in term_groups.keys():
            g=groups[term_groups[r[0]]]
            if set_filters is not None and not check_sets(set(g+[r[1]]), set_filters, min_matches):
                continue
            g.append(r[1])
            term_groups[r[1]]=term_groups[r[0]]
            
        else:
            continue
        
    return groups


# In[7]:

def get_grouped_df(indf, groups, ordering='ordering', group='group'):
    """
    returns a df with rows and columns sorted in the order groups and with a group column
    """
    column_order=[t for g in groups for t in g]
    row_groups={t:g for g,l in enumerate(groups) for t in l}
    
    df_out = indf.copy(deep=False)
    df_out[ordering]=pd.Series({k:v for v,k in enumerate(column_order)})
    df_out[group]=pd.Series(row_groups)
    
    df_out.sort(ordering, inplace=True)
    show = [ordering, group]+column_order
    return df_out[show]
    

