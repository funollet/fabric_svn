# -*- coding: utf-8 -*-
# fabfile.py
"""Fabric tasks for managing SVN repositories.

Creates repositories with a minimal tree; configure Apache to serve repository
via WebDAV; manages users.

Examples:

    # fab new:myproject
    # fab changeusers:myproject,"andy bert carl"
"""

# Copyright (C) 2010 Jordi Funollet <jordi.f@ati.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from fabric.api import *
from fabric.contrib.files import *

# Directory containing SVN configs for Apache.
env.apache_conf_dir = '/etc/apache2/conf.d/svn/'
# Directory for live CVS.
env.root_dir = '/home/svn'
# Directory for live CVS.
#env.cvs_root_dir = '/home/cvs'
# Directory for frozen (migrated, unmodificable) CVS.
#env.cvs_frozen_dir = '/home/cvs.migrated'



def __get_apache_conf_file(repository):
    """Return path to the Apache configuration.

    repository:     name of the repository
    """
    return os.path.join(env.apache_conf_dir, '%s.conf' % repository)


def __apache_restart():
    """Restart Apache to load new configuration."""
    run("apache2ctl -t")
    run("apache2ctl graceful")


def list():
    """List existing repositories."""
    run("ls %s" % env.root_dir)


def new(repository):
    """Creates repository and commits initial structure.

    repository:     name of the repository
    """

    repos_dir = os.path.join(env.root_dir,repository)

    if exists(repos_dir):
        abort("This is an existing repository.")

    # Create the repository.
    run("mkdir %s" % repos_dir)
    run("svnadmin create %s" % repos_dir)

    # Create a tree with the initial repository distribution.
    run("mkdir -p /tmp/svn_initial_tree/trunk")
    run("mkdir -p /tmp/svn_initial_tree/tags")
    run("mkdir -p /tmp/svn_initial_tree/branches")
    run("chmod -R 755 /tmp/svn_initial_tree/")

    # Import some minimal structure.
    run("svn import -m Initial_import /tmp/svn_initial_tree/ file://%s" \
        % repos_dir)
    # Adjust repository files permissions (will be managed by WebDAV).
    run("chown -R www-data:www-data %s" % repos_dir)
    run("find %s -type f -exec chmod 664 {} \;" % repos_dir)
    run("find %s -type d -exec chmod 775 {} \;" % repos_dir)
    # Cleanup.
    run("rm -r /tmp/svn_initial_tree/")



def apache(repository):
    """Configures Apache to serve a repository.

    repository:     name of the repository
    """

    conf_file = __get_apache_conf_file(repository)
    upload_template('apache_conf_svn.tmpl', conf_file, { 'repository': repository })
    run("chmod 644 %s" % conf_file)

    __apache_restart()



def users(repository):
    """List authorized users for a repository.

    repository:     name of the repository
    """
    run("grep 'Require user ' %s" % __get_apache_conf_file(repository))



def changeusers(repository, new_users):
    """Change 'Required users' on Apache configuration.

    repository:     name of the repository
    new_users:      list of users authorized (space-separated)

Restarts Apache to apply the new configuration.
    """

    conf_file = __get_apache_conf_file(repository)
    before = 'Require user .*$'
    after  = 'Require user %s' % new_users
    sed(conf_file, before, after, backup='')
    __apache_restart()

