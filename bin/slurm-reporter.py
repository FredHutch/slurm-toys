#! /usr/bin/env python3

# slurm-reporter reads the database table export (tsv) of the slurm_jobs table
# and groups all jobs by the full hour and 
#
# slurm-reporter dirkpetersen / Apr 2020
#

import sys, os, argparse, socket, pandas
#import subprocess, numpy, tempfile, datetime, re, glob, time


class KeyboardInterruptError(Exception): pass

def main():

    # Set up logging.  Show error messages by default, show debugging 
    # info if specified.
    #log = logger('slurm-reporter', args.debug)
    #log.debug('slurm-limiter - starting execution at %s' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    #log.debug('Parsed arguments: %s' % args)

    hostname = socket.gethostname()
    if not os.path.exists(args.tsvfile):
        print('File %s does not exist' % args.tsvfile)
        return False

    filebase = os.path.splitext(os.path.basename(args.tsvfile))[0]
    outputfile = '%s.xlsx' % filebase

    print('   Reading TSV file .....')
    df=pandas.read_csv(args.tsvfile,sep='\t', low_memory=0)
    df1=df.filter(['id_job','job_name','account','id_user','partition','work_dir','time_submit','time_start','time_end','cpus_req'], axis=1)
    df.drop()
    df = df1.query('time_start>0 & time_end>0 ')
    df['cpu_sec'] = (df['time_end'] - df['time_start']) * df['cpus_req']
    df['hour_start']=pd.to_datetime(df['time_start'], unit = 's').dt.round('60min')
    print('   Writing to Pickle .....')
    df.to_pickle('%s.zip' % filebase)
    print('   Writing to Excel .....')
    df.groupby('hour_start')['cpu_sec'].agg(['sum','count']).to_excel(outputfile,sheet_name='hourly-summary') 


    #from sqlalchemy import create_engine
    #engine = create_engine('postgresql://dirk:mydb123@mydb:32063/petersen')
    #df3.to_sql('gizmo_jobs_2020', engine)
            

def logger(name=None, stderr=False):
    import logging, logging.handlers
    # levels: CRITICAL:50,ERROR:40,WARNING:30,INFO:20,DEBUG:10,NOTSET:0
    if not name:
        name=__file__.split('/')[-1:][0]
    l=logging.getLogger(name)
    l.setLevel(logging.INFO)
    f=logging.Formatter('%(name)s: %(levelname)s:%(module)s.%(lineno)d: %(message)s')
    # logging to syslog
    s=logging.handlers.SysLogHandler('/dev/log')
    s.formatter = f
    l.addHandler(s)
    if stderr:
        l.setLevel(logging.DEBUG)
        # logging to stderr        
        c=logging.StreamHandler()
        c.formatter = f
        l.addHandler(c)
    return l

def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='slurm-reporter',
        description='slurm-reporter processes an export of the slurm jobs table ' + \
        'cluster and adjusts the account and user limits dynamically within certain range')
    parser.add_argument( 'tsvfile', action='store', type='str',
        help='output of xxx_job_table as tab delimited file',
        default='' )    
    parser.add_argument( '--debug', '-d', dest='debug', action='store_true',
        help='verbose output for all commands',
        default=False ) 
    parser.add_argument( '--cluster', '-M', dest='cluster',
        action='store',
        help='name of the slurm cluster, (default: current cluster)',
        default='' )           
    parser.add_argument( '--partition', '-p', dest='partition',
        action='store',
        help='partition of the slurm cluster (default: entire cluster)',
        default='' )
        
    args = parser.parse_args()        
    if args.debug:
        print('DEBUG: Arguments/Options: %s' % args)    
    return args

if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_arguments()
    sys.exit(main())
