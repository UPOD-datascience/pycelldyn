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





#%%
# CHONTIRA
"""Retriving files linking to specific flags. To see how the files were created
please go to get_individual_flags.ipynb in the sanbox folder. These csv files are a bit harder
to automate so please don't lose them """
alin_flags = pd.read_csv('T:/laupodteam/AIOS/Chontira/data/data_20230727/alin_flags.csv')
sapp_flags=pd.read_csv('T:/laupodteam/AIOS/Chontira/data/data_20230727/sapp_flags.csv')

"""These lists contains all matched flags within the machine regargless of whether they
match between machines (Manual matching). Check the csv files to see what I mean. These csv files
are a bit harder to automate so please don't lose them"""
alin_flags_all = pd.read_csv('T:/laupodteam/AIOS/Chontira/data/data_20230727/alin_flags_all.csv')
sapp_flags_all=pd.read_csv('T:/laupodteam/AIOS/Chontira/data/data_20230727/sapp_flags_all.csv')

"""
Paired samples with flags
To get these use this (as an example)

from CellDynComparison.src.utils import alin_sapp_paring as oo

labIds = list(set(sapp.S_labId.values))
link_dict = oo.extract_matching_samples(alin,sapp,labIds,True)

alin_sapp_paring.py can be found in the src/utils folder.
"""
paired_id = pd.read_pickle(r'T:/laupodteam/AIOS/Chontira/data/data_20230727/pairs_normal_non_normal_dictionary.pkl')

paired_values_cols = pd.read_csv('T:/laupodteam/AIOS/Chontira/data/data_20230727/paired_phenotypes.csv')# Hard to fully automate this file, please
#don't lose it.


def prepare_cell_dyn_for_R(alin, sapp, path_to_feather_alin = None, path_to_feather_sapp = None, remove_all_flags = True):
    """
    Preparing the data of the Alinity and the Sapphire for R programming by paring the matching samples together and removing values with flags
    by replacing them with NaN

    Check out the file "L:/laupodteam/AIOS/Chontira/CellDynComparison/R/regression.R on how to use the data translated by this method.
    Paramters
    ---------
        alin: dataframe
            First datafame needed: The Alinity dataframe much have no duplicates and must have
            instance ID -> called INSTANCE_ID
            To get this version of the Alinity or Sapphire datasets, use this as an example

            import pyreadstat

            alin_raw, alin_meta  = pyreadstat.read_sas7bdat('T:/laupodteam/AIOS/Chontira/data/data_20230727/compstud_dle_alin_20230727.sas7bdat', encoding='iso-8859-1')
            sapp_raw, sapp_meta = pyreadstat.read_sas7bdat('T:/laupodteam/AIOS/Chontira/data/data_20230727/compstud_dle_sapph_20230727.sas7bdat', encoding='iso-8859-1')

            from CellDynComparison.src.utils import preprocessing as process

            alin_path = 'T:/laupodteam/AIOS/Chontira/data/data_20230727/alinity_no_duplicates_04082023.feather'
            sapp_path = 'T:/laupodteam/AIOS/Chontira/data/data_20230727/sapphire_no_duplicates_04082023.feather'

            alin, sapp = preprocessing.cell_dyn_drop_duplicates_get_instance_id(alin_raw, sapp_raw, alin_path, sapp_path)

            #preprocessing.py can be found in the src/utils folder.

        sapp: dataframe
            Second datafame needed: The Sapphire dataframe much have no duplicates and must have
            instance ID -> called INSTANCE_ID
        path_to_feather_alin: String, optional
            Path to save the new Alinity dataframe in feather (.feather extension)
        path_to_feather_sapp: String, optional
            Path to save the new Alinity dataframe in feather (.feather extension)
        remove_all_flags: bool, optional
            Get rid of the flags with c_s > 2 as well c_s == 2 or not

    Returns:
    ----------
        alin_sort: dataframe
            The Alinity data for R
        sapp_sort: dataframe
            The Sapphire data for R

    """

    """Getting flags"""
    alin_flags_cols = [c for c in alin.columns if ('c_s' in c)]# Can be changed if flag name change
    sapp_flags_cols = [c for c in sapp.columns if ('c_s' in c)]# Can be changed if flag name change

    alin['ANY_SUSPECT_FLAGS_2']= (alin[alin_flags_cols]==2).sum(axis=1)
    sapp['ANY_SUSPECT_FLAGS_2']= (sapp[sapp_flags_cols]==2).sum(axis=1)

    alin['ANY_SUSPECT_FLAGS']= (alin[alin_flags_cols]>2).sum(axis=1)
    sapp['ANY_SUSPECT_FLAGS']= (sapp[sapp_flags_cols]>2).sum(axis=1)


    alin_n_f_p = alin.loc[alin['INSTANCE_ID'].isin(paired_id['alin'])]
    sapp_n_f_p= sapp.loc[sapp['INSTANCE_ID'].isin(paired_id['sapp'])]

    """
    Getting measurments from Sapphire and the Alinity
    """
    sapp_values_cols = [c for c in sapp.columns if ('c_b' in c)]
    alin_values_cols = [c for c in alin.columns if ('c_b' in c)]
    sapp_alone = list(set(sapp_values_cols)-set(sapp_flags_all['sapp_meas'])) #for keeping track of non-matching parameters
    alin_alone = list(set(alin_values_cols)-set(alin_flags_all['alin_meas']))

    for flag, measure in zip(alin_flags_all['alin_flag'], alin_flags_all['alin_meas']):
        if(not(remove_all_flags)):
            alin_n_f_p[measure] = alin_n_f_p.apply(lambda x:np.NaN if x[flag]==2 else x[measure], axis=1)
        else:
            alin_n_f_p[measure] = alin_n_f_p.apply(lambda x:np.NaN if x[flag]>=2 else x[measure], axis=1)

    for measure in alin_alone:
        if(not(remove_all_flags)):
            alin_n_f_p[measure] = alin_n_f_p.apply(lambda x:np.NaN if x["ANY_SUSPECT_FLAGS_2"]>0 else x[measure], axis=1)
        else:
            alin_n_f_p[measure] = alin_n_f_p.apply(lambda x:np.NaN if x["ANY_SUSPECT_FLAGS_2"]>0 or x["ANY_SUSPECT_FLAGS"]>0 else x[measure], axis=1)

    alin_sort = alin_n_f_p.sort_values(by = ['A_labId'], ignore_index = True)

    for flag, measure in zip(sapp_flags_all['sapp_flag'], sapp_flags_all['sapp_meas']):
        if(not(remove_all_flags)):
            sapp_n_f_p[measure] = sapp_n_f_p.apply(lambda x:np.NaN if x[flag]==2 else x[measure], axis=1)
        else:
            sapp_n_f_p[measure] = sapp_n_f_p.apply(lambda x:np.NaN if x[flag]>=2 else x[measure], axis=1)

    for measure in sapp_alone:
        if(not(remove_all_flags)):
            sapp_n_f_p[measure] = sapp_n_f_p.apply(lambda x:np.NaN if x["ANY_SUSPECT_FLAGS_2"]>0 else x[measure], axis=1)
        else:
            sapp_n_f_p[measure] = sapp_n_f_p.apply(lambda x:np.NaN if x["ANY_SUSPECT_FLAGS_2"]>0 or x["ANY_SUSPECT_FLAGS"]>0 else x[measure], axis=1)

    alin_sort = alin_n_f_p.sort_values(by = ['A_labId'], ignore_index = True)
    sapp_sort = sapp_n_f_p.sort_values(by = ['S_labId'], ignore_index=True)

    if((path_to_feather_alin is not None) or (path_to_feather_sapp is not None)):
        alin_sort.to_feather(path_to_feather_alin)
        sapp_sort.to_feather(path_to_feather_sapp)

    return alin_sort, sapp_sort

def prepare_cell_dyn_for_plots_with_a_specific_flag(alin_df, sapp_df, alin_meas, sapp_meas):
    """
    As the name suggest, prepare the data for plotting of joint plots and bland-altman plots. Can be use for other
    plots also if needed to compare two parameters from sapphire and the alinity with specific flag highlights.
    Most combinations of measurements are fine here as long as they have c_b_.

    The sapphire parameter will have S_ added to the front of the parameter name.

    If there is no specific flag for the parameter, all the flags table will be used for that parameter.

    (It's a messy code, please don't mind it)

    Paramters
    ---------
        alin_df: dataframe
            First datafame needed: The Alinity dataframe much have no duplicates and must have
            instance ID -> called INSTANCE_ID
            To get this version of the Alinity or Sapphire datasets, use this as an example

            import pyreadstat

            alin_raw, alin_meta  = pyreadstat.read_sas7bdat('T:/laupodteam/AIOS/Chontira/data/data_20230727/compstud_dle_alin_20230727.sas7bdat', encoding='iso-8859-1')
            sapp_raw, sapp_meta = pyreadstat.read_sas7bdat('T:/laupodteam/AIOS/Chontira/data/data_20230727/compstud_dle_sapph_20230727.sas7bdat', encoding='iso-8859-1')

            from CellDynComparison.src.utils import preprocessing as process

            alin_path = 'T:/laupodteam/AIOS/Chontira/data/data_20230727/alinity_no_duplicates_04082023.feather'
            sapp_path = 'T:/laupodteam/AIOS/Chontira/data/data_20230727/sapphire_no_duplicates_04082023.feather'

            alin, sapp = preprocessing.cell_dyn_drop_duplicates_get_instance_id(alin_raw, sapp_raw, alin_path, sapp_path)

            #preprocessing.py can be found in the src/utils folder.
        sapp_df: dataframe
            Second datafame needed: The Sapphire dataframe much have no duplicates and must have
            instance ID -> called INSTANCE_ID
        alin_meas: String
            The alinity variable that you want to measure
        sapp_meas: String
            The sapphire variable that you want to measure

    Returns:
    ----------
        all_samples: dataframe
            The combined dataset with the "Hue_sub" column that have the flag indicators
            corresponding to the variables that you want to measure
        colour_dict:dictionary
            Dictionary of the flag colours
            Use this as indicated below to get the rows that correspond to the flag colours:
            c = np.asarray(all_samples['Hue_sub'].map(colour_dict))

    """

    """Getting flags"""
    alin_flags_cols = [c for c in alin_df.columns if ('c_s' in c)]# Can be changed if flag name change
    sapp_flags_cols = [c for c in sapp_df.columns if ('c_s' in c)]# Can be changed if flag name change

    alin_df['ANY_SUSPECT_FLAGS_2']= (alin_df[alin_flags_cols]==2).sum(axis=1)
    sapp_df['ANY_SUSPECT_FLAGS_2']= (sapp_df[sapp_flags_cols]==2).sum(axis=1)

    alin_df['ANY_SUSPECT_FLAGS']= (alin_df[alin_flags_cols]>2).sum(axis=1)
    sapp_df['ANY_SUSPECT_FLAGS']= (sapp_df[sapp_flags_cols]>2).sum(axis=1)

    alin_n_f_p = alin_df.loc[alin_df['INSTANCE_ID'].isin(paired_id['alin'])]
    sapp_n_f_p= sapp_df.loc[sapp_df['INSTANCE_ID'].isin(paired_id['sapp'])]

    sapp_n_f_p.columns = ['S_' + x  for x in sapp_n_f_p.columns]

    alin_n_f_p=alin_n_f_p.sort_values(by='A_labId', ignore_index=  True)
    sapp_n_f_p=sapp_n_f_p.sort_values(by='S_S_labId', ignore_index=  True)

    all_samples = pd.concat([alin_n_f_p, sapp_n_f_p], axis=1)

    sapp_meas_samples = 'S_'+sapp_meas
    alin_fl = "c_s_all"
    sapp_fl = "S_c_s_all"

    if(alin_meas in  alin_flags_all['alin_meas'].values):
        alin_fl = alin_flags_all[alin_flags_all['alin_meas'] == alin_meas].iloc[:,1].values[0]

    if(sapp_meas in  sapp_flags_all['sapp_meas'].values):
        sapp_fl = 'S_'+sapp_flags_all[sapp_flags_all['sapp_meas'] == sapp_meas].iloc[:,1].values[0]

    #all_samples.replace([np.inf, -np.inf], np.nan, inplace=True)
    all_samples.dropna(subset=[sapp_meas_samples, alin_meas], inplace=True)


    num_both_normal = str(len(np.where((all_samples['ANY_SUSPECT_FLAGS_2']==0) & (all_samples["S_ANY_SUSPECT_FLAGS_2"]==0)\
                                       & (all_samples['ANY_SUSPECT_FLAGS']==0) & (all_samples['S_ANY_SUSPECT_FLAGS']==0))[0]))
    num_alin_2 = str(sum(all_samples['ANY_SUSPECT_FLAGS_2']>0))
    num_sapp_2 = str(sum(all_samples["S_ANY_SUSPECT_FLAGS_2"]>0))
    num_both_2 = str(len(np.where((all_samples['ANY_SUSPECT_FLAGS_2']>0)\
                                   & (all_samples["S_ANY_SUSPECT_FLAGS_2"]>0))[0]))
    num_alin_more = str(sum(all_samples['ANY_SUSPECT_FLAGS']>0))
    num_sapp_more = str(sum(all_samples['S_ANY_SUSPECT_FLAGS']>0))
    num_both_more = str(len(np.where((all_samples['ANY_SUSPECT_FLAGS']>0)\
                                   & (all_samples["S_ANY_SUSPECT_FLAGS"]>0))[0]))

    if(alin_fl !="c_s_all"):
        num_both_normal = str(len(np.where((all_samples[alin_fl]<=1) & (all_samples["S_ANY_SUSPECT_FLAGS_2"]==0)\
                                           & (all_samples['S_ANY_SUSPECT_FLAGS']==0))[0]))
        num_alin_2 = str(sum(all_samples[alin_fl]==2))
        num_both_2 = str(len(np.where((all_samples[alin_fl]==2) & (all_samples["S_ANY_SUSPECT_FLAGS_2"]>0))[0]))
        num_alin_more = str(sum(all_samples[alin_fl]>2))
        num_both_more = str(len(np.where((all_samples[alin_fl]>2) & (all_samples["S_ANY_SUSPECT_FLAGS"]>0))[0]))


    if(sapp_fl != "S_c_s_all"):
        num_both_normal = str(len(np.where((all_samples[sapp_fl]<=1) & (all_samples["ANY_SUSPECT_FLAGS_2"]==0)\
                                            &(all_samples['ANY_SUSPECT_FLAGS']==0))[0]))
        num_sapp_2 = str(sum(all_samples[sapp_fl]==2))
        num_both_2 = str(len(np.where((all_samples[sapp_fl]==2) & (all_samples["ANY_SUSPECT_FLAGS_2"]>0))[0]))
        num_sapp_more = str(sum(all_samples[sapp_fl]>2))
        num_both_more = str(len(np.where((all_samples[sapp_fl]>2) & (all_samples["ANY_SUSPECT_FLAGS"]>0))[0]))


    if(sapp_fl != "S_c_s_all" and alin_fl !="c_s_all"):
        num_both_normal = str(len(np.where((all_samples[alin_fl]<=1) & (all_samples[sapp_fl]<=1))[0]))
        num_both_2 = str(len(np.where((all_samples[alin_fl]==2) & (all_samples[sapp_fl]==2))[0]))
        num_both_more = str(len(np.where((all_samples[alin_fl]>2) & (all_samples[sapp_fl]>2))[0]))

    # this commented code is for debugging.
   # print("both_nomral:", num_both_normal, ", alin_2:", num_alin_2, ",sapp_2:",num_sapp_2,",both_2:",num_both_2, ",alin_more:" ,num_alin_more, ",sapp_more:",num_sapp_more, ",both_more:" ,num_both_more)

    old_sapp = sapp_fl
    sapp_fl = sapp_fl[2:]
    both_fl = sapp_fl

    if(sapp_fl != "c_s_all" and alin_fl !="c_s_all"):
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(A) " + alin_fl + " = 2, n="+num_alin_2 if x[alin_fl]==2 else "No suspect, n="+num_both_normal , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(S) " +sapp_fl + " = 2, n="+num_sapp_2 if x[old_sapp]==2 else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(B) " +both_fl + " = 2, n="+num_both_2 if (x[alin_fl]==2) and (x[old_sapp]==2) else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(A) " + alin_fl + " > 2, n="+num_alin_more if x[alin_fl]>2 else x['Hue_sub']  , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(S) " +sapp_fl + " > 2, n="+num_sapp_more if x[old_sapp]>2 else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(B) " +both_fl + " > 2, n="+num_both_more if (x[alin_fl]>2) and (x[old_sapp]>2) else x['Hue_sub'] , axis=1)

    elif(sapp_fl != "c_s_all" and  alin_fl =="c_s_all"):
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(A) " + alin_fl + " > 2, n="+num_alin_more if x["ANY_SUSPECT_FLAGS"]>0 else "No suspect, n="+num_both_normal , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(S) " +sapp_fl + " > 2, n="+num_sapp_more if x[old_sapp]>2 else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(B) " +both_fl + " > 2, n="+num_both_more if (x["ANY_SUSPECT_FLAGS"]>0) and (x[old_sapp]>2) else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(A) " + alin_fl + " = 2, n="+num_alin_2 if x['ANY_SUSPECT_FLAGS_2']>0 else x['Hue_sub']  , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(S) " +sapp_fl + " = 2, n="+num_sapp_2 if x[old_sapp]==2 else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(B) " +both_fl + " = 2, n="+num_both_2 if (x['ANY_SUSPECT_FLAGS_2']>0) and (x[old_sapp]==2) else x['Hue_sub'] , axis=1)

    elif(sapp_fl == "c_s_all" and  alin_fl !="c_s_all"):
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(A) " + alin_fl + " > 2, n="+num_alin_more if x[alin_fl]>2 else "No suspect, n="+num_both_normal , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(S) " +sapp_fl + " > 2, n="+num_sapp_more if x["S_ANY_SUSPECT_FLAGS"]>0 else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(B) " +both_fl + " > 2, n="+num_both_more if (x[alin_fl]>2) and (x["S_ANY_SUSPECT_FLAGS"]>0) else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(A) " + alin_fl + " = 2, n="+num_alin_2 if x[alin_fl]==2 else x['Hue_sub']  , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(S) " +sapp_fl + " = 2, n="+num_sapp_2 if x['S_ANY_SUSPECT_FLAGS_2']>0 else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(B) " +both_fl + " = 2, n="+num_both_2 if (x[alin_fl]==2) and (x['S_ANY_SUSPECT_FLAGS_2']>0) else x['Hue_sub'] , axis=1)

    else:
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(A) " + alin_fl + " > 2, n="+num_alin_more if x["ANY_SUSPECT_FLAGS"]>0 else "No suspect, n="+num_both_normal , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(S) " +sapp_fl + " > 2, n="+num_sapp_more if x["S_ANY_SUSPECT_FLAGS"]>0 else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(B) " +both_fl + " > 2, n="+num_both_more if (x["ANY_SUSPECT_FLAGS"]>0) and (x["S_ANY_SUSPECT_FLAGS"]>0) else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(A) " + alin_fl + " = 2, n="+num_alin_2 if x['ANY_SUSPECT_FLAGS_2']>0 else x['Hue_sub']  , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(S) " +sapp_fl + " = 2, n="+num_sapp_2 if x['S_ANY_SUSPECT_FLAGS_2']>0 else x['Hue_sub'] , axis=1)
        all_samples["Hue_sub"] = all_samples.apply(lambda x: "(B) " +both_fl + " = 2, n="+num_both_2 if (x['ANY_SUSPECT_FLAGS_2']>0) and (x['S_ANY_SUSPECT_FLAGS_2']>0) else x['Hue_sub'] , axis=1)

    all_samples["dot_size"] = all_samples.apply(lambda x: 30 if x['Hue_sub'] == "No suspect, n="+num_both_normal else 15 , axis=1)

    colour_dict = {"No suspect, n="+num_both_normal : "#3778bf",
                    "(S) " +sapp_fl + " = 2, n="+num_sapp_2  : "#750851",
                    "(A) " + alin_fl + " = 2, n="+num_alin_2 : "orange",
                    "(B) " +both_fl + " = 2, n="+num_both_2  : "#23c48b",
                    "(S) " +sapp_fl + " > 2, n="+num_sapp_more : "#4e518b",
                    "(A) " + alin_fl + " > 2, n="+num_alin_more : "#b17261",
                    "(B) " +both_fl + " > 2, n="+num_both_more : "#a8a495"}


    return all_samples, colour_dict
