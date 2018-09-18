"""    Find out, when last commit was done
"""
from subprocess import Popen, PIPE
from os import path

def revision_info(src_path, store_dir=None):

    # Get git log info

    moment = "Unknown"
    
    month_dict = {"Jan":1,"Feb":2,"Mar":3,"Apr":4, "May":5, "Jun":6,
                  "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

    gitproc = Popen(['git', 'log', '-1'], stdout = PIPE, cwd=src_path)
    (stdout, _) = gitproc.communicate()
    git_out = stdout.strip().decode("utf-8")
#     print (git_out)
    for line in git_out.splitlines():
        if line.startswith("Date:"):
            # Date:   Sun Aug 26 10:54:26 2018 +0300
            a = line.split()
            moment = "{}.{}.{} {}".format(a[3], month_dict[a[2]], a[5], a[4])
    
    print("Git version {}".format(moment))
    
    if store_dir:
        # Store a text file in the log directory
        rev_info_filename = path.join(store_dir, 'revision_info.txt')
        with open(rev_info_filename, "w") as text_file:
            text_file.write('{}\n'.format(moment))
    return moment

# revision_info(".", "app")
