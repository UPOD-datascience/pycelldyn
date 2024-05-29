# -*- coding: utf-8 -*-
"""
preprocessing.py
Functions for pre-processing data.
"""
#%%
import numpy as np
import pandas as pd
import pathlib

#%%
def rename_columns(df, df_type, path_dictionary, verbose=True):
    """`rename_columns`

    Rename the columns so that they have computer names as defined
    in the corresponding data dictionary.

    !!! warning
        The Excel sheet with the dictionary information should have the word
        `df_type` in its name (case insensitive).

    !!! tip
        Renaming the columns should always be the first pre-processing step.

    Parameters
    ----------
    df : pandas DataFrame
        The pandas DataFrame.

    df_type : str
        DataFrame of interest. It accepts the following values:

        * `alinity`
        * `sapphire`
        * `sample_pairs`

    path_dictionary : str, pathlib.Path
        Location of the `.xlsx` data dictionary.

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

    # Make sure that the given path is a pathlib.Path.
    path_dictionary = pathlib.Path(path_dictionary)

    # Check that data dictionary exists.
    if not path_dictionary.exists():
        raise Exception(f"Data dictionary {path_dictionary} does not exist.")

    # Get the proper sheet name.
    # Notice we use `with open` to avoid the issue of the dictionary file
    # not being closed. See https://github.com/pandas-dev/pandas/issues/29803#issuecomment-1075031412
    with open(path_dictionary, 'rb') as f:
        excel_file = pd.ExcelFile(f)
    sheet_names = [sheet for sheet in excel_file.sheet_names if df_type in sheet.lower()]
    sheet_name = sheet_names[0]

    # Read the dictionary.
    with open(path_dictionary, 'rb') as f:
        df_dictionary = pd.read_excel(f,
                                      engine='openpyxl',
                                      sheet_name=sheet_name,
                                      header=0)

    # Select the columns of interest.
    df_dictionary = df_dictionary[['Name', 'Computer name']]

    # Convert DataFrame to dictionary.
    df_dictionary_dict = dict(zip(df_dictionary['Name'].values,
                                  df_dictionary['Computer name'].values))

    # Perform the renaming.
    df_renamed = df.rename(columns=df_dictionary_dict)

    if verbose:
        print("\tDONE!")


    return df_renamed



#%%
def clean_dataframe(df, machine, path_dictionary, cols=None, verbose=True):
    """`clean_dataframe`

    Clean categorical and numerical columns of a Sapphire or Alinity
    DataFrame.

    !!! warning
        The Excel sheet with the dictionary information should have the word
        machine name (case insensitive).

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

    machine : str
        The machine of interest. It accepts the following values:

        * `sapphire`
        * `alinity` (preferred) or `alinity hq`

    path_dictionary : str, pathlib.Path
        Location of the `.xlsx` data dictionary.

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

    # Make sure that the given path is a pathlib.Path.
    path_dictionary = pathlib.Path(path_dictionary)

    # Check that data dictionary exists.
    if not path_dictionary.exists():
        raise Exception(f"Data dictionary {path_dictionary} does not exist.")

    # Get the proper sheet name.
    excel_file = pd.ExcelFile(path_dictionary)
    sheet_names = [sheet for sheet in excel_file.sheet_names if machine.lower() in sheet.lower()]
    sheet_name = sheet_names[0]

    # Read the dictionary.
    df_dictionary = pd.read_excel(path_dictionary,
                                  sheet_name=sheet_name,
                                  header=0)

    # Select the columns of interest.
    df_dictionary = df_dictionary[['Computer name', 'Unit', 'Type mapping']]
    df_dictionary = df_dictionary.set_index('Computer name')


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

        col_type = str(df_dictionary.loc[col, 'Type mapping']).lower()

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
