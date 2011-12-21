# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, sys, shlex

from git_command import GitCommand
from command import Command
from sync import Sync

class Flow(Command):
  common = True
  helpSummary = "Passes a git flow command along to multiple repos (only if everything is on the same branch)"
  helpUsage = """
%prog [<project>...] -c "command"
"""
  def _Options(self, p):
    def cmd(option, opt_str, value, parser):
      setattr(parser.values, option.dest, list(parser.rargs))
      while parser.rargs:
        del parser.rargs[0]
    p.add_option('-c', '--command',
                 help='Git flow command to execute (e.g. "init", "feature start", etc.)',
                 dest='command',
                 action='callback',
                 callback=cmd)

  def Execute(self, opt, args):
    current_branches = set()
    for project in self.GetProjects(args):
      status = project.work_git.status()
      firstline = status.split('\n')[0]

      #check if repo is on a branch, and add it to current branches
      if "On branch" not in firstline:
        print >>sys.stderr, "error: '%s' is not on a branch" % project.name
        sys.exit(1)
      current_branches.add(firstline.split("On branch")[1].strip())

      #check if working directory is clean
      if "nothing to commit" not in status:
        print >>sys.stderr, "error: '%s' has uncommitted changes, run 'repo status' for more info" % project.name
        sys.exit(1)

    #make sure everything is on the same branch
    if len(current_branches) != 1:
      print >>sys.stderr, "error: not all repos are on the same branch, run 'repo branches' for more info"
      sys.exit(1)

    flow_command = ["flow"]
    flow_command.extend(shlex.split(" ".join(opt.command)))
    for project in self.GetProjects(args):
      print >>sys.stdout, "%s:" % project.name
      if GitCommand(project, flow_command).Wait() != 0:
        print >>sys.stdout, "error: git flow command failed for '%s'" % project.name
        sys.exit(1)
