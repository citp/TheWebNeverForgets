import paramiko
from os.path import join, basename

##############################################
# Configure SSH for auto-uploading crawl data
SSH_KEY_FILE = ''
SSH_USERNAME = ''
SSH_DEST_DIR = ''
SSH_HOSTNAME = ''
##############################################

# Set log of paramiko
paramiko.util.log_to_file('/tmp/paramiko.log')


def get_sftp_connection(host=SSH_HOSTNAME, username=SSH_USERNAME):
    priv_key = paramiko.RSAKey.from_private_key_file(SSH_KEY_FILE)
    transport = paramiko.Transport((SSH_HOSTNAME, 22))
    transport.connect(username=username, pkey=priv_key)
    sftp = paramiko.SFTPClient.from_transport(transport)
    return transport, sftp


def get_ssh_connection(host=SSH_HOSTNAME, username=SSH_USERNAME):
    priv_key = paramiko.RSAKey.from_private_key_file(SSH_KEY_FILE)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, pkey=priv_key)
    transport = ssh.get_transport()
    return ssh, transport


def scp_put(local, remote):
    """Put a file into server through scp."""
    trans, sftp = get_sftp_connection()
    sftp.put(remotepath=remote, localpath=local)
    sftp.close()
    trans.close()


def scp_put_to_server(local, remote=None):
    """Put a file into server through scp."""
    trans, sftp = get_sftp_connection()
    if remote is None:
        base_name = basename(local)
        remote = join(SSH_DEST_DIR, base_name)
    sftp.put(remotepath=remote, localpath=local)
    sftp.close()
    trans.close()


def scp_get(remote, local):
    """Get a file from server through scp."""
    trans, sftp = get_sftp_connection()
    sftp.get(remotepath=remote, localpath=local)
    sftp.close()
    trans.close()


def run_command(command):
    """Send command through ssh to server."""
    ssh, _ = get_ssh_connection()
    ssh.exec_command(command)
    ssh.close()
