# -*- coding: utf-8 -*-
"""
quality_control.py
Functions for performing quality control on clean data.

These scripts were adapted from `quality.py` by Bram van Es.
"""
#%%
import numpy as np

import pycelldyn.miscellaneous as misc

#%%
def perform_qc(df, qc_types=['wbc_scatter', 'rbc_scatter', 'plausible_range', 'flags'], df_data_dictionary=None, machine=None, verbose=True):
    """ `perform_qc`

    Perform quality control (QC) on the data of the given DataFrame.
    For more information, see each of the `qc_types`.
            
    Parameters
    ----------
    df : pandas DataFrame
        DataFrame with the clean data to be checked.

        !!! tip
            Cleaning can be done using the function `clean_dataframe`

    qc_types :  list of str
        List of quality control types. Possible values for each element are:
            
        | QC type                            | Description                                                     | Additional comments                                               |
        |------------------------------------|-----------------------------------------------------------------|-------------------------------------------------------------------|
        | `wbc_scatter` or `leuko_scatter`   | QC of parameters regarding the scatter measurement of white blood cells | Not to be confused with WBC counts or sizes               |
        | `rbc` or `erythro`                 | QC of (some) red blood cell parameters.                         | Not all RBC parameters get QC!                                    |
        | `plausible_range`                  | QC of plausible ranges of different parameters                  | Min and max values are defined in the corresponding data dictionary |
        | `flags` or `suspicious_flags`      | QC based on the presence of suspicious values (defined by corresponding flags) |                                                    |
        | `fail` or `failure`                | Set parameter values to `NaN` based on corresponding flags)     |                                                                   |
        | `standard_values`                  | Set standard values to a given set of parameters                | Not recommended!                                                  |
        | `all`                              | All of the previous QC                                          |                                                                   |

    df_data_dictionary : pandas DataFrame, optional
        DataFrame with data dictionary information. Required if 'plausible_range' is in qc_types.
        It should have at least the following columns:

        * `Computer name` - The computer name of each parameter.
        * `Min` - Minimal allowed value
        * `Max` - Maximum allowed value

    machine : str
        What machine does the data correspond to. Possible values are:
        
        * `sapphire` or `sapph` - Sapphire
        * `alinity` or `alin` - Alinity hq

        !!! info
            No functionality yet, but might be useful in the future.

    verbose : bool
        Define if verbose output will be printed (`True`) or not (`False`).

    Returns
    -------
    df_qc : pandas DataFrame
        DataFrame with quality controlled data.
    """
    df_qc = df.copy()

    # Check that qc_types is not empty
    if qc_types == []:
        raise("qc_types is empty.")

    # Check if `all` QCs are needed.
    qc_types_possible = ['wbc_scatter', 'rbc_scatter', 'plausible_range', 'flags', 'fail', 'standard_values']
    if (qc_types == 'all') or ('all' in qc_types):
        qc_types = qc_types_possible

    # Check if plausible_range is requested but df_data_dictionary is not provided
    if ('plausible_range' in qc_types) and (df_data_dictionary is None):
        raise ValueError("df_data_dictionary is required when 'plausible_range' is in qc_types.")

    # Perform each of the QC types.
    for qc in qc_types:

        if qc in qc_types_possible:

            if verbose:
                print(f"Performing QC {qc}...", end="", flush=True)

            match qc:

                case 'wbc_scatter' | 'leuko_scatter':
                    df_qc = qc_wbc_scatter(df_qc)

                case 'rbc' | 'erythro':
                    df_qc = qc_rbc(df_qc)

                case 'plausible_range':
                    df_qc = qc_plausible_range(df_qc, df_data_dictionary)

                case 'flags' | 'suspicious_flags':
                    pass

                case 'fail' | 'failure':
                    pass

                case 'standard_values':
                    df_qc = qc_standard_values(df_qc)

                case '_':
                    print(f"{qc} is not a valid QC. It will be skipped.")

            if verbose:
                print("\tDONE!")

        else:
            print(f"{qc} is not a valid QC. It will be skipped.")

    return df_qc


#%%
def qc_wbc_scatter(df, threshold=1e-14, machine=None, verbose=True):
    """ `qc_wbc_scatter`

    Perform quality control (QC) on the white blood cells (WBCs) scatter
    measurement parameters.

    Namely, it looks at the coefficient of variance (CV) of the following
    parameters:

    * `neutrophil_size_mean`
    * `neutrophil_intracellular_complexity`
    * `neutrophil_lobularity_polarized`
    * `neutrophil_lobularity_depolarized`
    * `neutrophil_dna_staining`
    * `lymphocyte_size_mean`
    * `lymphocyte_intracellular_complexity`

    and if it is below `threshold` (which defaults to `1e-14`), it sets 
    both values (that of the parameter and its corresponding CV) to numpy's 
    `NaN`.
    
    !!! info
        This function was adapted from the original implementation in
        `quality.py` by Bram van Es.

    Parameters
    ----------
    df : pandas DataFrame
        DataFrame with the clean data to be checked.

        !!! tip
            Cleaning can be done using the function clean_dataframe

    threshold : float
        When the CV of any parameter is below the threshold, both the
        parameter and its CV will be replaced by a `NaN`.

    machine : str
        What machine does the data correspond to. Possible values are:

        * `sapphire` or `sapph` - Sapphire
        * `alinity` or `alin` - Alinity hq

        !!! info
            No functionality yet, but might be useful in the future.

    verbose : bool
        Define if verbose output will be printed (`True`) or not (`False`).

    Returns
    -------
    df_qc : pandas DataFrame
        DataFrame with quality controlled data.
    """

    df_qc = df.copy()

    # Get the relevant columns.
    # These are the parameter names (not the CV names).
    cols_wbc_scatter = misc.get_cols_wbc_scatter()

    for col in cols_wbc_scatter:

        # Create the CV parameter name by just appending `_cv` at the end.
        col_cv = col + '_cv'

        # Perform QC only when both the parameter and its corresponding CV
        # column are present in the DataFrame.
        if (col in df_qc.columns) and (col_cv in df_qc.columns):
            df_qc.loc[df[col_cv] < threshold, [col_cv, col]] = np.nan
            
            if verbose:
                print(f"\tQC for WBC scatter parameters performed on {col} and {col_cv}.")

        # Otherwise, do nothing.
        else:
            if verbose:
                print(f"\tColumn {col} and/or {col_cv} not present in DataFrame. No WBC scatter QC performed.")

    return df_qc


#%%
def qc_rbc(df, machine=None, verbose=True):
    """ `qc_rbc`

    Perform quality control (QC) on (some) red blood cells (RBCs) parameters.

    Namely, it looks at the following parameters and if they are below 
    (i.e., `<`), their corresponding threshold, they will be replaced by 
    numpy's `NaN`.
    
    TODO: c_mode_rtc (mode_reti) - why change to NaN when 0?
    
    | Parameter                             | Threshold | Additional comments                                               |
    |---------------------------------------|-----------|-------------------------------------------------------------------|
    | `reticulocytes`                       | `1e-4`    |                                                                   |
    | `reticulocytes_perc`                  | `1e-4`    |                                                                   |
    | `irf`                                 | `1e-4`    | Immature reticulocyte fraction                                    |
    | `rbc_intracellular_complexity`        | `1e-4`    |                                                                   |
    | `rbc_intracellular_complexity_cv`     | `1e-4`    |                                                                   |
    | `rbc_population_position`             | `1e-4`    |                                                                   |
    | `rbc_population_position_cv`          | `1e-4`    |                                                                   |
    | `reticulocyte_population_position`    | `1e-4`    |                                                                   |
    | `reticulocyte_population_position_cv` | `1e-4`    |                                                                   |
    | `mchcr`                               | `1e-4`    | Mean Corpuscular HGB Concentration per Reticulocyte               |
    | `mchr_nl`                             | `1e-4`    | Mean corpuscular hemoglobin per reticulocyte, aka reticulocyte hemoglobin content (in NL units)|
    | `mcvr`                                | `1e-4`    | Mean corpuscular volume (aka mean cell volume) of reticulocytes   |
    | `hdw`                                 | `1e-4`    | Hemoglobin distribution width per RBC                             |
    | `rbc_hypochromic_perc`                | `1e-30`   | Hypochromic RBCs (RBCs with hemoglobin < 28 g/dL) percentage      |
    | `rbc_hyperchromic_perc`               | `1e-30`   | Hyperchromic RBC (RBCs with hemoglobin > 41 g/dL) percentage      |
    
    !!! info
        This function was adapted from the original implementation in
        `quality.py` by Bram van Es.
        
    Parameters
    ----------
    df : pandas DataFrame
        DataFrame with the clean data to be checked.

        !!! tip
            Cleaning can be done using the function clean_dataframe

    machine : str
        What machine does the data correspond to. Possible values are:

        * `sapphire` or `sapph` - Sapphire
        * `alinity` or `alin` - Alinity hq

        !!! info
            No functionality yet, but might be useful in the future.

    verbose : bool
        Define if verbose output will be printed (`True`) or not (`False`).

    Returns
    -------
    df_qc : pandas DataFrame
        DataFrame with quality controlled data.
    """
    
    df_qc = df.copy()

    # Relevant columns.
    cols_rbc = ['reticulocytes',
                'reticulocytes_perc',
                'irf',
                'rbc_intracellular_complexity',
                'rbc_intracellular_complexity_cv',
                'rbc_population_position',
                'rbc_population_position_cv',
                'reticulocyte_population_position',
                'reticulocyte_population_position_cv',
                'mchcr',
                'mchr_nl',
                'mcvr',
                'hdw',
                'rbc_hypochromic_perc',
                'rbc_hyperchromic_perc'
                ]
    
    for col in cols_rbc:

        # Perform QC only when the correpsonding column is present 
        # in the DataFrame.
        if col in df_qc.columns:
            
            # Define threshold. 
            if col in ['rbc_hypochromic_perc', 'rbc_hyperchromic_perc']:
                threshold = 1e-30
            else:
                threshold = 1e-4
            df_qc.loc[df[col] < threshold, col] = np.nan
            
            if verbose:
                print(f"\tQC for RBCs performed on {col}.")

        # Otherwise, do nothing.
        else:
            if verbose:
                print(f"\tColumn {col} not present in DataFrame. No RBC QC performed.")

    return df_qc


#%%
def qc_standard_values(df, machine=None, verbose=True):
    """ `qc_standard_values`

    Perform quality control (QC) by removing rows that do *not* have 
    a predefined standard value.

    Namely, it looks at the following parameters and their corresponding
    (standard) values:
    
    TODO: What is this for? Why remove rows?
    TODO: Why only these parameters?
    TODO: Why hemoglobin in NL units?
    
    | Parameter                             | Value       | Additional comments |
    |---------------------------------------|-------------|---------------------|
    | `rbc_intracellular_complexity`        | `182`       | |
    | `rbc_population_position`             | `85`        | |
    | `neutrophil_size_mean`                | `140`       | |
    | `neutrophil_intracellular_complexity` | `150`       | |
    | `neutrophil_lobularity_polarized`     | `125`       | |
    | `neutrophil_lobularity_depolarized`   | `28`        | |
    | `neutrophil_dna_staining`             | `69`        | |
    | `lymphocyte_size_mean`                | `100`       | |
    | `lymphocyte_intracellular_complexity` | `75`        | |
    | `hb_nl`                               | `6.206e-21` | Hemoglobin (in NL units) |
    | `mch_usa`                             | `0.6206`    | Mean corpuscular hemoglobin (in USA units) |
    | `mchc_usa`                            | `0.6206`    | Mean corpuscular hemoglobin concentration (in USA units) |
    | `rbc_intracellular_complexity_cv`     | `1.59341`   | |
    | `rbc_population_position_cv`          | `7.2`       | |
    
    !!! info
        This function was adapted from the original implementation in
        `quality.py` by Bram van Es.
        
    Parameters
    ----------
    df : pandas DataFrame
        DataFrame with the clean data to be checked.

        !!! tip
            Cleaning can be done using the function clean_dataframe

    machine : str
        What machine does the data correspond to. Possible values are:

        * `sapphire` or `sapph` - Sapphire
        * `alinity` or `alin` - Alinity hq

        !!! info
            No functionality yet, but might be useful in the future.

    verbose : bool
        Define if verbose output will be printed (`True`) or not (`False`).

    Returns
    -------
    df_qc : pandas DataFrame
        DataFrame with quality controlled data.
    """

    df_qc = df.copy()

    # Pair of relevant columns and standard values.
    cols_standard_values = {'rbc_intracellular_complexity': 182,
                            'rbc_population_position': 85,
                            'neutrophil_size_mean': 140,
                            'neutrophil_intracellular_complexity': 150,
                            'neutrophil_lobularity_polarized': 125,
                            'neutrophil_lobularity_depolarized': 28,
                            'neutrophil_dna_staining': 69,
                            'lymphocyte_size_mean': 100,
                            'lymphocyte_intracellular_complexity': 75,
                            'hb_nl': 6.206e-21,
                            'mch_usa': 0.6206,
                            'mchc_usa': 0.6206,
                            'rbc_intracellular_complexity_cv': 1.59341,
                            'rbc_population_position_cv': 7.2,
                            }
    
    for col, value in cols_standard_values:

        # Perform QC only when the corresponding column is present 
        # in the DataFrame.
        if col in df_qc.columns:

            # Remove rows that do not have the corresponding value.
            df_qc = df.loc[lambda x: x[col] != value]
            
            if verbose:
                print(f"\tQC for standard values performed on {col}.")

        # Otherwise, do nothing.
        else:
            if verbose:
                print(f"\tColumn {col} not present in DataFrame. No standard value QC performed.")

    return df_qc


#%%
def qc_plausible_range(df, df_data_dictionary, machine=None, verbose=True):
    """ `qc_plausible_range`

    Perform quality control (QC) by converting values that are below
    or above an given threshold (defined in the data dictionary).
    
    TODO: Why convert to NaN and not clip?
    
    !!! info
        This function was adapted from the original implementation in
        `quality.py` by Bram van Es.
        
    Parameters
    ----------
    df : pandas DataFrame
        DataFrame with the clean data to be checked.

        !!! tip
            Cleaning can be done using the function clean_dataframe
            
    df_data_dictionary : pandas DataFrame
        DataFrame with data dictionary information. It should have
        at least the following columns:

        * `Computer name` - The computer name of each parameter.
        * `Min` - Minimal allowed value
        * `Max` - Maximum allowed value
        
        !!! tip
            If the parameter has no min or max values, these should be
            filled in as a single dash (`-`).

    machine : str
        What machine does the data correspond to. Possible values are:

        * `sapphire` or `sapph` - Sapphire
        * `alinity` or `alin` - Alinity hq

        !!! info
            No functionality yet, but might be useful in the future.

    verbose : bool
        Define if verbose output will be printed (`True`) or not (`False`).

    Returns
    -------
    df_qc : pandas DataFrame
        DataFrame with quality controlled data.
    """

    df_qc = df.copy()
    
    # Check that columns of interest are present in the data dictionary.
    cols_interest = ['Computer name', 'Min', 'Max']
    for col in cols_interest:
        if col not in df_data_dictionary.columns:
            raise Exception(f"Column '{col}' not present in df_data_dictionary")
            
    # Select the data dictionary's columns of interest.
    df_data_dictionary = df_data_dictionary[cols_interest]
    df_data_dictionary = df_data_dictionary.set_index('Computer name')
    
    # Make sure that Min and Max columns are cast to floats properly.
    # `-` are replaced to `np.nan`.
    for col in ['Min', 'Max']:
        df_data_dictionary[col] = df_data_dictionary[col].replace('-', np.nan)
        df_data_dictionary[col] = df_data_dictionary[col].astype(float).fillna(np.nan)


    # Try to perform QC on all data columns.
    for col in df_qc.columns:

        # Check that data column exists in the data dictionary.
        if col in df_data_dictionary.index:

            col_min = df_data_dictionary.loc[col, 'Min']
            col_max = df_data_dictionary.loc[col, 'Max']
            
            # Perform QC only when an existing min limit is found.
            if col_min == col_min:
                df_qc.loc[df_qc[col] < col_min, col] = np.nan
                if verbose:
                    print(f"\tQC for plausible range (min = {col_min}) performed on {col}.")
            else:
                print(f"\tQC for plausible range (min) NOT performed on {col} due to NaN min value.")
            
            # Perform QC only when an existing max limit is found.
            if col_max == col_max:
                df_qc.loc[df_qc[col] > col_max, col] = np.nan
                if verbose:
                    print(f"\tQC for plausible range (max = {col_max}) performed on {col}.")
            else:
                print(f"\tQC for plausible range (max) NOT performed on {col} due to NaN max value.")

        # If the column does not exist, do nothing.
        else:
            if verbose:
                print(f"\tColumn {col} not present df_data_dictionary. No plausible range QC performed.")

    return df_qc
