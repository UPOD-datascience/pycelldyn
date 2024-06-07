# -*- coding: utf-8 -*-
"""
miscellaneous.py
Handy miscellaneous functions.
"""
import pandas as pd
import pathlib

#%%
def read_data_dictionary(path_dictionary_file, machine=None, verbose=True):
    """ `read_data_dictionary`
    
    Read an (Excel) data dictionary file.
    
    !!! info
        The name of the Excel sheet should correspond to the `machine` type 
        (see below).

    Parameters
    ----------
    path_dictionary_file : pathlib.Path or str
        Path to the data dictionary (Excel) file.
        
    machine : str
        What machine does the data correspond to. Possible values are:
        
        * `sapphire` or `sapph` - Sapphire
        * `alinity` or `alin` - Alinity hq

    verbose : bool
        Define if verbose output will be printed (`True`) or not (`False`).

    Returns
    -------
    df_data_dictionary : pandas DataFrame
        pandas DataFrame version of the data dictionary defined in the
        file `path_dictionary`.
    """    
    
    # Make sure that the given path is a pathlib.Path.
    path_dictionary_file = pathlib.Path(path_dictionary_file)

    # Check that data dictionary exists.
    if not path_dictionary_file.exists():
        raise Exception(f"Data dictionary {path_dictionary_file} does not exist.")

    # Get the proper sheet name.
    # Notice we use `with open` to avoid the issue of the dictionary file
    # not being closed. See https://github.com/pandas-dev/pandas/issues/29803#issuecomment-1075031412
    with open(path_dictionary_file, 'rb') as f:
        excel_file = pd.ExcelFile(f)
    sheet_names = [sheet for sheet in excel_file.sheet_names if machine in sheet.lower()]
    sheet_name = sheet_names[0]

    # Read the dictionary.
    with open(path_dictionary_file, 'rb') as f:
        df_data_dictionary = pd.read_excel(f,
                                      engine='openpyxl',
                                      sheet_name=sheet_name,
                                      header=0)
        
    # df_data_dictionary = df_data_dictionary.set_index('Computer name')
        
    return df_data_dictionary

#%%
def get_flag_names(cols_values):
    """ `get_flag_names`

    Parameters
    ----------
    cols_values : list
        Each element is a

    Returns
    -------
    flag_names : list
        Each element is the flag column name corresponding to an element
        of `cols_values`.
    """

    flag_names = []
    for col in cols_values:

        # First, let's look at the special cases (i.e., exceptions)
        if (col == 'hb_nl') or (col == 'hb_usa'):
            flag_name = 'hb_flag'
        elif (col == 'mch_nl') or (col == 'mch_usa'):
            flag_name = 'mch_flag'
        elif (col == 'mchc_nl') or (col == 'mchc_usa'):
            flag_name = 'mchc_flag'
        elif (col == 'mchr_nl') or (col == 'mchr_usa'):
            flag_name = 'mchr_flag'
        elif (col == '') or (col == ''):
            flag_name = ''

        # Otherwise, we can just append `_flag` at the end.
        else:
            flag_name = col + '_flag'

        flag_names.append(flag_name)

    return flag_names

#%%
def get_cols_wbc_scatter():
    """ `get_cols_wbc_scatter`

    Get a list of column names that correspond to scatter measurement of
    white blood cells (WBCs).

    !!! warning
        Not to be confused with columns corresponding to WBC counts or sizes.

    !!! tip
        In order to get the coefficient of variance (CV) columns, just
        append `_cv` to each element of `cols_wbc_measurements`. For
        example:

        `cols_cv = [c + '_cv' for c in get_cols_wbc_measurements()]`

    Parameters
    ----------
    None

    Returns
    -------
    cols_wbc_measurements : list
        List of column names that correspond to scatter measurements of WBCs.
    """
    # TODO: Should we keep this function at all or should this be relegated
    # to the QC functions exclusively?
    
    cols_wbc_scatter = ['neutrophil_size_mean',
                        'neutrophil_intracellular_complexity',
                        'neutrophil_lobularity_polarized',
                        'neutrophil_lobularity_depolarized',
                        'neutrophil_dna_staining',
                        'lymphocyte_size_mean',
                        'lymphocyte_intracellular_complexity'
                        ]

    return cols_wbc_scatter

#%%
def get_cols_with_values(df):
    """ `get_cols_with_values`

    Get a list of column names that correspond to actual parameter values
    (i.e., not flags nor alerts)

    Parameters
    ----------
    df : pandas DataFrame
        Original DataFrame

    Returns
    -------
    cols_with_values : list
        Columns with values based on their corresponding _flag counterparts.

    """
    # Get columns from the original DataFrame with _flag suffix.
    cols_flags = get_elements_with_substring(df.columns, ['_flag'])

    # Obtain the original parameter name by removing the suffix.
    cols_with_values = [col_with_value.replace('_flag', '') for col_with_value in cols_flags ]


    # TODO
    # Correct for flags to correspond to two variables
    # e.g., hb_flag apply to both hb_usa and hb_nl

    return cols_with_values


#%%
def get_elements_with_substring(base_list, substr_list):
    """ `get_elements_with_substring`

    Get elements of a list that have a specific substring.

    !!! tip
        This is a handy function to get flag columns (e.g., columns which
        name end with `_flag` or that start with `flag_`).

    Parameters
    ----------
    base_list : list
        Base lists (for example, `list(df.columns)`)

    substr_list : list
        Each element of the list is a substring to be found.

        !!! tip
            If interested in only one substring, pass a list with one element.

    Returns
    -------
    list
        List with the elements that have the given substring.
        If none, returns an empty list.

    References
    ----------
    * [Filtering a list of strings based on a substring](https://www.geeksforgeeks.org/python-filter-list-of-strings-based-on-the-substring-list/)
    """

    return [str for str in base_list if
             any(sub in str for sub in substr_list)]
