#! /usr/bin/env python3

# slurm-limiter checks the current util of a slurm cluster and adjusts
# the limits dynamically within certain a range  
#
# slurm-limiter dirkpetersen / Oct 2017
#

import sys, os, argparse, time, socket, subprocess, pandas, numpy, tempfile, datetime, re, glob

class KeyboardInterruptError(Exception): pass

prometheus_folder = '/opt/node_exporter/metrics_dump'
default_cluster = 'gizmo'
default_partition = 'campus'

def main():

    # Set up logging.  Show error messages by default, show debugging 
    # info if specified.
    log = logger('slurm-limiter', args.debug)
    #log.debug('slurm-limiter - starting execution at %s' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.debug('Parsed arguments: %s' % args)

    hostname = socket.gethostname()

    squeuecmd = ['squeue', '--format=%i;%P;%t;%D;%C;%a;%u']
    sinfocmd = ['sinfo', '--format=%n;%c;%m;%f;%O;%e;%t', '--responding']
    sacctmgrcmd = ['sacctmgr', 'list', 'qos', 'where', 'name=%s' % args.qos, 
                'format=maxtresperuser,maxtresperaccount', 
                '--parsable2', '--noheader']
    
    sacctmgrupd = "sacctmgr -i update qos where name=%s set maxtresperuser=cpu=#UCPU# maxtresperaccount=cpu=#ACPU#" % args.qos
    #  sacctmgrcmd returns cpu=xxx|cpu=yyy

    headeroffset = 0
    if args.cluster != '':
        headeroffset = 1
        squeuecmd.append('--cluster=%s' % args.cluster)
        sinfocmd.append('--cluster=%s' % args.cluster)
    else:
        args.cluster = default_cluster

    if args.partition != '':
        squeuecmd.append('--partition=%s' % args.partition)
        sinfocmd.append('--partition=%s' % args.partition)
    else:
        args.partition = default_partition
        
    squeue = subprocess.Popen(squeuecmd, stdout=subprocess.PIPE)
    sinfo = subprocess.Popen(sinfocmd, stdout=subprocess.PIPE)
    sacctmgr = subprocess.Popen(sacctmgrcmd, stdout=subprocess.PIPE)
        
    sacctmgr2 = sacctmgr.stdout.read().decode("utf-8").rstrip().replace('cpu=','').split('|')
    ulimitold = int(sacctmgr2[0])
    alimitold = int(sacctmgr2[1])
    
    jobs=pandas.read_table(squeue.stdout, sep=';', header=headeroffset)
    if args.partition != '':
        jobs = jobs[(jobs['PARTITION']==args.partition)]
    nodes=pandas.read_table(sinfo.stdout, sep=';', header=headeroffset)
    if args.feature != '':
        nodes = nodes[(nodes['FEATURES'].str.contains(args.feature))]
    
    # are there any jobs running
    if len(jobs.index) == 0:
        log.debug('No jobs running, really?')
        return True
        
    if args.debug:
        print(jobs.groupby(["PARTITION","ACCOUNT","USER"]).sum()["CPUS"])   
        
    # getting running cores, pending cores, total cores
    jrunning = jobs[jobs['ST'] == 'R'].sum()["CPUS"]
    jpending = jobs[jobs['ST'] == 'PD'].sum()["CPUS"]
    tcores = nodes[nodes['STATE'] != 'drain'].sum()["CPUS"]     
    idlenodes = nodes[nodes['STATE'] == 'idle'].count()['STATE']
    
    if numpy.isnan(jrunning): jrunning = 0
    if numpy.isnan(jpending): jpending = 0
    if numpy.isnan(tcores): tcores = 0
    if numpy.isnan(idlenodes): idlenodes = 0
            
    log.info('Cores: running=%i, pending=%i, total=%i, Usage=%i %%, Limits: %i / %i, Nodes: idle=%i' % 
            (jrunning, jpending, tcores, int(jrunning/tcores*100), alimitold, ulimitold, idlenodes))
        
    # are there fewer pending jobs that our minimum threshold?
    if jpending < args.minpending:
        log.debug('Not adjusting limits, not enough pending jobs')
        return True
    
    # do we not have enough idle nodes ?
    # This does not work because of the restart queue
    #if idlenodes < args.minidlenodes:
    #    log.info('Not enough idle nodes, throttling to minimum limit of %i cores' % args.minlimit)
    #    # set the new limits 
    #    ulimitnew=args.minlimit+args.userlimitoffset
    #    alimitnew=args.minlimit        
    
    # is the percent usage above the max target usage plus 5%?
    if jrunning/tcores*100 > args.maxpercentuse+5 or jrunning/tcores == 1:
        log.info('Utilization > 5%% above max, throttling to minimum limit of %i cores' % args.minlimit)
        ulimitnew=args.minlimit+args.userlimitoffset
        alimitnew=args.minlimit        
        
    # is the percent usage above the max target usage?
    elif jrunning/tcores*100 > args.maxpercentuse:
        # yes, dial it down a little, but only by --changestep
        alimitnew = alimitold-args.changestep
        ulimitnew = alimitnew+args.userlimitoffset
        if alimitnew < args.minlimit:
            alimitnew = args.minlimit
            ulimitnew = alimitnew+args.userlimitoffset
        if alimitnew != alimitold:
            log.info('Usage above %i %%, throttling by %i %%...' % 
                     (args.maxpercentuse, args.changestep))
    else:
        # no, let's increase it again. 
        alimitnew=alimitold+args.changestep
        ulimitnew=alimitnew+args.userlimitoffset
        # if the new limit would exceed the max, set the max
        if alimitnew > args.maxlimit:
            alimitnew = args.maxlimit
            ulimitnew = alimitnew+args.userlimitoffset
        if alimitnew != alimitold:
            log.info('Usage below %i %%, increasing limit to %s / %s ...' % 
                    (args.maxpercentuse, alimitnew, ulimitnew))
                
    sacctmgrupd = sacctmgrupd.replace('#UCPU#', str(ulimitnew))
    sacctmgrupd = sacctmgrupd.replace('#ACPU#', str(alimitnew)) 
    
    # adding prometheus exporters for monitoring. 
    if not os.path.exists(prometheus_folder):        
        os.makedirs(prometheus_folder)
    # exporter for displaying account limits (# of cores)
    with open(os.path.join(prometheus_folder,'hpc_%s_%s_account_limit.prom' % (args.cluster, args.partition)), 'w') as fh:        
        fh.write('# TYPE hpc_%s_%s_account_limit_current gauge\n' % (args.cluster, args.partition))
        fh.write('hpc_%s_%s_account_limit_current %s\n\n' % (args.cluster, args.partition, alimitnew))
        fh.write('# TYPE hpc_%s_%s_account_limit_sla gauge\n' % (args.cluster, args.partition))
        fh.write('hpc_%s_%s_account_limit_sla %s\n\n' % (args.cluster, args.partition, args.slalimit))
        fh.write('# TYPE hpc_%s_%s_account_limit_max gauge\n' % (args.cluster, args.partition))
        fh.write('hpc_%s_%s_account_limit_max %s\n\n' % (args.cluster, args.partition, args.maxlimit))
        fh.write('# TYPE hpc_%s_%s_account_limit_min gauge\n' % (args.cluster, args.partition))
        fh.write('hpc_%s_%s_account_limit_min %s\n\n' % (args.cluster, args.partition, args.minlimit))
    # exporter for displaying % utilization 
    with open(os.path.join(prometheus_folder,'hpc_%s_%s_usage_percent.prom' % (args.cluster, args.partition)), 'w') as fh:
        fh.write('# TYPE hpc_%s_%s_usage_percent_max gauge\n' % (args.cluster, args.partition))
        fh.write('hpc_%s_%s_usage_percent_max %s\n\n' % (args.cluster, args.partition, args.maxpercentuse))
        fh.write('# TYPE hpc_%s_%s_usage_percent_current gauge\n' % (args.cluster, args.partition))
        fh.write('hpc_%s_%s_usage_percent_current %s\n\n' % (args.cluster, args.partition, int(jrunning/tcores*100)))
                  
    # only execute sacctmgr if there is actually a change 
    if alimitnew != alimitold or ulimitnew != ulimitold:
        log.info('executing %s ...' % sacctmgrupd)
        sacctmgrupdcmd = sacctmgrupd.split(" ")
        # run sacctmgr to update the QOS limits
        ret = subprocess.Popen(sacctmgrupdcmd, stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        stderr = ret.stderr.read().decode("utf-8").rstrip()
        retcode = ret.wait()
        if retcode > 0:
            log.error("Error executing sacctmgr. Error message: %s\n" % (stderr))

        if alimitnew < args.slalimit:
            if alimitnew < alimitold:
                log.warning('SLA breach, reducing account limits below SLA of %i cores' % args.slalimit)
            # only send mail while SLA is breached 
            try:
                if args.erroremail:
                    send_mail([args.erroremail,], "Slurm (account: %s / user: %s) SLA breach. Limits changed!" % (alimitnew,ulimitnew),
                        "The SLURM limits were changed. We are not meeting the SLA Account Limit!\n\n" \
                        "Cluster: %s \n" \
                        "Partition: %s \n" \
                        "Features: %s \n" \
                        "Idle Nodes (incl. restart): %i \n" \
                        "SLA Account Limit: %i \n" \
                        "Previous Account Limit: %i \n" \
                        "Previous User Limit: %i \n" \
                        "Cores: running=%i, pending=%i, total=%i, Usage=%i %% \n" \
                        "\n" % (args.cluster, args.partition, args.feature, 
                        idlenodes, args.slalimit, alimitold, ulimitold, 
                        jrunning, jpending, tcores, int(jrunning/tcores*100)))
                    log.debug('Sent warning email to %s' % args.erroremail) 
                else:
                    log.error("No email address set via --error-email")
            except:
                e=sys.exc_info()[0]
                sys.stderr.write("Error in send_mail while sending to '%s': %s\n" % (args.erroremail, e))
                log.error("Error in send_mail while sending to '%s': %s\n" % (args.erroremail, e))
    else:
        log.debug('no account limit changes required')
    
    #do we need some file stubs?
    ## if user is idle, delete stub /tmp/loadwatcher.py_USER.stub
    #for fl in glob.glob(tempfile.gettempdir()+'/'+os.path.basename(__file__)+'_*.stub'):
        #if not fl[20:-5] in userutil:
            #log.info('deleting stub %s ...' % fl)
            #os.unlink(fl)                
            
def send_mail(to, subject, text, attachments=[], cc=[], bcc=[], smtphost="", fromaddr=""):

    if sys.version_info[0] == 2:
        from email.MIMEMultipart import MIMEMultipart
        from email.MIMEBase import MIMEBase
        from email.MIMEText import MIMEText
        from email.Utils import COMMASPACE, formatdate
        from email import Encoders
    else:
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email.utils import COMMASPACE, formatdate
        from email import encoders as Encoders
    from string import Template
    import socket
    import smtplib

    if not isinstance(to,list):
        print("the 'to' parameter needs to be a list")
        return False    
    if len(to)==0:
        print("no 'to' email addresses")
        return False
    
    myhost=socket.getfqdn()

    if smtphost == '':
        smtphost = get_mx_from_email_or_fqdn(myhost)
    if not smtphost:
        sys.stderr.write('could not determine smtp mail host !\n')
        
    if fromaddr == '':
        fromaddr = os.path.basename(__file__) + '-no-reply@' + \
           '.'.join(myhost.split(".")[-2:]) #extract domain from host
    tc=0
    for t in to:
        if '@' not in t:
            # if no email domain given use domain from local host
            to[tc]=t + '@' + '.'.join(myhost.split(".")[-2:])
        tc+=1

    message = MIMEMultipart()
    message['From'] = fromaddr
    message['To'] = COMMASPACE.join(to)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = subject
    message['Cc'] = COMMASPACE.join(cc)
    message['Bcc'] = COMMASPACE.join(bcc)

    body = Template('This is a notification message from $application, running on \n' + \
            'host $host. Please review the following message:\n\n' + \
            '$notify_text\n\nIf output is being captured, you may find additional\n' + \
            'information in your logs.\n'
            )
    host_name = socket.gethostname()
    full_body = body.substitute(host=host_name.upper(), notify_text=text, application=os.path.basename(__file__))

    message.attach(MIMEText(full_body))

    for f in attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(f, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        message.attach(part)

    addresses = []
    for x in to:
        addresses.append(x)
    for x in cc:
        addresses.append(x)
    for x in bcc:
        addresses.append(x)

    smtp = smtplib.SMTP(smtphost)
    smtp.sendmail(fromaddr, addresses, message.as_string())
    smtp.close()

    return True

def get_mx_from_email_or_fqdn(addr):
    """retrieve the first mail exchanger dns name from an email address."""
    # Match the mail exchanger line in nslookup output.
    MX = re.compile(r'^.*\s+mail exchanger = (?P<priority>\d+) (?P<host>\S+)\s*$')
    # Find mail exchanger of this email address or the current host
    if '@' in addr:
        domain = addr.rsplit('@', 2)[1]
    else:
        domain = '.'.join(addr.rsplit('.')[-2:])
    p = os.popen('/usr/bin/nslookup -q=mx %s' % domain, 'r')
    mxes = list()
    for line in p:
        m = MX.match(line)
        if m is not None:
            mxes.append(m.group('host')[:-1])  #[:-1] just strips the ending dot
    if len(mxes) == 0:
        return ''
    else:
        return mxes[0]

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
    parser = argparse.ArgumentParser(prog='slurm-limiter',
        description='slurm-limiter checks the current util of a slurm ' + \
        'cluster and adjusts the account and user limits dynamically within certain range')
    parser.add_argument( '--debug', '-d', dest='debug', action='store_true',
        help='verbose output for all commands',
        default=False ) 
    parser.add_argument( '--error-email', '-e', dest='erroremail',
        action='store',
        help='send errors to this email address.',
        default='' )   
    parser.add_argument( '--cluster', '-M', dest='cluster',
        action='store',
        help='name of the slurm cluster, (default: current cluster)',
        default='' )           
    parser.add_argument( '--partition', '-p', dest='partition',
        action='store',
        help='partition of the slurm cluster (default: entire cluster)',
        default='' )
    parser.add_argument( '--feature', '-f', dest='feature',
        action='store',
        help='filter for only this slurm feature',
        default='' )     
    parser.add_argument( '--qos', '-q', dest='qos',
        action='store',
        help='slurm QOS to use for changing account limits (default: %(default)s)',
        default='public' )                          
    parser.add_argument( '--maxaccountlimit', '-x', dest='maxlimit',
        action='store',
        type=int,
        help='maximum account limit, never go above this (default: %(default)s)',
        default=300 )             
    parser.add_argument( '--minaccountlimit', '-n', dest='minlimit',
        action='store',
        type=int,
        help='minimum account limit, never go below this (default: %(default)s)',
        default=100 )
    parser.add_argument( '--slaaccountlimit', '-t', dest='slalimit',
        action='store',
        type=int,
        help='min SLA limit that has been committed to customers, ' + \
             'notify via email if breached (default: %(default)s)',
        default=150 )
    parser.add_argument( '--userlimitoffset', '-o', dest='userlimitoffset',
        action='store',
        type=int,
        help='offset of userlimit from account limit, set a negative ' + \
             'number for a userlimit lower than account limit (default: %(default)s)',
        default=20 )
    parser.add_argument( '--changestep', '-s', dest='changestep',
        action='store',
        type=int,
        help='increase or decrease the limit by this # of cores (default: %(default)s)',
        default=10 )
    parser.add_argument( '--minpending', '-i', dest='minpending',
        action='store',
        type=int,
        help='minimum number of jobs that have to be pending to take action (default: %(default)s)',
        default=50 )      
    parser.add_argument( '--maxpercentuse', '-u', dest='maxpercentuse',
        action='store',
        type=int,
        help='maximum allowed %% usage in this cluster or partition ' + \
             'Throttle QOS down by --changestep if exceeded. (default: %(default)s)',
        default=90 )
    parser.add_argument( '--minidlenodes', '-w', dest='minidlenodes', 
        action='store',
        type=int,
        help='critical minimum number of idle nodes. Throttle QOS down ' + \
             'to --minaccountlimit if exceeded. (default: %(default)s)',
        default=5 )   
        
    args = parser.parse_args()        
    if args.debug:
        print('DEBUG: Arguments/Options: %s' % args)    
    return args

if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_arguments()
    sys.exit(main())
