'''
Näyttää syötteen otsikkotietoja

Created on 23.4.2017
@author: jm
'''
from re import match
from collections import OrderedDict

version = "1.0"

def add_args(parser):
    pass

def show_info(run_args, transformer, task_name=''):
    ''' Reaf gedgom HEAD info and count level 0 items
        Returns a list of descriptive lines
     '''
    input_gedcom = run_args['input_gedcom']
    enc = run_args['encoding']
    msg = []
    cnt = {}
    #msg.append(os.path.basename(input_gedcom) + '\n')
    try:
        with open(input_gedcom, 'r', encoding=enc) as f:
            for _ in range(100):
                ln = f.readline()
                if ln[:6] in ['2 VERS', '1 NAME', '1 CHAR']:
                    msg.append(ln[2:])
                if ln.startswith('1 SOUR'):
                    msg.append('Source ' + ln[7:-1] + ' ')
                if ln.startswith('1 GEDC'):
                    msg.append('Gedcom ')
                if ln.startswith('2 CONT _COMMAND'):
                    #print('"' + ln)
                    msg.append('– ' + ln[16:-1])
                if ln.startswith('2 CONT _DATE'):
                    msg.append(ln[12:])
                if match('0.*SUBM', ln):
                    msg.append('Submitter ')
                if match('0.*INDI', ln):
                    cnt['INDI'] = 1
                    break
            ln = '-'
            while ln:
                ln = f.readline()[:-1]
                if ln.startswith('0'):
                    flds = ln.split(maxsplit=2)
                    key = flds[-1][:4]
                    if key in cnt:
                        cnt[key] = cnt[key] + 1
                    elif key != 'TRLR':
                        cnt[key] = 1

    except OSError:     # End of file
        pass
    except UnicodeDecodeError as e:
        msg.append("Väärä merkistö, lisää esim. '--encoding ISO8859-1'")
    except Exception as e:
        msg.append( type(e).__name__ + str(e))

    if cnt:
        msg.append('        count\n')
    for i in OrderedDict(sorted(cnt.items())):
        msg.append('{:4} {:8}\n'.format(i, cnt[i]))
        
    return ''.join(msg)
