#!/usr/bin/env python

import numpy as N
import unittest
import subprocess as SP
import os
import util

try: 
    from mpi4py import MPI
    rank = MPI.COMM_WORLD.Get_rank()
    distributed = MPI.COMM_WORLD.Get_size() > 1
except ImportError:
    print 'Warning: without mpi4py module, only serial behavior is tested'
    distributed = False
    rank = 0

if rank==0:
    print 'To fully test, must do both:'
    print '  1) python testutil.py'
    print '  2) mpiexec -n <# procs> python testutil.py\n\n'

class TestUtil(unittest.TestCase):
    """Tests all of the functions in util.py
    
    To test all parallel features, use "mpiexec -n 2 python testutil.py"
    Some parallel features are tested even when running in serial.
    """    
    def setUp(self):
        try:
            from mpi4py import MPI
            self.comm=MPI.COMM_WORLD
            self.numMPITasks = self.comm.Get_size()
            self.rank = self.comm.Get_rank()
        except ImportError:
            self.numProcs=1
            self.rank=0
        self.testDir = 'files_modaldecomp_test/'
        if rank == 0:
            if not os.path.isdir(self.testDir):
                SP.call(['mkdir', self.testDir])
    
    def tearDown(self):
        if distributed:
            MPI.COMM_WORLD.barrier()
        if rank == 0:
            SP.call(['rm -rf %s/*' % self.testDir], shell=True)
        if distributed:
            MPI.COMM_WORLD.barrier()
        
        
    @unittest.skipIf(distributed,'Only save/load matrices in serial')
    def test_load_save_mat_text(self):
        """Test that can read/write text matrices"""
        tol = 8
        rows = [1, 5, 20]
        cols = [1, 4, 5, 23]
        matPath = self.testDir+'testMatrix.txt'
        delimiters = [',',' ',';']
        for delimiter in delimiters:
            for is_complex in [False, True]:
                for squeeze in [False, True]:
                    for numRows in rows:
                        for numCols in cols:
                            mat_real = N.random.random((numRows,numCols))
                            if is_complex:
                                mat_imag = N.random.random((numRows,numCols))
                                mat = mat_real + 1J*mat_imag
                            else:
                                mat = mat_real
                            # Check row and column vectors, no squeeze (1,1)
                            if squeeze and (numRows > 1 or numCols > 1):
                                mat = N.squeeze(mat)
                            util.save_mat_text(mat,matPath,delimiter=delimiter)
                            matRead = util.load_mat_text(matPath,delimiter=delimiter,
                                is_complex=is_complex)
                            if squeeze:
                                matRead = N.squeeze(matRead)
                            N.testing.assert_array_almost_equal(matRead,mat,
                              decimal=tol)
                          
        
    def test_svd(self):
        numInternalList = [10,50]
        numRowsList = [3,5,40]
        numColsList = [1,9,70]
        for numRows in numRowsList:
            for numCols in numColsList:
                for numInternal in numInternalList:
                    leftMat = N.mat(N.random.random((numRows,numInternal)))
                    rightMat = N.mat(N.random.random((numInternal,numCols)))
                    A = leftMat*rightMat
                    [LSingVecs,singVals,RSingVecs]=util.svd(A)
                    
                    U,E,Vstar=N.linalg.svd(A,full_matrices=0)
                    V = N.mat(Vstar).H
                    if numInternal < numRows or numInternal <numCols:
                        U=U[:,:numInternal]
                        V=V[:,:numInternal]
                        E=E[:numInternal]
          
                    N.testing.assert_array_almost_equal(LSingVecs,U)
                    N.testing.assert_array_almost_equal(singVals,E)
                    N.testing.assert_array_almost_equal(RSingVecs,V)
    
    
if __name__=='__main__':
    unittest.main(verbosity=2)


