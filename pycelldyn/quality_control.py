# -*- coding: utf-8 -*-
"""
quality_control.py
Functions for performing quality control on clean data.
"""
#%%
import numpy as np

import pycelldyn.miscellaneous as misc

#%%
def perform_qc(df, qc_types=['wbc_scatter', 'rbc_scatter', 'plausible_range', 'flags'], machine=None, verbose=True):
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
                    pass

                case 'flags' | 'suspicious_flags':
                    pass

                case 'fail' | 'failure':
                    pass

                case 'standard_values':
                    pass

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
                print(f"\tQC performed on {col} and {col_cv}.")

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
                print(f"\tQC performed on {col}.")

        # Otherwise, do nothing.
        else:
            if verbose:
                print(f"\tColumn {col} not present in DataFrame. No RBC QC performed.")

    return df_qc
