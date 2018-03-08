# -*- coding: utf-8 -*-
"""
Created on Wed Nov 15 11:38:12 2017

@author: 703355681
"""

import py
import time
import pandas
import logging
import warnings
from context import dicomtools


class PacsToolsMixin(object):
    """Shared methods used in pacstools classes

       Common properties:
       ------------------
       data - a pandas data frame that acts as the server map or modality
       specific imaging parameter database

       _dataServerMap - a pandas data frame that acts as the server map,
       storing accession numbers, server locations, etc.

       _fileDataBase  - a py.path.local object specifying the database file
       location.
       """

    @property
    def data(self):
        if self._readonly:
            self._hdf.open()
            data = self._hdf.get(self._hdfKey)
            self._hdf.close()
        else:
            data = self._hdf.get(self._hdfKey)
        return data

    @property
    def _dataMap(self):
        return pandas.DataFrame(columns=list(self._dataTypeMap.keys()))

    @property
    def _fileDatabase(self):
        """:obj: 'py.path.local': Data base file name.

        When setting this property, a str or py.path.local can be provided.
        All str values are converted to py.path.local objects. Moreover, the
        provided file name is checked to ensure the user has appropriate
        privlages

        """
        return self.___fileDataBase

    @_fileDatabase.setter
    def _fileDatabase(self, val):

        # Special case for an empty string input - generate the default full
        # file name
        if not val and hasattr(self, '_modality'):
            val = self._gen_dir_local_storage().join(f'{self._modality}-DB.h5')
        elif not val:
            val = self._gen_dir_local_storage().join('SectraDB.h5')
        elif (type(val) == str):
            val = py.path.local(val)
        elif (type(val) == py.path.local):
            pass
        else:
            raise NotImplementedError(f"{type(val)} is not a supported "
                                      "'_fileDatabase' value.")

        assert(type(val) == py.path.local)
        if not val.dirpath().isdir():
            raise NotADirectoryError(f'"{val.dirpath()}" is not a valid '
                                     'directory. A file name with a valid '
                                     'directory must be sepcified.')

        # Create a back-up
        if self._isbackup and val.isfile() and not self._readonly:
            backup = py.path.local(val.strpath.replace('.h5', '.backup'))
            val.copy(backup)

        self.___fileDataBase = val

        #TODO: I need to make _dataCols, _hdfKey, and _isbackup abstract
        #      properties of PacsToolsMixin

        # Initialize the HDF5 store
        self._hdf = pandas.HDFStore(val)
        if not self._readonly:

            # Initialize the data frame if non-existent
            #FIXME: By initializing all columns in the data frame to None, a
            #       row of None values is created and stored as teh first entry
            #       in the data file. Currently, the SectraListener class can
            #       remove this row, but not the Modality class
            if self._hdfKey not in self._hdf.root:
                df = self._dataMap
                df.loc[0, :] = None
                self._overwrite_hdf(df)

        else:  # Read only...
            self._hdf.close()

    @property
    def _logger(self):
        return logging.getLogger(__name__)

    @property
    def _readonly(self):
        return self.___readonly

    @_readonly.setter
    def _readonly(self, val):
        assert(type(val) == bool)
        self.___readonly = val

    def __del__(self):
        self._hdf.close()
        if hasattr(self, '_serverObj'):
            self._serverObj._hdf.close()

    def copy(self, loc, acc):
        """Copy an exam to a local directory

        Parameters
        ----------
        loc : str or py.path.local
            Target directory in which to copy the imaging exam
        acc : str or list
            Accession number(s) corresponding to the exams to be copied

        Returns
        -------
        success : bool
            True when the copy occurs succesfully

        """

        loc = dicomtools.dirStr2PyPath(loc)
        if type(acc) == str:
            acc = [acc]
        assert (type(acc) == list) and all([type(e) == str for e in acc])

    def _gen_dir_local_storage(self):
        """Generates a local storage directory in the user's "home" folder.
           This directory is used to copy data from PACS before being processed
           and imported into a database."""

        # Get the user's home directory
        val = py.path.local('~', expanduser=True)

        # Determine which paths should be appended. Currently, there is no
        # special case for non-Windows based systems
        if ('Windows' in py.process.cmdexec('ver')):
            val = val.join("AppData", 'PACSimport')
        else:
            strErr = ("Unable to determine the local user directory. Either "
                      "the case hasn't been programmed or the appropriate "
                      "system environment variable doesn't exist.")
            raise NotImplementedError(strErr)

        # Concatenate the unique directory name
        if not val.isdir():
            val.ensure_dir()

            # Provide some user feedback
            print(f'[{time.ctime()}] Temporary storage created: {val}')

        else:
            # Provide some user feedback
            print(f'[{time.ctime()}] Using existing temporary storage: {val}')

        return val

    def _get_exam_dir(self, accession=None, row=-1):
        """Generates the PACS directory for the exam

        Parameters
        ----------
        accession : str
            Accession number to query
        row : int
            Database row index to query

        Returns
        -------
        dir : py.path.local
            Requested exam directory

        Notes
        -----
        A query operation may only be performed with *either* an accession
        number *or* a row index.


        """

        # There are three possible input cases: (1) the user specified an
        # accession number, (2) the user provided an index row, or (3) no user
        # input was given. Handle those cases (and the validation) here
        isAcc = bool(accession)
        isIdx = bool(row+1)  # makes zero index work...
        if (not isAcc and not isIdx) or (isAcc and isIdx):
            raise ValueError('Invalid input... either accession or idxRow must'
                             ' be provided but not both')
        elif isAcc:
            assert(type(accession) == str)

            # This will append the accession number to the current directory.
            #  In the event that the accession number cannont be found, a non-
            # existant path should be returned
            val = py.path.local(accession)

            # Find the exam index
            row = self._dataServerMap[
                            self._dataServerMap.Accession == accession].index
            if (row.size == 0):
                return val
            elif (row.size > 1):
                #TODO: I recently had an accession number (0405343066) show up
                #      twice in two different locations. It appears that a
                #      lumbar myelogram was performed and images from two
                #      different units were acquired (MH_CR900_GEN and
                #      MH_FL_GEN) in the same exam.
                raise NotImplementedError(f'Expected a single index, but '
                                          '{idxRow.size} were found')
            row = row[0]
        elif not(row):
            assert (type(row) == int) and (row >= 0)

        # Get the database entry
        df = self._dataServerMap.loc[row, :]
        return self._get_dir_from_entry(df)

    def _get_dir_from_entry(self, df):
        """Derives a server directory from a database entry

        Parameters
        ----------
        df : pandas.Series or pandas.DataFrame
            Single database entry from which to compute the directory

        Returns
        -------
        dir : py.path.local
            Absolute path to the server directory

        """

        #TODO: currently, the code assumes that a directory "0". In fact, there
        #      was an exam that was recently encountered for which the
        #      directory "0" did not exist. Instead, there was a folder labeled
        #      "0_1". and no "admdata" directory. Perhaps instead of assuming
        #      that "0" exists, instead all directories not titled "admdata"
        #      should be found and further investigated... For the time being,
        #      just verify that the directory exists, skipping it if not.
        d = py.path.local(df.PacsServer)
        if 'folders' not in d.strpath:
            d = d.join('folders')

        return d.join(df.PacsScanner, df.Accession, '0')

    def _map_data_types(self, data, check_category=True):
        """Maps the data frame data types

        Parameters
        ----------
        data : pandas.DataFrame
            Data frame containing data to be mapped

        Returns
        -------
        data : pandas.DataFrame
            Data frame with mapped data types
        check_category : bool
            (Optional) When True, the category of the HDF5 file is checked

        """

        typeMap = self._dataTypeMap
        for c in data.columns:
            if check_category and (typeMap[c] == 'category'):
                # For categorical data, remove any NaN. Replace those values
                # with an empty string
                data[c] = data[c].replace(float('NaN'), '')

                # Load a single entry from the database and attempt to define
                # the categories based on the file's content. If the categories
                # are not the same (i.e., the sets are not equal), create a
                # category based on the union of the two sets
                df = self._hdf.select(self._hdfKey, columns=[c],
                                      start=0, stop=1)
                for cat in set(data[c]):
                    if cat not in df[c].cat.categories:
                        df[c] = df[c].cat.add_categories(cat)
                data[c] = data[c].astype(df[c].dtype)
            else:
                if (typeMap[c] == float):
                    data[c] = data[c].replace('', float('NaN'))
                data[c] = data[c].astype(typeMap[c])

        return data

    def _overwrite_hdf(self, data, partial=False):
        """Overwrites (instead of appending data) the current HDF file

        The current HDF store object is closed, and re-opened in a write only
        mode. After the data is written, the HDF store is returned to an append
        mode.

        **WARNING** No comparison of the data input is made with that currently
        stored in the file. Be careful!

        Parameters
        ----------
        data : pandas.DataFrame
            Data to be written to an HDF5 file
        partial : bool
            When True, the provided data is considered a chunk of the on-disk
            database. The database is loaded and combined with user input

        """

        # Combine the stored and in-memory data frames and reset the index
        if partial and (self._hdfKey in self._hdf.root):
            data = self._hdf.get(self._hdfKey).append(data)
        data = self._map_data_types(data, check_category=False)
        data = data.reset_index(drop=True)

        self._hdf.close()

        # Overwrite the current file
        self._hdf.open(mode='w')
        self._hdf.put(self._hdfKey, data, format='table', dropna=True,
                      index=False, data_columns=self._dataCols)
        self._hdf.close()

        # Reopen in append mode
        self._hdf.open()


class PacsImportModality(PacsToolsMixin):
    """Aggregated modality database import

    Parameters
    ----------
    modality : str
        One of 'CR', 'CT', 'DG', 'DX', 'MR', 'NM', 'US', or 'XA' specifying the
        imaging modality to import. Various behaviors depend on the modality.
    fileServerMap : str or py.path.local
        Full file name of the server map to use
    fileModalityDB : str or py.path.local
        (Optional) Full file name of the modality database to use. By default,
        the modality string (see above) is mangled with the server map database
        to generate a file name for the modality database.
    readOnly : bool
        (Optional) When True, instantiates the class in read-only mode (i.e.,
        no database writing is allowed). This is useful when using the modality
        sepcific database with other software

    """

    def __init__(self, modality, fileServerMap, **kwargs):

        # Update the moadlity first as this might be used by other set methods
        self._modality = modality
        self._readonly = kwargs.get('readOnly', False)
        self._isbackup = kwargs.get('createBackUp', True)

        # Before storing the server object, validate the file name to ensure
        # that an empty database is not created by the "_fileDatabase" setter.
        fileServerMap = dicomtools.fileStr2PyPath(fileServerMap)
        if not fileServerMap.isfile():
            strErr = (f'Could not find a server map stored in {fileServerMap}.'
                      ' Expected an existing PACS server database.')
            raise ValueError(strErr)
        self._serverObj = SectraPacs(None, fileDatabase=fileServerMap,
                                     readOnly=True)

        # Store the database storage directory. Note that the attribute setter
        # will perform all validation (or auto-generation) of the user-
        # specified directory
        self._fileDatabase = kwargs.get('fileModalityDB', '')

        # Import the Sectra database and close the file. Retain only the
        # specified modality entries, and raise an error if none exist
        serverHdf = self._serverObj._hdf
        try:
            serverHdf.open()
            dfServer = serverHdf.select(self._serverObj._hdfKey,
                                        where=f'Modality=="{self._modality}"')
            serverHdf.close()
        except Exception as e:
            serverHdf.close()
            raise e
        if not dfServer.size:
            raise ValueError(f'No "{modality}" modality exams found. '
                             'Unable to create a class instance...')
        dfServer = dfServer.reset_index(drop=True).drop('Modality', axis=1)
        self._dataServerMap = dfServer

# -----------------------------------------------------------------------------
# --------------------------------- Properties --------------------------------
# -----------------------------------------------------------------------------

    @property
    def _dataCols(self):
        return ['File', 'MD5']

    @property
    def _dataTypeMap(self):
        if (self._modality in ['CR', 'DX']):

            # Define the non-DICOM derived dictionary
            keys = ['Accession', 'File', 'MD5', 'CuFilterMin', 'CuFilterMax',
                    'AlFilterMin', 'AlFilterMax']
            vals = [str, str, str, float, float, float, float]

            # Get the DICOM derived dictionary
            dcmMap = self._dicomMap
            for k in dcmMap.keys():
                if k not in keys:
                    keys.append(k)
                    vals.append(dcmMap[k][0])

            return dict(zip(keys, vals))
        else:
            raise NotImplementedError()

    @property
    def _dicomMap(self):
        if (self._modality == 'DX'):
            return {'Accession': [str, (0x0008, 0x0050)],
                    'PatientName': [str, (0x0010, 0x0010)],
                    'PatientSex': ['category', (0x0010, 0x0040)],
                    'PatientBirthDate': [str, (0x0010, 0x0030)],
                    'Institution': [str, (0x0008, 0x0080)],
                    'InstitutionAddress': [str, (0x0008, 0x0081)],
                    'StationName': ['category', (0x0008, 0x1010)],
                    'SeriesDate': [str, (0x0008, 0x0020)],
                    'Protocol': [str, (0x0011, 0x1046)],
                    'StudyDescription': [str, (0x0008, 0x1030)],
                    'SeriesNumber': [int, (0x0020, 0x0011)],
                    'SeriesDescription': [str, (0x008, 0x103e)],
                    'BodyPart': [str, (0x0018, 0x0015)],
                    'Exposure': [float, (0x0018, 0x1153)],
                    'ExposureTime': [float, (0x0018, 0x1153)],
                    'kVp': [float, (0x0018, 0x0060)],
                    'FilterMaterial': ['category', (0x0018, 0x7050)],
                    'Grid': ['category', (0x0018, 0x1166)], #TODO: verify this...
                    'ExposureMode': [str, (0x0018, 0x7060)],
                    'ExposureModeDescription': [str, (0x0018, 0x7062)],
                    'SID': [float, (0x0018, 0x1110)],
                    'ColLeftVertEdge': [float, (0x0018, 0x1702)],
                    'ColRightVertEdge': [float, (0x0018, 0x1704)],
                    'ColUpperHorEdge': [float, (0x0018, 0x1706)],
                    'ColLowerHorEdge': [float, (0x0018, 0x1708)],
                    'ColVerts': [str, (0x0018, 0x1720)],  # "\" separated int
                    'CollimatorShape': ['category', (0x0018, 0x1700)],
                    'ExposedArea': [str, (0x0040, 0x0030)],  #TODO: verify this
                    'ImageProcessingDescription': [str, (0x0018, 0x1400)],
                    'EI': [float, (0x0018, 0x1411)],
                    'TargetEI': [float, (0x0018, 0x1412)],
                    'DI': [str, (0x0018, 0x1413)],
                    'Sensitivity': [float, (0x0018, 0x6000)],
                    'OperatorsName': [str, (0x0008, 0x1070)],
                    'DetectorID': ['category', (0x0018, 0x0700a)]}
        else:
            raise NotImplementedError()

    @property
    def _hdfKey(self):
        return self._modality + 'ModalityDB'

    @property
    def _modality(self):
        return self.___modality

    @_modality.setter
    def _modality(self, val):
        assert(type(val) == str)
        if not(len(val)) or not(val in self._modalities):
            raise ValueError(f'"{self._modality}" is not a valid modality '
                             f'string.\nValid modality strings are: '
                             f'{self._modalities}')
        self.___modality = val

    @property
    def _modalities(self):
        return ['CR', 'CT', 'DG', 'DX', 'MR', 'NM', 'US', 'XA']

# -----------------------------------------------------------------------------
# ---------------------------------- Methods ----------------------------------
# -----------------------------------------------------------------------------

    def process(self, **kwargs):
        """Processes modality specific exam data on the Sectra server

           process all exams found in the current database

        Parameters
        ----------
        accessions : list
            Accession numbers to add to the database (if not already added).
        chunksize : int
            Number of database entries to add before writing to the HDF file
        checkhash : bool
            When True, hashes are calculated for duplicate files existing in
            the database. DICOM data is added to the database if needed

        """

        # Parse the user input
        #TODO: i need to check the checkhas and hash logic
        chunksize = kwargs.get('chunksize', 100)
        isCheckHash = kwargs.get('checkhash', True)
        isHash = kwargs.get('hash', False)
        if kwargs.get('accessions', None):
            sl = self._dataServerMap.Accession.isin(kwargs.get('accessions'))
        else:
            sl = self._dataServerMap.Accession.notnull()

        # Loop through the accession numbers, only processing those exams that
        # can be found in the DATA attribute
        hdf = self._hdf  # alias for ease
        data = self._dataMap
        nAcc = sl.sum()
        files = hdf.select(self._hdfKey, columns=['File'])
        nIter = 0
        dcmDict = self._dicomMap
        dcmMaps = [att for att in dir(dicomtools.vendormaps) if '_' not in att]
        for idx, row in self._dataServerMap.loc[sl, :].iterrows():

            dirExam = self._get_dir_from_entry(row)
            if not dirExam.isdir():
                nAcc -= 1
                continue
            else:
                print(f'Processing exam {nIter+1} of {nAcc}...')
                nIter += 1

            for f in dirExam.visit(fil='*.dcm'):

                # Update the slicer to be used with a second call to the
                # process method. This makes adding new files to the database
                # much faster. Duplicate are then checked after the fact.
                #FIXME: I'm currently having an issue where I cannot use the
                #       the 'where' functionality of hdf.select to find an
                #       entry in the database.
                sl[idx] = files.isin([f.strpath]).any()[0]
                if sl[idx] and isHash:
                    fHash = f.computehash()
                    sl[idx] = bool(hdf.select(self._hdfKey,
                                              where=[f'MD5="{fHash}"'],
                                              columns=['MD5']).shape[0])
                if sl[idx]:
                    continue

                # Generate a template data from using the current accession
                # number
                dfData = self._dataMap
                dfData.at[0, 'MD5'] = f.computehash()
                dfData.at[0, 'File'] = f.strpath

                # Initialize the GDCM import and attempt to read the file. Only
                # consider files of the specified modality
                hdr = dicomtools.header(f, autoLoad=False, customLookup=True)
                if (hdr[0x0008, 0x0060] != self._modality):
                    continue

                strLog = f'Processing {f.strpath}'
                self._logger.warning(strLog)

                if not hdr.read() or (
                        dicomtools.vendormaps.Modality(hdr) != self._modality):
                    continue

                # Process the file according to the DICOM dictionary
                for k in dcmDict.keys():

                    if k in dcmMaps:
                        fcn = getattr(dicomtools.vendormaps, k)
                        dfData.at[0, k] = fcn(hdr)
                    else:
                        dfData.at[0, k] = hdr[dcmDict[k][1]]

                    # Special check for accession number
                    if (k == 'Accession'):
                        val = dfData.at[0, k]
                        if (val not in dfData.at[0, 'File']):
                            sWarn = (f"Accession number {val} found in "
                                     f"{dfData.at[0, 'File']}")
                            self._logger.warn(sWarn)
                        if not dfData.at[0, k]:
                            dfData.at[0, k] = row.Accession
                    elif (k == 'FilterMaterial') and (self._modality == 'DX'):
                        val = dfData.at[0, k]
                        fl1 = dicomtools.vendormaps.FilterThicknessMinimum(hdr)
                        fl2 = dicomtools.vendormaps.FilterThicknessMaximum(hdr)
                        if val:
                            for flIdx, el in enumerate(val):
                                dfData.loc[0, 'FilterMaterial'] = el
                                if (el.lower() in ['copper', 'none']):
                                    dfData.loc[0, 'CuFilterMin'] = fl1[flIdx]
                                    dfData.loc[0, 'CuFilterMax'] = fl2[flIdx]
                                elif (el.lower() == 'aluminum'):
                                    dfData.loc[0, 'AlFilterMin'] = fl1[flIdx]
                                    dfData.loc[0, 'AlFilterMax'] = fl2[flIdx]
                                elif (el.lower() == 'unknown'):
                                    pass
                                else:
                                    raise NotImplementedError()
                        elif not val:
                            dfData.at[0, k] = float('NaN')
                        elif 'FilterMaterial' in hdr._tag_lookup.values():
                            raise NotImplementedError()
                    elif (k == 'ImageProcessingDescription'):
                        dfData.at[0, k] = \
                          dicomtools.vendormaps.ImageProcessingDescription(hdr)

                # Pixel spacing
                #TODO: I think i moved this to the equipment database
    #                    if dfIsNullEntry.PixelSpacing:
    #                        dfData.PixelSpacing = hdr[0x0018, 0x1164].value

                # After the modality data has been determined, update the
                # 'isBreak' variable to break all associated loops
                #TODO: nominally, this code should only be checking the
                #      columns not related to the directory structure of
                #      the Sectra servers (i.e., not Accession,
                #      PacsScanner, PacsServer, Series, NumImages). For the
                #      moment, this is easier

                # Append that data to current database
                data = data.append(dfData, ignore_index=True)

                if not (nIter % chunksize) or (nIter == nAcc):
                    data = self._map_data_types(data)

                    try:
                        self._hdf.append(self._hdfKey, data,
                                         format='table',
                                         index=False)
                    except (TypeError, ValueError) as e:
                        #TODO: it might be worthwhile separating these errors.
                        #      When a category is not present, one error occurs
                        #      And a separate error occurs when a string in the
                        #      file is too short for a string in the current
                        #      data frame
                        self._overwrite_hdf(data, partial=True)

                    # Reset the data variable
                    data = self._dataMap

        if nAcc and isCheckHash and sl.any():
            self.process(self._dataServerMap.loc[sl, 'Accession'],
                         hash=True, checkhash=False)


class SectraPacs(PacsToolsMixin):
    """Aggregated short term Sectra DICOM image directories

    Parameters
    ----------
    listDirSectra : list
        Server directories to monitor. These directories must contain a sub-
        -directory titled 'folders'. If not immediately found, the provide will
        directory will be searched recursively for 'folders' (extensive
        directory structures may result in slow performance)
    fileDatabase : str or py.path.local
        (Optional) Full file name of the server map database
    readOnly : bool
        (Optional) When True, a class instance can be created. This instance
        can be used to access the database, but limits writing of any data.
        Note in read-only mode, the user is not required to supply the PACS
        server directory

    Attributes
    ----------

    """

    def __init__(self, dirsSectra, **kwargs):

        self._readonly = kwargs.get('readOnly', False)
        self._isbackup = kwargs.get('createBackUp', True)
        if not self._readonly:
            self.listDirSectra = dirsSectra

        # Store the database storage directory. Note that the attribute setter
        # will perform all validation (or auto-generation) of the user-
        # specified directory
        self._fileDatabase = kwargs.get('fileDatabase', None)

# -----------------------------------------------------------------------------
# --------------------------------- Properties --------------------------------
# -----------------------------------------------------------------------------

    @property
    def _dataCols(self):
        return ['Accession', 'Modality']

    @property
    def _dataTypeMap(self):
        # Define the non-DICOM derived data
        keys = ['Accession', 'PacsScanner', 'PacsServer']
        vals = [str, 'category', 'category']

        # Append the DICOM derived data
        dcmMap = self._dicomMap
        keys.extend(dcmMap.keys())
        vals.extend([v[0] for v in dcmMap.values()])

        return dict(zip(keys, vals))

    @property
    def _dicomMap(self):
        return {'Modality': ['category', (0x0008, 0x0060)]}

    @property
    def _hdfKey(self):
        return 'SectraServerMap'

    @property
    def listDirSectra(self):
        """:obj:'list' of :obj:'py.path.local': Sectra server directories to be
        monitored.

        When setting this property, all paths are validated and, for str
        inputs, converted to py.path.local objects.

        Raises
        ------
        TypeError
            Any inputs are not of type str or py.path.local
        ValueError
            No inputs are valid Sectra directories

        """
        val = []
        if not self._readonly:
            val = self.__listDirSectra
        return val

    @listDirSectra.setter
    def listDirSectra(self, val):

        if self._readonly:
            raise AttributeError('Unable to set "listDirSectra" when the '
                                 'class instance is in read-only mode.')

        # Ensure a list of paths is validated
        if (type(val) != list):
            val = [val]
        assert (type(val) == list)

        # Get the unique elements
        val = list(set(val))

        # Validate each of the list's contents
        for d in reversed(val):

            idx = val.index(d)

            # Convert strings to py.path.local
            if (type(d) == str):
                d = py.path.local(d)
                val[idx] = d
            elif (type(d) == py.path.local):
                pass
            else:
                raise TypeError()

            # Remove invalid directories
            if not d.isdir():
                warnings.warn(f'Invalid directory: "{d.strpath}"', UserWarning)
                val.remove(d)
                continue

            # Attempt to find the 'folders' directory
            if 'folders' not in d.strpath:
                if d.join('folders').isdir():
                    val[idx] = d.join('folders')
                else:
                    warnings.warn(f"'folders' not immediately found in "
                                  "{d.strpath}. Searching for 'folders'. This"
                                  " could take a while...", UserWarning)
                    for sd in d.visit(fil='*folders', bf=True):
                        if 'folders' in sd.strpath:
                            d = sd
                            break
                    if 'folders' in d.strpath:
                        val[idx] = d
                    else:
                        warnings.warn('Invalid Sectra director: '
                                      f'{val.strpath}', UserWarning)
                        val.remove(d)

            # Raise an error when no valid directories are provided...
            if not val:
                strErr = ("No valid 'folders' sub-directories were found.\n\n"
                          "Usage: pacstools.SectraPacs(PATH)\n\nPATH must be a"
                          " str or list of str that are valid directories"
                          " containing a 'folders' sub-directory.")
                raise ValueError(strErr)

        self.__listDirSectra = val

# -----------------------------------------------------------------------------
# ---------------------------------- Methods ----------------------------------
# -----------------------------------------------------------------------------

    def clean(self, **kwargs):
        """Verifies and removes invalid PACS server database entries

        Specified database entries are checked (i.e., the directories should
        exist on the PACS servers). The current in-memory database is updated
        to reflect any entries that are dropped

        Parameters
        ----------
        acc : list
            (Optional) Accession numbers corresponding to database entries to
            be verified

        """

        # Create a logical slice for the data frame
        data = self._hdf.get('SectraServerMap')
        acc = kwargs.get('acc', [])
        dropNa = kwargs.get('dropNa', False)
        if acc:
            assert (type(acc) == list)
            sl = data['Accession'].isin(acc)
        elif dropNa:
            sl = data['Accession'].notnull()
        else:
            sl = data.notnull()

        # Drop 'None' entries
        data = data[~data.Accession.isin(['None'])]

        # Determine which accession numbers correspond to database entries with
        # valid corresponding PACS server locations
        tf = sl & data['Accession'].isnull()
        for idx, row in data.loc[sl, :].iterrows():
            tf.at[idx] = self._get_dir_from_entry(row).isdir()

        # Drop the bad entries
        data = data.loc[tf, :].dropna(how='all')
        data = data.drop_duplicates()

        self._overwrite_hdf(data)

    def walk(self, exclude=[], chunksize=100):
        """Walks through the user-specified PACS directories

        Walk seeks and appends to the database all sub-directories that match
        the assumed fingerprint of the Sectra PACS directory structure. Those
        accession numbers that exist in the current database are ignored during
        the search.

        Parameters
        ----------
        exclude : list
            Sub-directories that should be ignored when searching the PACS
            servers. For example, temporary pre-fetch directories
        chunksize : int
            Number of new entries to complete before writing to the database.
            Note that for small values of chunksize significant performance
            degradation will occur

        Returns
        -------
        accList : list
            All sub-directories found (not necessarily appended to the
            database)

        """

        assert (type(chunksize) == int) and (chunksize > 0)

        exList = []
        for se in exclude:
            for sp in self.listDirSectra:
                exList.append(py.path.local(sp).join(se))

        # Get all of the accession numbers
        scanList = []
        for s in self.listDirSectra:
            scanList.extend([d for d in s.listdir() if not d.isfile()])
            for rm in exList:
                if rm in scanList:
                    scanList.remove(rm)
        accList = []
        for s in scanList:
            accList.extend(s.listdir())

        data = self._dataMap

        # Loop variables/aliases
        n = 0
        nAcc = len(accList)
        modKey = self._dicomMap['Modality'][1]

        for d in accList:

            # Only consider gathering additional information on those sub-
            # directories that have not already been evaluated. The assumption
            # here is that if the accession number exists, then the sub-
            # directories were successfully mapped
            dfAcc = self._hdf.select(self._hdfKey,
                                     where=[f'Accession="{d.purebasename}"'])
            if dfAcc.shape[0]:
                dStr = d.dirpath()
                if dfAcc.Modality.isna().any() or \
                        (dfAcc.PacsServer.isin([dStr.dirname]) &
                         dfAcc.PacsScanner.isin([dStr.purebasename])).any():
                    nAcc -= 1
                    continue
                logStr = f'Accession number {d.purebasename} was logged in:\n'
                for idx, row in dfAcc.iterrows():
                    logStr = logStr + \
                        f'\t"{self._get_dir_from_entry(row).dirname}"\n'
                logStr = logStr + f'\tIt was also found in:\n\t"{d.strpath}"'
                self._logger.warn(logStr)
            elif not d.isdir():
                self._logger.warn(f'Accession directory "{d.strpath}" found in'
                                  ' an initial recursive search, but no longer'
                                  ' exists.')
                nAcc -= 1
                continue

            sProg = f'Processing {n+1} of {nAcc} files... {d.strpath}'
            self._logger.warning(sProg)
            print(sProg)

            # Generate the new data frame
            df = self._dataMap
            df.at[0, 'Accession'] = d.purebasename
            df.at[0, 'PacsScanner'] = d.dirpath().purebasename
            df.at[0, 'PacsServer'] = d.dirpath().dirname
            df.at[0, 'Modality'] = ''

            # Find the first valid modality tag
            for f in dicomtools.dicomMixin.seek_dicom(d,
                                                      fil='*.dcm', gen=True):
                if hasattr(df, 'Modality') and df.Modality.notnull()[0]:
                    break

                #TODO: the following code assumes that the modality tag is the
                #      same for all series. However, consider the case of CT...
                #      There are three modalities that might exist for the same
                #      game: (1) CT, (2) SR (structured dose report), or (3) SC
                #      (secondary screen capture).

                #TODO: I need to figure out how to handle exams that contain
                #      only a SC or SR file. While I have not seen the latter,
                #      an example of only a screen capture showed up at:
                #       \\172.25.206.203\i\folders\CT_IMS2\0119032120160606

                # Get the modality tag
                hdr = dicomtools.header(f, autoLoad=False)
                valModality = hdr[modKey]
                if valModality is 'DX':
                    df['Modality'] = dicomtools.vendormaps.Modality(hdr)
                elif valModality and (valModality != 'SC') and \
                        (valModality != 'SR') and \
                        (valModality != 'Mammogram'):
                    df['Modality'] = valModality

            # Use the data frame to force the correct data types. Note that if
            # a new category exists that column will be converted to an object
            # data type.
            data = data.append(df, ignore_index=True)
            n += 1

            # Append the data on-the-fly
            if not (n % chunksize) or (n == nAcc):

                data = self._map_data_types(data)

                try:
                    self._hdf.append(self._hdfKey, data, format='table')
                except (TypeError, ValueError):
                    self._overwrite_hdf(data, partial=True)

                # Reset the data variable
                data = self._dataMap

        return accList
