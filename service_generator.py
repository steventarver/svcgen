#!/usr/bin/env python3

import os
from tempfile import mkdtemp
from shutil import rmtree
import glob


USER_INSTRUCTIONS = '''
Service Generator

This script will initialize a new GitHub repo dir with skeleton service code.

The following should be true:
 1. I have created a new GitHub repo
 2. I have cloned that repo
 3. I don't have any other files in that repo dir but the .git directory
 4. I started this script from that new repo directory

Now, we will collect some information to customize your project
 domain:       The domain is a family of services that this service belongs to; the 
               functional area it will target. E.g. billing, network, etc.
               The domain is used to define the java package and ReST paths.
 subdomain:    The subdomain refines the scope of the service. Smaller domains
               may use the main, top level resource collections. 
               E.g. quotes in /billing/quotes, vpn in /network/vpn
               The subdomain is used to define the ReST path.
 java package: This information lets you customize the java package structure.
               Source code will be placed in io.ctl.{domain}.{java_package}

If you don't like the resulting package structure, you can:
 1. Delete all files in this directory except the .git directory and start over.
 2. Refactor the package paths in your IDE and manually update the path in the
    second host rule in helm/{github_repo_name}/templates/ingress.yaml
'''

PREFIX = '===>'

# User input for template replacement params
CONFIG = dict(
    github_repo_name = '',
    # Which template to use - java-maven is the only supported template at the moment
    template_type = 'java-maven',
    domain = '',
    subdomain = '',
    java_package = '',
    # Path to temp dir holding our template tempsource
    template_source='',
    # Path to the new project
    template_target='',
)


def cleanup():
    """ Remove temporary items """
    print("{} Removing {}".format(PREFIX, CONFIG['template_source']))
    rmtree(CONFIG['template_source'])


def clone_template():
    """ Clone pl-cloud-starter to a temp dir """
    CONFIG['template_source'] = mkdtemp(prefix='pl-cloud-starter-template')
    print("{} Created temp directory {}".format(PREFIX, CONFIG['template_source']))

    print("{} Cloning pl-cloud-starter to temp dir".format(PREFIX))
    cwd = os.getcwd()
    os.chdir(CONFIG['template_source'])
    os.system('git clone https://github.com/CenturyLinkCloud/pl-cloud-starter.git')

    # TODO: Remove these 3 lines immediately prior to merge to master
    print("{} TODO: Remove me: Changing to template branch".format(PREFIX))
    os.chdir('pl-cloud-starter')
    os.system('git checkout template')

    os.chdir(cwd)


def copy_template():
    """ Copy the template source to the target dir """
    print("{} Copying template to new GitHub repo {}".format(PREFIX, CONFIG['template_target']))
    template_dir = "{}/pl-cloud-starter/template/{}/".format(CONFIG['template_source'], CONFIG['template_type'])
    os.system("cp -r {} {}".format(template_dir, CONFIG['template_target']))


def gather_user_input():
    """ Get required input from user """
    print(USER_INSTRUCTIONS)

    cwd = os.getcwd()
    this_dir = os.path.basename(cwd)
    if not os.path.exists("{}/.git".format(cwd)):
        print("{} The current directory does not look like a GitHub repo dir - no .git directory present.".format(PREFIX))
        print("     Please review the above instructions to help identify the problem.")
        print("     Perhaps you are not in the GitHub repo dir. If not, cwd to the GitHub repo dir and retry.")
        print("     Cowardly refusing to continue.")
        exit(1)
    if len(os.listdir('.')) > 1:
        print("{} The current directory has files in it (other than the .git dir).".format(PREFIX))
        print("     Please review the above instructions to help identify the problem.")
        print("     Perhaps you are not in the GitHub repo dir. If so, remove those files and retry.")
        print("     Cowardly refusing to continue.")
        exit(1)

    CONFIG['template_target'] = cwd
    CONFIG['github_repo_name'] = this_dir

    CONFIG['domain'] = input("{} Enter your domain: ".format(PREFIX))
    CONFIG['subdomain'] = input("{} Enter your subdomain: ".format(PREFIX))
    CONFIG['java_package'] = input("{} Enter your java package: ".format(PREFIX))

    print("{} Using this configuration:".format(PREFIX))
    print("     template    : {}".format(CONFIG['template_target']))
    print("     target dir  : {}".format(CONFIG['template_target']))
    print("     repo name   : {}".format(CONFIG['github_repo_name']))
    print("     domain      : {}".format(CONFIG['domain']))
    print("     subdomain   ; {}".format(CONFIG['subdomain']))
    print("     java package: {}".format(CONFIG['java_package']))

    ok = input("{} Continue? [Yn]: ".format(PREFIX))
    if ok not in ['y', 'Y']:
        print("{} Exiting at user request".format(PREFIX))
        exit(1)


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
        '~~GITHUB_REPO_NAME~~': CONFIG['github_repo_name'],
        '~~DOMAIN~~': CONFIG['domain'],
        '~~SUBDOMAIN~~': CONFIG['subdomain'],
        '~~JAVA_PACKAGE~~': CONFIG['java_package'],
    }
    files = get_file_list('./')

    print("{} Applying template to {}".format(PREFIX, CONFIG['template_target']))
    for k,v in params.items():
        for file in files:
            os.system("sed -i '' 's/{}/{}/g' {} > /dev/null".format(k, v, file))

    print("{} Updating directroy structure".format(PREFIX))

    # Change dir to match java package name
    base = 'src/main/java/io/ctl'
    os.system("mv {}/platform/ {}/{}/".format(base, base, CONFIG['domain']))

    base = "src/main/java/io/ctl/{}".format(CONFIG['domain'])
    os.system("mv {}/cloudStarterJava/ {}/{}/".format(base, base, CONFIG['java_package']))

    base = 'src/test/java/io/ctl'
    os.system("mv {}/platform/ {}/{}/".format(base, base, CONFIG['domain']))

    base = "src/test/java/io/ctl/{}".format(CONFIG['domain'])
    os.system("mv {}/cloudStarterJava/ {}/{}/".format(base, base, CONFIG['java_package']))

    # Rename helm/main to helm/~~GITHUB_REPO_NAME~~
    os.system("mv helm/main helm/{}".format(CONFIG['github_repo_name']))

    print("{} Committing project files to git".format(PREFIX))
    os.system('git add --all')
    os.system("git commit -am 'Initial {} template'".format(CONFIG['template_type']))


def print_remaining_tasks():
    print("{} Next steps:".format(PREFIX))
    print("     1. Review code and refine naming as necessary")
    print("     2. Run project and test endpoints")
    print("        * mvn spring-boot:run")
    print("        * http://localhost:8080/actuator")
    print("        * http://localhost:8080/prometheus")
    print("        * http://localhost:8080/healthz/readiness")
    print("        * http://localhost:8080/healthz/liveness")
    print("        * http://localhost:8080/healthz/ping")
    print("        * http://localhost:8080/v3/{}/{}/contacts".format(CONFIG['domain'], CONFIG['subdomain']))
    print("     3. Push to GitHub")
    print("     4. Create a DNS name in DEV using the GitHub repo name, pointing to k8s")
    print("     5. Create a Jenkins build job")
    print("       * Copy an existing java project")
    print("       * Point it at this GitHub repo")
    print("     6. Build")
    print("     7. Verify k8s deploy: http://{}/v3/{}/{}/contacts".format(CONFIG['github_repo_name'], CONFIG['domain'], CONFIG['subdomain']))
    print("     8. Visit TODO tags for advanced configuration")


def main():

    gather_user_input()

    clone_template()
    copy_template()
    replace_keywords()

    cleanup()
    print_remaining_tasks()


main()

