"""    Find out, when last commit was done
"""
from subprocess import Popen, PIPE

class Chkdate():
    ''' Methods to find app version dates '''

    month_dict = {"Jan":1,"Feb":2,"Mar":3,"Apr":4, "May":5, "Jun":6,
                  "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

    def __init__(self):
        self.moment_long = 'Unidefined'
        self.moment_short = self.moment_long

        # Get git log info
        gitproc = Popen(['git', 'log', '-1'], stdout = PIPE)    #, cwd=src_path)
        (stdout, _) = gitproc.communicate()
        git_out = stdout.strip().decode("utf-8")

        for line in git_out.splitlines():
            if line.startswith("Date:"):
                # Date:   Sun Aug 26 10:54:26 2018 +0300
                a = line.split()
                self.moment_short = "{}.{}.{}".format(a[3], Chkdate.month_dict[a[2]], a[5])
                self.moment_long = "{} {}".format(self.moment_short, a[4])
        
        print("Git version {}".format(self.moment_long))


    def revision_time(self):
        ''' Returns the git commit date and time "18.9.2018 13:19:23" '''
        return self.moment_long


    def revision_date(self):
        ''' Returns the git commit date "18.9.2018" '''
        return self.moment_short

