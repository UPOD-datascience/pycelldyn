# -*- coding: utf-8 -*-
"""
preprocessing.py
Functions for pre-processing data.
"""
#%%
import numpy as np
import pandas as pd
import pathlib

import pycelldyn.miscellaneous as misc

#%%
def rename_columns(df, df_data_dictionary, verbose=True):
    """`rename_columns`

    Rename the columns so that they have computer names as defined
    in the given data dictionary.

    !!! tip
        Renaming the columns should always be the first pre-processing step.

    Parameters
    ----------
    df : pandas DataFrame
        The pandas DataFrame.

    df_data_dictionary : pandas DataFrame
        DataFrame with data dictionary information. It should have
        at least the following columns:

        * `Name` - The original name of the column in the raw data
        * `Computer name` - The computer name defined in the dictionary

    verbose : bool
        Define if verbose output will be printed (`True`) or not (`False`).

    Returns
    -------
    df_renamed : pandas DataFrame
        Same as input `df`, but with the columns renamed according
        to the data dictionary mapping.
    """
    if verbose:
        print("Renaming columns...", flush=True, end='')
        
    # Check that columns of interest are present in the data dictionary.
    for col in ['Name', 'Computer name']:
        if col not in df_data_dictionary.columns:
            raise Exception(f"Column '{col}' not present in df_data_dictionary")
            
    # Select the data dictionary's columns of interest.
    df_data_dictionary = df_data_dictionary[['Name', 'Computer name']]

    # Convert DataFrame to dictionary.
    df_data_dictionary_dict = dict(zip(df_data_dictionary['Name'].values,
                                       df_data_dictionary['Computer name'].values))

    # Perform the renaming.
    df_renamed = df.rename(columns=df_data_dictionary_dict)

    if verbose:
        print("\tDONE!")


    return df_renamed



#%%
def clean_dataframe(df, df_data_dictionary, cols=None, verbose=True):
    """`clean_dataframe`

    Clean categorical and numerical columns of a Sapphire or Alinity
    DataFrame.

    !!! info
        To identify what type a column is, this function uses information
        from the given data dictionary:

        * Numerical columns are those that have a `Type` of `int`,
        `float`, or `int (scientific notation)`.
        * Categorical columns are those that have a `Type` of `str`.
        * Columns that fall outside of these types remain unchanged.


    Parameters
    ----------
    df : pandas DataFrame
        The pandas DataFrame.

    df_data_dictionary : pandas DataFrame
        DataFrame with data dictionary information. It should have
        at least the following columns:

        * `Computer name` - The computer name of each parameter.
        * `Type` - Variable type

    cols : list of str
        List with the columns to be cleaned. If `None`,
        all columns will be (attempted to be) cleaned.

    verbose : bool
        Define if verbose output will be printed (`True`) or not (`False`).

    Returns
    -------
    df_clean : pandas DataFrame
        Clean DataFrame.
    """

    if verbose:
        print("Cleaning columns...")

    # Check that columns of interest are present in the data dictionary.
    for col in ['Computer name', 'Type']:
        if col not in df_data_dictionary.columns:
            raise Exception(f"Column '{col}' not present in df_data_dictionary")
            
    # Select the data dictionary's columns of interest.
    df_data_dictionary = df_data_dictionary[['Computer name', 'Type']]
    df_data_dictionary = df_data_dictionary.set_index('Computer name')


    # Define which columns will be cleaned.
    if cols is None:
        cols = df.columns

    # Perform cleaning of columns.
    # This is done one by one and depending on the column type.
    types_numerical = ['int', 'float', 'int (scientific notation)']
    types_categorical = ['str', 'string']

    df_clean = df.copy()
    for col in cols:
        # In case we ever will need to use unit information, we can
        # do so by uncommenting this line:
        # col_unit = str(df_dictionary.loc[col, 'Unit']).lower()

        # If a column name starts with an underscore (_), it means that
        # it is meant to be ignored (for example, in cases when columns
        # are duplicated.
        if col[0] == '_':
            if verbose:
                print(f"- Column {col} is to be ignored.")
            continue

        col_type = str(df_data_dictionary.loc[col, 'Type']).lower()

        if col_type in types_numerical:
            if verbose:
                print(f"+ Cleaning numerical ({col_type}) column {col}...", end='', flush=True)
            df_clean[col] = clean_column_numerical(df, col)

            if verbose:
                print("\t DONE!")

        elif col_type in types_categorical:
            if verbose:
                print(f"+ Cleaning categorical ({col_type}) column {col}...", end='', flush=True)
            df_clean[col] = clean_column_categorical(df, col)
            if verbose:
                print("\t DONE!")
        else:
            if verbose:
                print(f". Column {col} will not be cleaned and left as is.")


    if verbose:
        print("\tDONE!")


    return df_clean


#%%
def clean_column_numerical(df, col):
    """`clean_column_numerical`

    Clean a numerical column. It applies the following steps:

    * Convert empty spaces (i.e., `' '`) to `NaN`s.
    * Convert weird entries with a value of `\\xa0` to `NaN`s.
    * Convert entries with a value of `'nan'` to `NaN`s.
    * Cast to float to ensure that values will be numbers.

    Parameters
    ----------
    df : pandas DataFrame
        The pandas DataFrame.s

    col : string
        Name of the numerical column to be cleaned.

    Returns
    -------
    col_clean: pandas Series
        The clean (numerical) column.
    """
    df_clean = df.copy(deep=True)

    # Clean weird string entries.
    df_clean.loc[df[col]==' ', col] = np.nan
    df_clean.loc[df[col]=='\xa0', col] = np.nan
    df_clean.loc[df[col]=='nan', col] = np.nan

    # Cast to float (i.e., ensure that it will be a number).
    df_clean[col] = df_clean[col].astype(float)

    return df_clean[col]


#%%
def clean_column_categorical(df, col):
    """`clean_column_categorical`

    Clean a categorical column. It applies the following steps:

    * Make strings lower case
    * Remove leading spaces
    * Remove trailing spaces
    * Convert weird entries with a value of `\\xa0` to `NaN`s.

    Parameters
    ----------
    df : pandas DataFrame
        The pandas DataFrame.

    col : str
        Name of the categorical column to be cleaned.

    Returns
    -------
    col_clean: pandas Series
        The clean (categorical) column.
    """

    df_clean = df.copy(deep=True)

    # Make lower case, remove leading/trailing spaces, and convert
    # apostrophes to proper format (’ --> ').
    def _clean_string(string):

        if isinstance(string, str):
            clean_string = string.lower().strip()
            clean_string = clean_string.replace("’", "'")

        else:
            clean_string = string

        return clean_string
    df_clean[col] = df_clean[col].apply(_clean_string)

    # Remove weird string entries.
    df_clean.loc[df[col]=='\xa0', col] = np.nan

    return df_clean[col]
