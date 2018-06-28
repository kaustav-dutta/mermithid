'''
'''

# import CicadaPy
# CicadaPy.loadLibraries(True)
# try:
#     from ROOT import Cicada as KT
# except ImportError:
#     from ROOT import Katydid as KT


from morpho.processors.IO import IOProcessor
from morpho.utilities import reader, morphologging
logger = morphologging.getLogger(__name__)

from ROOT import TFile, TTreeReader, TTreeReaderValue


class IOCicadaProcessor(IOProcessor):

    def InternalConfigure(self,params):
        super().InternalConfigure(params)
        self.object_type = reader.read_param(params,"object_type","TMultiTrackEventData")
        self.object_name = reader.read_param(params,"object_name","multiTrackEvents:Event")
        self.use_katydid = reader.read_param(params,"use_katydid",False)
        return True

    def Reader(self):
        '''
        '''
        logger.debug("Reading {}".format(self.file_name))
        from ReadKTOutputFile import ReadKTOutputFile
        self.data = ReadKTOutputFile(self.file_name,self.variables,katydid=self.use_katydid,objectType=self.object_type,name=self.object_name)
        return True
        

    def Writer(self):
        '''
        End-user analysis should not produce Katydid output objects...
        '''
        logger.error("End user analysis: cannot write reconstruction algorithm output")
        raise
