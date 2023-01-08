#!/usr/bin/env python

import os
import re
import json
import logging
import paramiko, socket
from collections import namedtuple

Credentials = namedtuple('Credentials', ['principal', 'secret'])
Hostname = namedtuple('Hostname', ['hostname'])
Collected_data = namedtuple('Collected_data', ['git_branch', 'git_revision', 'svn_branch', 'svn_revision'])

absolute_path = os.path.dirname(__file__)
relative_path= "data/inventory.json"
inventrory_path= os.path.join(absolute_path, relative_path)

def get_credential(inventrory_path, cluster):
    with open(inventrory_path) as inventory:
        data = json.load(inventory)

    try:
        username = data['hosts'][cluster]['user']
        secret = username
    except KeyError:
        logging.error(f'JSON does not contain credential in expected format(user) for {cluster}')
        raise
    try:
        ssh_key_path = data['hosts'][cluster]['ssh_key_path']
        secret = ssh_key_path
    except KeyError:
        logging.warning(f'Does not contain ssh_path for {cluster} (password connection is not secure)')
    else: secret=ssh_key_path
    return Credentials(principal=username, secret=secret)

def get_hostname(inventrory_path, cluster):
    with open(inventrory_path) as inventory:
        data = json.load(inventory)
    try:
        host = data['hosts'][cluster]['host']
    except KeyError:
        logging.error(f'JSON does not contain credential in expected format(host) for {cluster}')
        raise
    return Hostname(hostname=host)

def initialize_ssh(cluster):

    host=get_hostname(inventrory_path, cluster).hostname
    user=get_credential(inventrory_path, cluster).principal
    secret=get_credential(inventrory_path, cluster).secret

    n = 0
    while n <= 3:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            """Check if secret handle *.pub key (path to it expected)"""
            if ".pub" in secret:
                ssh.connect(hostname=host, username=user, key_filename=secret)
            else:
                ssh.connect(hostname=host, username=user, password=secret)
            return ssh
        except paramiko.AuthenticationException:
            logging.error("Authentication failed, please verify your credentials: %s")
        except paramiko.SSHException as sshException:
            logging.error("Unable to establish SSH connection: %s" % sshException)
            continue
        except socket.error as e:
            logging.error(f"Unable to establish SSH connection ({user}): %s" % e)
            n += 1
            break
    raise Exception

def collect_data(ssh, cvs_path):
    """Simple way to check directory exsistence"""
    stdin, stdout, stderr = ssh.exec_command('ls ' + cvs_path)
    if stderr.readlines():
        logging.error(f'Requested CSV directory ({cvs_path}) doest exsist')
    else:
        stdin, stdout, stderr = ssh.exec_command('cd ' + cvs_path + ' && ' + 'git branch --show-current')
        if not stderr.readlines():
            for line in stdout.readlines():
                git_branch = line
                stdin, stdout, stderr = ssh.exec_command('cd ' + cvs_path + ' && ' + 'git rev-list --count HEAD')
                for line in stdout.readlines():
                        git_revision = line
        else:
            git_branch = ''
            git_revision = ''
        if not git_branch:
            logging.warning(f'Working copy doesnt use git, usage of SVN (mostly deprecated) will be checked')
            stdin, stdout, stderr = ssh.exec_command('svn info ' + cvs_path)
            if not stderr.readlines():
                for line in stdout.readlines():
                    svn_info = line
                    branch_string = re.search(r"URL:\s\d+", str(svn_info)).group()
                    revision_string = re.search(r"Revision:\s\d+", str(svn_info)).group()
                    svn_branch = branch_string.split(': ')[1]
                    svn_revision = revision_string.split(': ')[1]
            else:
                logging.error(f'Specified directory ({cvs_path}) doest use git or svn')
        else:
            svn_branch = ''
            svn_revision = ''
    return Collected_data(git_branch, git_revision, svn_branch, svn_revision)

def main():
    global cvs_path
    cvs_path = "~/bw/"
    cluster_list = ["EU-CLUSTER", "NA-CLUSTER"]

    for cluster in cluster_list:
        try:
            ssh = initialize_ssh(cluster)
            git_branch = collect_data(ssh, cvs_path).git_branch
            git_revision = collect_data(ssh, cvs_path).git_revision
            svn_branch = collect_data(ssh, cvs_path).svn_branch
            svn_revision = collect_data(ssh, cvs_path).svn_revision

            if git_branch:
                with open(inventrory_path, "r") as inventory:
                    data = json.load(inventory)

                data['hosts'][cluster]['git_branch'] = git_branch.rstrip()
                with open(inventrory_path, "w") as inventory:
                    json.dump(data, inventory, indent = 4)

            if git_revision:
                with open(inventrory_path, "r") as inventory:
                    data = json.load(inventory)

                data['hosts'][cluster]['git_revision'] = git_revision.rstrip()
                with open(inventrory_path, "w") as inventory:
                    json.dump(data, inventory, indent = 4)

            if svn_branch:
                with open(inventrory_path, "r") as inventory:
                    data = json.load(inventory)

                data['hosts'][cluster]['svn_branch'] = svn_branch.rstrip()
                with open(inventrory_path, "w") as inventory:
                    json.dump(data, inventory, indent = 4)

            if svn_revision:
                with open(inventrory_path, "r") as inventory:
                    data = json.load(inventory)

                data['hosts'][cluster]['svn_revision'] = svn_revision.rstrip()
                with open(inventrory_path, "w") as inventory:
                    json.dump(data, inventory, indent = 4)
        except:
            pass

if __name__ == "__main__":
    main()
