#  Copyright (c) 2019. Partners HealthCare and other members of
#  Forome Association
#
#  Developed by Sergey Trifonov based on contributions by Joel Krier,
#  Michael Bouzinier, Shamil Sunyaev and other members of Division of
#  Genetics, Brigham and Women's Hospital
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import sys, gzip, json
from io import TextIOWrapper
from subprocess import Popen, PIPE

from utils.ixbz2 import IndexBZ2
#===============================================
class DataDiskStorage:
    def __init__(self, ds_h, dataset_path):
        self.mDS = ds_h
        self.mPath = dataset_path
        self.mVData = IndexBZ2(self.mPath + "/vdata.ixbz2")

    def hasFullSupport(self):
        return True

    def getRecordData(self, rec_no):
        assert 0 <= rec_no < self.mDS.getTotal()
        return json.loads(self.mVData[rec_no])

    def iterFData(self, rec_no_set = None):
        with gzip.open(self.mPath + "/fdata.json.gz",
                "rt", encoding = "utf-8") as inp:
            for rec_no, line in enumerate(inp):
                if rec_no_set is not None and rec_no not in rec_no_set:
                    continue
                yield rec_no, json.loads(line.strip())

    def iterPData(self, rec_no_set = None):
        with gzip.open(self.mPath + "/pdata.json.gz",
                "rt", encoding = "utf-8") as inp:
            for rec_no, line in enumerate(inp):
                if rec_no_set is not None and rec_no not in rec_no_set:
                    continue
                yield rec_no, json.loads(line.strip())

#===============================================
class DataDiskStorageWriter:
    def __init__(self, dataset_path, report_mode = False):
        self.mPath = dataset_path
        self.mReportMode = report_mode
        self.mTotal = 0
        self.mVDataProc = Popen(sys.executable + " -m utils.ixbz2 --calm -o "
            + self.mPath + "/vdata.ixbz2 /dev/stdin", shell = True,
            stdin = PIPE, stderr = PIPE,
            bufsize = 1, universal_newlines = False,
            close_fds = True)

        self.mVDataOut = TextIOWrapper(self.mVDataProc.stdin,
            encoding = "utf-8", line_buffering = True)

        self.mFDataOut = gzip.open(self.mPath + "/fdata.json.gz",
                'wt', encoding = "utf-8")
        self.mPDataOut = gzip.open(self.mPath + "/pdata.json.gz",
                'wt', encoding = "utf-8")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __enter__(self):
        return self

    def close(self):
        _, vreport_data = self.mVDataProc.communicate()
        if self.mReportMode:
            for line in str(vreport_data, encoding="utf-8").splitlines():
                print(line, file = sys.stderr)
        self.mVDataProc.wait()
        self.mFDataOut.close()
        self.mPDataOut.close()

    def getTotal(self):
        return self.mTotal

    def putRecord(self, record, f_data, p_data):
        print(json.dumps(record, ensure_ascii = False), file = self.mVDataOut)
        print(json.dumps(f_data, ensure_ascii = False), file = self.mFDataOut)
        print(json.dumps(p_data, ensure_ascii = False), file = self.mPDataOut)
        self.mTotal += 1