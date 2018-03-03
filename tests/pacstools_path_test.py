# -*- coding: utf-8 -*-
"""
Created on Sun Dec 24 10:28:21 2017

@author: Ryan
"""

from context import pacstools
import os
import py
import pytest
import string
import random
import tempfile
import win32wnet


class TestAccessionPathWalk(object):

    def test_pacstools_storage_path_auto_gen_no_input(self):
        """This test checks the auto-generated user directory that is used in
           lieu of a user-defined directory for storing files (e.g., databases)
           generated by PACSTOOLS"""

        # The code here was copied from PACSTOOLS as there is no way to
        # generate the local path name without creating the directory

        # Get the user's home directory and determine which paths
        dirUser = os.path.expanduser("~")
        if (os.name == 'nt'):
            dirUser = os.path.join(dirUser, 'AppData')
        else:
            strErr = ('Unable to determine the local user directory. Either '
                      'the case hasn''t been programmed or the appropriate '
                      'system environment variable doesn''t exist.')
            raise NotImplementedError(strErr)

        # Concatenate the unique directory name
        dirLocalStorage = os.path.join(dirUser, "PACSimport")
        if os.path.isdir(dirLocalStorage):
            pytest.skip(f'The local storage directory "{dirLocalStorage}" '
                        'already exists. Unable to test the auto-generate'
                        'feature.')

        # Create a SECTRALISTENER object without using a user-defined directory
        # and ensure that the above path exists
        pacstools.SectraListener()

        assert(os.path.isdir(dirLocalStorage))

        # Since we made the directory, remove it
        py.path.local(dirLocalStorage).remove()

    def test_pacstools_storage_path_auto_gen_bad_input(self):
        """This test checks the auto-generated user directory that is used in
           lieu of a bad user-defined directory for storing files (e.g.,
           databases) generated by PACSTOOLS"""

        # The code here was copied from PACSTOOLS as there is no way to
        # generate the local path name without creating the directory

        # Get the user's home directory and determine which paths
        dirUser = os.path.expanduser("~")
        if (os.name == 'nt'):
            dirUser = os.path.join(dirUser, 'AppData')
        else:
            strErr = ('Unable to determine the local user directory. Either '
                      'the case hasn''t been programmed or the appropriate '
                      'system environment variable doesn''t exist.')
            raise NotImplementedError(strErr)

        # Create and remove a temporary directory. This directory name will be
        # used to ensure to pass as a non-existent directory to the
        # SectraListener constructor
        dirBad = tempfile.TemporaryDirectory()
        dirBad.cleanup()

        # Concatenate the unique directory name
        dirLocalStorage = os.path.join(dirUser, "PACSimport")
        if os.path.isdir(dirLocalStorage):
            pytest.skip(f'The local storage directory "{dirLocalStorage}" '
                        'already exists. Unable to test the auto-generate'
                        'feature.')

        # Create a SECTRALISTENER object using a non-existent user-defined
        # directory and ensure that the above path is created
        pacstools.SectraListener(dirBad.name)

        assert(os.path.isdir(dirLocalStorage))

        # Since we made the directory, remove it
        py.path.local(dirLocalStorage).remove()

    def test_no_folders_directory_failure(self, tmpdir):
        """This test generates a directory - "folder" - instead of "folders"
           to ensure that the SectraListener initialization will raise an
           error - NotADirectoryError"""

        # Generate a directory that should cause a failure
        dirFolder = tmpdir.mkdir('folder').strpath

        with pytest.raises(NotADirectoryError):
            pacstools.SectraListener(dirFolder)

        # Perform the clean-up
        tmpdir.remove()

    def test_unc_path_multi_scanner_multi_accession(self):
        """This test attempts to test the UNC path capabilities. When the test
           file path is convertable to a UNC path, the tests from method
           'test_multi_scanner_multi_accession' are run"""

        #TODO: the following code will raise an error (2250) when the path is a
        #      on a local drive. I have tested that the following code works,
        #      but the generic EXCEPTION is used in the TRY/EXCEPT statement
        #      below. I'd like to replace this with somethin less general

        # Get the current file's absolute path
        try:
            d = win32wnet.WNetGetUniversalName(py.path.local(__file__).dirname)
        except Exception:
            pytest.skip('Unable to generate a UNC path with the current' +
                        'configuration')
        d = py.path.local(d)

        # Generate the directories as in the multi-scanner, multi-accession
        # number test
        nAcc = [random.randint(1, 10) for x in range(4)]
        accList, nImDirs = self._gen_dirs(d, nAcc=nAcc)

        # Instantiate a SectraListener object, walk the directory structure,
        # and validate that a single accession folder was found. Use the same
        # temporary directory to house the database to ensure that another
        # database is not loaded
        obj = pacstools.SectraListener(d.strpath, dirDataBase=d.strpath)
        obj.walk_dirs()

        # Before asserting the test results, clean-up the directories. Note
        # that the 'folders' path must be added because the parent
        # directory 'tests' must not be removed!
        d.join('folders').remove()

        # Perform three tests: (1) only one accession number has been found
        # and (2) that all accession numbers generated exist in the data
        # frame, (3) that the number of image directories matches the
        # number that were generated automatically
        assert(obj.data.loc[:, 'Accession'].size == len(accList))
        for acc in accList:
            assert(obj.data.Accession.isin([acc]).any())
        #TODO: generate one more assertion (or loop of assertions) to
        #      ensure that all series sub-directories for the accession
        #      numbers were generated correctly

    def test_no_scanner_no_accession_list(self, tmpdir):
        """This test generates a single Sectra style PACS directory structure
           with a single modality sub-directory (CT) containing a single
           accession number"""

        # Generate the temporary Sectra style directory structure
        accList, nImDirs = self._gen_dirs(tmpdir, [0]*4)

        # Remove all of the sub-directories except that one for CT
        tmpdir.join('folders', 'CR').remove()
        tmpdir.join('folders', 'CT').remove()
        tmpdir.join('folders', 'MG').remove()
        tmpdir.join('folders', 'MR').remove()

        # Instantiate a SectraListener object, walk the directory structure,
        # and validate that a single accession folder was found. Use the same
        # temporary directory to house the database to ensure that another
        # database is not loaded
        obj = pacstools.SectraListener(tmpdir.strpath,
                                       dirDataBase=tmpdir.strpath)
        obj.walk_dirs()

        # Before asserting the test results, clean-up the directories
        tmpdir.remove()

        # Perform a test to ensure that no accession numbers were found
        assert(obj.data.loc[:, 'Accession'].size == 0)

    def test_single_scanner_no_accession_list(self, tmpdir):
        """This test generates a single Sectra style PACS directory structure
           with a single modality sub-directory (CT) containing a single
           accession number"""

        # Generate the temporary Sectra style directory structure
        accList, nImDirs = self._gen_dirs(tmpdir, [0]*4)

        # Remove all of the sub-directories except that one for CT
        tmpdir.join('folders', 'CR').remove()
        tmpdir.join('folders', 'MG').remove()
        tmpdir.join('folders', 'MR').remove()

        # Instantiate a SectraListener object, walk the directory structure,
        # and validate that a single accession folder was found. Use the same
        # temporary directory to house the database to ensure that another
        # database is not loaded
        obj = pacstools.SectraListener(tmpdir.strpath,
                                       dirDataBase=tmpdir.strpath)
        obj.walk_dirs()

        # Before asserting the test results, clean-up the directories
        tmpdir.remove()

        # Perform a test to ensure that no accession numbers were found
        assert(obj.data.loc[:, 'Accession'].size == 0)

    def test_single_scanner_single_accession_list(self, tmpdir):
        """This test generates a single Sectra style PACS directory structure
           with a single modality sub-directory (CT) containing a single
           accession number"""

        # Generate the temporary Sectra style directory structure
        accList, nImDirs = self._gen_dirs(tmpdir)

        # Remove all of the sub-directories except that one for CT
        tmpdir.join('folders', 'CR').remove()
        tmpdir.join('folders', 'MG').remove()
        tmpdir.join('folders', 'MR').remove()

        # Instantiate a SectraListener object, walk the directory structure,
        # and validate that a single accession folder was found. Use the same
        # temporary directory to house the database to ensure that another
        # database is not loaded
        obj = pacstools.SectraListener(tmpdir.strpath,
                                       dirDataBase=tmpdir.strpath)
        obj.walk_dirs()

        # Before asserting the test results, clean-up the directories
        tmpdir.remove()

        # Perform three tests: (1) only one accession number has been found and
        # (2) that accession number matches the auto-generated one, (3) that
        # the number of image directories matches the number that were
        # generated automatically
        assert(obj.data.loc[:, 'Accession'].size == 1)
        assert(obj.data.loc[0, 'Accession'] == accList[0])
        assert(len(obj.data.loc[0, 'Series']) == nImDirs[1][0])

    def test_single_scanner_multi_accession_list(self, tmpdir):
        """This test generates a single Sectra style PACS directory structure
           with a single modality sub-directory (CT) containing a multiple
           accession number sub-directories"""

        # Generate the temporary Sectra style directory structure
        nAcc = [0, random.randint(1, 10), 0, 0]
        accList, nImDirs = self._gen_dirs(tmpdir, nAcc=nAcc)

        # Remove all of the sub-directories except that one for CT
        tmpdir.join('folders', 'CR').remove()
        tmpdir.join('folders', 'MG').remove()
        tmpdir.join('folders', 'MR').remove()

        # Instantiate a SectraListener object, walk the directory structure,
        # and validate that a single accession folder was found. Use the same
        # temporary directory to house the database to ensure that another
        # database is not loaded
        obj = pacstools.SectraListener(tmpdir.strpath,
                                       dirDataBase=tmpdir.strpath)
        obj.walk_dirs()

        # Before asserting the test results, clean-up the directories
        tmpdir.remove()

        # Perform three tests: (1) only one accession number has been found and
        # (2) that accession number matches the auto-generated one, (3) that
        # the number of image directories matches the number that were
        # generated automatically
        assert(obj.data.loc[:, 'Accession'].size == len(accList))
        for acc in accList:
            assert(obj.data.Accession.isin([acc]).any())
        #TODO: generate one more assertion (or loop of assertions) to ensure
        #      that all series sub-directories for the accession numbers were
        #      generated correctly

    def test_multi_scanner_no_accession_list(self, tmpdir):
        """This test generates a single Sectra style PACS directory structure
           with 4 empty modality sub-directories (CR, CT, MG, MR) to check the
           case where a PACS directory with no accession numbers"""

        # Generate the temporary Sectra style directory structure
        accList, nImDirs = self._gen_dirs(tmpdir, [0]*4)

        # Instantiate a SectraListener object, walk the directory structure,
        # and validate that a single accession folder was found. Use the same
        # temporary directory to house the database to ensure that another
        # database is not loaded
        obj = pacstools.SectraListener(tmpdir.strpath,
                                       dirDataBase=tmpdir.strpath)
        obj.walk_dirs()

        # Before asserting the test results, clean-up the directories
        tmpdir.remove()

        # Perform a test to ensure that no accession numbers were found
        assert(obj.data.loc[:, 'Accession'].size == 0)

    def test_multi_scanner_single_accession_list(self, tmpdir):
        """This test generates a single Sectra style PACS directory structure
           with 4 modality sub-directories (CR, CT, MG, MR) generating a random
           number of accession numbers and image directories within the CT
           modality sub-directory"""

        # Generate the temporary Sectra style directory structure
        accList, nImDirs = self._gen_dirs(tmpdir)

        # Instantiate a SectraListener object, walk the directory structure,
        # and validate that a single accession folder was found. Use the same
        # temporary directory to house the database to ensure that another
        # database is not loaded
        obj = pacstools.SectraListener(tmpdir.strpath,
                                       dirDataBase=tmpdir.strpath)
        obj.walk_dirs()

        # Before asserting the test results, clean-up the directories
        tmpdir.remove()

        # Perform three tests: (1) only one accession number has been found and
        # (2) that accession number matches the auto-generated one, (3) that
        # the number of image directories matches the number that were
        # generated automatically
        assert(obj.data.loc[:, 'Accession'].size == 1)
        assert(obj.data.loc[0, 'Accession'] == accList[0])
        assert(len(obj.data.loc[0, 'Series']) == nImDirs[1][0])

    def test_multi_scanner_multi_accession_list(self, tmpdir):
        """This test generates a single Sectra style PACS directory structure
           with 4 modality sub-directories (CR, CT, MG, MR) generating a random
           number of accession numbers and image directories within each of the
           modality sub-directory"""

        # Generate the temporary Sectra style directory structure
        nAcc = [random.randint(1, 99) for x in range(4)]
        accList, nImDirs = self._gen_dirs(tmpdir, nAcc=nAcc)

        # Instantiate a SectraListener object, walk the directory structure,
        # and validate that a single accession folder was found. Use the same
        # temporary directory to house the database to ensure that another
        # database is not loaded
        obj = pacstools.SectraListener(tmpdir.strpath,
                                       dirDataBase=tmpdir.strpath)
        obj.walk_dirs()

        # Before asserting the test results, clean-up the directories
        tmpdir.remove()

        # Perform three tests: (1) only one accession number has been found and
        # (2) that all accession numbers generated exist in the data frame, (3)
        # that the number of image directories matches the number that were
        # generated automatically
        assert(obj.data.loc[:, 'Accession'].size == len(accList))
        for acc in accList:
            assert(obj.data.Accession.isin([acc]).any())
        #TODO: generate one more assertion (or loop of assertions) to ensure
        #      that all series sub-directories for the accession numbers were
        #      generated correctly

    def _gen_dirs(self, d, nAcc=[0, 1, 0, 0]):
        """Generate the Sectra style directory structure

            ACC, NIMS = OBJ._GEN_DIRS() generates a single accession number in
            the CT direcrtory, returning the list of accession numbers and the
            list of the number of series per accession.

            [...] = OBJ._GEN_DIRS(nAcc=[...]) generates random accession
            numbers in the respective modalities based on the number in the
            corresponding list position. For example, if nAcc[1] is 3, 3
            accession numbers will be generated in the CT directory"""

        assert(len(nAcc) == 4)

        # Generate the folders directory, image directory number list, and
        # accession number list
        dirFolders = d.mkdir('folders')
        nImDirs = [[], [], [], []]
        accList = []

        # Generate the CR sub-directories
        dirCr = dirFolders.mkdir('CR')
        for iAcc in range(nAcc[0]):
            accList.append("".join(random.choices(string.digits, k=9)))
            nImDirs[0].append(random.randint(1, 10))
            for iIm in range(1, nImDirs[0][-1]+1):
                imDir = 'im_' + str(iIm)
                dirCr.join(accList[-1], '0', imDir, 'i0000,0000.dcm').ensure()

        # Generate the CT sub-directories
        dirCt = dirFolders.mkdir('CT')
        for iAcc in range(nAcc[1]):
            accList.append("".join(random.choices(string.digits, k=9)))
            nImDirs[1].append(random.randint(1, 10))
            for iIm in range(1, nImDirs[1][-1]+1):
                imDir = 'im_' + str(iIm)
                dirCt.join(accList[-1], '0', imDir, 'i0000,0000.dcm').ensure()

        # Generate the MG sub-directories
        dirMg = dirFolders.mkdir('MG')
        for iAcc in range(nAcc[2]):
            accList.append("".join(random.choices(string.digits, k=9)))
            nImDirs[2].append(random.randint(1, 10))
            for iIm in range(1, nImDirs[2][-1]+1):
                imDir = 'im_' + str(iIm)
                dirMg.join(accList[-1], '0', imDir, 'i0000,0000.dcm').ensure()

        # Generate the MR sub-directories
        dirMr = dirFolders.mkdir('MR')
        for iAcc in range(nAcc[3]):
            accList.append("".join(random.choices(string.digits, k=9)))
            nImDirs[3].append(random.randint(1, 10))
            for iIm in range(1, nImDirs[2][-1]+1):
                imDir = 'im_' + str(iIm)
                dirMr.join(accList[-1], '0', imDir, 'i0000,0000.dcm').ensure()

        # Retrun the accession list
        return accList, nImDirs