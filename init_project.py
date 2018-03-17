#!/usr/bin/env python3

import os
from tempfile import mkdtemp
from shutil import rmtree
import glob
from pprint import pprint


PREFIX = '===>'

# User input for template replacement params
PARAMS = dict(
    # Which template to use
    github_repo_name = 'pl-demo',
    template_type = 'java-maven',
    domain = 'demo',
    subdomain = 'java',
    java_package = 'verycool',
)

CONFIG = dict(
    # Path to temp dir holding our template tempsource
    source_dir_path = '',
    # Path to the new project
    template_target = '/Users/starver/code/cna/pl-demo/',
)


# ~~GITHUB_REPO_NAME~~
github_repo_targets = [
    './Jenkinsfile',
    './pom.xml',
    './jenkins/scripts/*',
    './src/main/resources/logback.xml',
]


# ~~DOMAIN~~
domain_targets = [
    './helm/~~GITHUB_REPO_NAME~~/templates/ingress.yaml'
]

# ~~SUBDOMAIN~~
subdomain_targets = [
    './helm/~~GITHUB_REPO_NAME~~/templates/ingress.yaml'
]

# This is the io.ctl.platform/ folder all source is under
# First change that folder name
# ~~SRC_FOLDER~~
subdomain_targets = [
    './src/main/java/*'
]



def clone_template():
    """ Clone pl-cloud-starter to a temp dir """

    # TODO: protect against overwriting current dir contents

    CONFIG['source_dir_path'] = mkdtemp(prefix='pl-cloud-starter-template')
    print("{} Created temp directory {}".format(PREFIX, CONFIG['source_dir_path']))

    print("{} Cloning pl-cloud-starter to temp dir".format(PREFIX))
    cwd = os.getcwd()
    os.chdir(CONFIG['source_dir_path'])
    os.system('git clone https://github.com/CenturyLinkCloud/pl-cloud-starter.git')

    # TODO: Remove these 3 lines immediately prior to merge to master
    print("{} TODO: Remove me: Changing to template branch".format(PREFIX))
    os.chdir('pl-cloud-starter')
    os.system('git checkout template')

    os.chdir(cwd)


def copy_template():
    """ Copy the template source to the target dir """
    print("{} Copying template to new GitHub repo {}".format(PREFIX, CONFIG['template_target']))
    template_dir = "{}/pl-cloud-starter/template/{}/".format(CONFIG['source_dir_path'], PARAMS['template_type'])
    os.system("cp -r {} {}".format(template_dir, CONFIG['template_target']))


def cleanup():
    """ Remove temporary items """
    print("{} Removing {}".format(PREFIX, CONFIG['source_dir_path']))
    rmtree(CONFIG['source_dir_path'])


def get_file_list(root_dir):
    """ Return a list of paths to all files in all directories and sub-directories """
    result = []
    for filename in glob.iglob(root_dir + '**/*', recursive=True):
        if os.path.isfile(filename):
            result.append(filename[2:])
    return result


def replace_keywords():
    """ """
    params = {
        '~~GITHUB_REPO_NAME~~': PARAMS['github_repo_name'],
        '~~DOMAIN~~': PARAMS['domain'],
        '~~SUBDOMAIN~~': PARAMS['subdomain'],
        '~~JAVA_PACKAGE~~': PARAMS['java_package'],
    }
    files = get_file_list('./')

    print("{} Applying template to {}".format(PREFIX, CONFIG['template_target']))
    for k,v in params.items():
        for file in files:
            os.system("sed -i '' 's/{}/{}/g' {} > /dev/null".format(k, v, file))

    print("{} Updating directroy structure".format(PREFIX))
    # Change dir to match java package name
    base = 'src/main/java/io/ctl'
    os.system("mv {}/platform/ {}/{}/".format(base, base, PARAMS['domain']))

    base = "src/main/java/io/ctl/{}".format(PARAMS['domain'])
    os.system("mv {}/cloudStarterJava/ {}/{}/".format(base, base, PARAMS['java_package']))

    # Rename helm/main to helm/~~GITHUB_REPO_NAME~~
    os.system("mv helm/main helm/{}".format(PARAMS['github_repo_name']))

    print("{} Committing project files to git".format(PREFIX))
    os.system('git add --all')
    os.system("git commit -am 'Initial {} template'".format(PARAMS['template_type']))


def print_remaining_task_list():
    print("{} Next steps:".format(PREFIX))
    print("     1. Review code and refine naming as necessary")
    print("     2. Run project and test endpoints")
    print("        * mvn spring-boot:run")
    print("        * http://localhost:8080/actuator")
    print("        * http://localhost:8080/prometheus")
    print("        * http://localhost:8080/healthz/readiness")
    print("        * http://localhost:8080/healthz/liveness")
    print("        * http://localhost:8080/healthz/ping")
    print("        * http://localhost:8080/v3/{}/{}/contacts".format(PARAMS['domain'], PARAMS['subdomain']))
    print("     3. Push to GitHub")
    print("     4. Create a DNS name in DEV using the GitHub repo name, pointing to k8s")
    print("     5. Create a Jenkins build job")
    print("       * Copy an existing java project")
    print("       * Point it at this GitHub repo")
    print("     6. Build")
    print("     7. Verify k8s deploy: http://{}/v3/{}/{}/contacts".format(PARAMS['github_repo_name'], PARAMS['domain'], PARAMS['subdomain']))


def validate_args():
    """ verify args sane """
    # Does the template target exist?
    if(not os.path.exists(CONFIG['template_target'])):
        print("{} Target directory does not exist: {}".format(PREFIX, CONFIG['template_target']))
        print("{} Cannot continue".format(PREFIX))
        exit(1)


def main():

    validate_args()
    clone_template()
    copy_template()
    replace_keywords()

    cleanup()
    print_remaining_task_list()


main()
