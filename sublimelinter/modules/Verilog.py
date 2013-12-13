import re
import os
import shutil
import subprocess

from .base_linter import BaseLinter, TEMPFILES_DIR

CONFIG = {
    'language': 'Verilog'
}

BaseFileName = ""

class Linter(BaseLinter):
    def built_in_check(self, view, code, filename):
        global BaseFileName

        fileList = []
        baseDir = os.path.dirname(filename)

        fileList.append(filename)
        bfilename = os.path.basename(filename)
        BaseFileName = bfilename

        with open(os.path.join(TEMPFILES_DIR, bfilename), 'w') as f:
            f.write(code)


        for root, dirs, files in os.walk(baseDir):
            for file_ in files:
                if os.path.splitext(file_)[1] == ".v" or os.path.splitext(file_)[1] == ".h":
                    path = os.path.join(root, file_)
                    if path not in fileList:
                        fileList.append(path)
                        shutil.copyfile(path, os.path.join(TEMPFILES_DIR, os.path.basename(path)))
                        print("File Copyed:" + path)


        args = ["verilator", "-Wall", "--language", "1364-2001", "--lint-only", bfilename]

        try:
            process = subprocess.Popen(args,
                                       cwd=TEMPFILES_DIR,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       startupinfo=self.get_startupinfo())

            result = process.communicate()[0].decode('utf-8')
        finally:
            print("Execution finish!")

        """
        try:
            for path in fileList:
                tmpname = os.path.join(TEMPFILES_DIR, os.path.basename(path))
                os.chmod(tmpname, stat.S_IWRITE)
                os.remove(tmpname)
        finally:
            print "Delete temporary file error"
        """

        return result.strip()

    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):
        global BaseFileName
        line_list = []
        print("TARGET FILE:" + BaseFileName)
        for line in errors.splitlines():
            #match = re.match(r'^Parse error:\s*(?:\w+ error,\s*)?(?P<error>.+?)\s+in\s+.+?\s*line\s+(?P<line>\d+)', line)
            match = re.match(r'^%Error:\s(?P<file>.+?\.v):(?P<line>\d+?):\s(?P<error>.+?)$', line)

            #print line

            if match:
                fname, error, line = match.group('file'), match.group('error'), match.group('line')
                if fname == BaseFileName and False == error.startswith("Cannot find file containing module:") and int(line) not in line_list:
                    self.add_message(int(line), lines, error, errorMessages)
                    line_list.append(int(line))
                    print("ERROR:" + error + ", Line:" + line)

            match = re.match(r'^%Warning.+?:\s(?P<file>.+?\.v):(?P<line>\d+?):\s(?P<warning>.+?)$', line)
            if match:
                fname, warning, line = match.group('file'), match.group('warning'), match.group('line')
                if fname == BaseFileName and int(line) not in line_list:
                    self.add_message(int(line), lines, warning, warningMessages)
                    line_list.append(int(line))
                    print("WARNING:" + warning + ", Line:" + line)
