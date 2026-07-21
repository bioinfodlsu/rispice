import pandas as pd
import os
import wget
import scripts.constants as constants

def importCSV(path):
    return pd.read_csv(path)

def downloadFiles(links, paths=None):
    """
    This function downloads a list of files.

    If given a list of paths, it will check if the file is already existing.
    If it is, the file wouldn't be downloaded.

    Args:
        links (dict): dict where the keys are the accession and the value is the link to download
        paths (dict): dict where the keys are the accession and the value is the path to check.
    """
    # Check if file exists
    if paths is not None:
        for accession in paths.keys():
            file_path = paths[accession]
            if os.path.exists(file_path):
                print(f"The file '{file_path}' for {accession} exists.")
                # remove from files to dl
                del links[accession]

    # Download each file within links
    for accession in links.keys():
        wget.download(links[accession])
        print(f"File for {accession} was downloaded.")

    return

def get_features(path, key="features"):
    """Given a path to the Features file, retrieve the list of features (columns)"""
    df = pd.read_csv(path)
    return df[key].to_list()


def addHistoneSampleToDB(
    df, study, notes=None, path=constants.HISTONE_DB_PATH, cultivar=constants.NIPPONBARE
):
    # Process the new samples
    samples = df[
        ["Accession", "Cultivar", "Tissue", "Histone_Mod", "File_Name", "Link"]
    ].copy()
    samples["Study"] = study
    samples["Cultivar"] = cultivar
    samples["Path"] = (
        ".data/"
        + samples["Study"]
        + "/histone/"
        + samples["Tissue"]
        + "/"
        + samples["File_Name"]
    )
    samples["Notes"] = notes

    # Sort the columns based on the constant
    samples = samples[constants.HISTONE_DB_COLS]
    
    if os.path.exists(path):
        db = importCSV(path)
        db = pd.concat([db, samples], ignore_index=True)
        return db
    else:
        return samples


def addChromatinSampleToDB(
    df, study, notes=None, path=constants.CHROMATIN_DB_PATH, cultivar=constants.NIPPONBARE
):
    # Process the new samples
    samples = df[
        ["Accession", "Cultivar", "Tissue", "Method", "File_Name", "Link"]
    ].copy()
    samples["Study"] = study
    samples["Cultivar"] = cultivar
    samples["Path"] = (
        ".data/"
        + samples["Study"]
        + "/chromatin/"
        + samples["Tissue"]
        + "/"
        + samples["File_Name"]
    )
    samples["Notes"] = notes

    # Sort the columns based on the constant
    samples = samples[constants.CHROMATIN_DB_COLS]
    
    if os.path.exists(path):
        db = importCSV(path)
        db = pd.concat([db, samples], ignore_index=True)
        return db
    else:
        return samples

def addDNAMethSampleToDB(
    df, study, notes=None, path=constants.DNA_METH_DB_PATH, cultivar=constants.NIPPONBARE
):
    # Process the new samples
    samples = df[
        ["Accession", "Cultivar", "Tissue", "File_Name", "Link"]
    ].copy()
    samples["Study"] = study
    samples["Cultivar"] = cultivar
    samples["Path"] = (
        ".data/"
        + samples["Study"]
        + "/dna_meth/"
        + samples["Tissue"]
        + "/"
        + samples["File_Name"]
    )
    samples["Notes"] = notes

    # Sort the columns based on the constant
    samples = samples[constants.DNA_METH_DB_COLS]
    
    if os.path.exists(path):
        db = importCSV(path)
        db = pd.concat([db, samples], ignore_index=True)
        return db
    else:
        return samples

def commitDB(df, path):
    # save db to csv file
    df.to_csv(path, index=False)
