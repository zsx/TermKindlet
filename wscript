#! /usr/bin/env python
# encoding: utf-8

VERSION = '0.3'
APPNAME = 'KindleTerm'

top = '.'
out = 'build'

from waflib.TaskGen import feature, extension
from waflib import TaskGen, Task, Utils, Options, Build, Errors, Node
import os
import re

class SignTask(Task.Task):
    after = 'jar_create'
    run_str='${JARSIGNER} ${OPTS} ${TGT} ${ALIAS}'

@feature('sign')
def sign(self):
    self.sign_task = tsk = self.create_task('SignTask')
    tsk.env['ALIAS'] = getattr(self, 'alias', None)
    tsk.env['OPTS'] = getattr(self, 'opts', None)
    target = getattr(self, 'target', None)
    if not isinstance(target, Node.Node):
            target = self.path.find_or_declare(target)
    if not target:
            self.bld.fatal('invalid target %r for %r' % (target, self))
    tsk.set_outputs(target)
    if getattr(self, 'jar_task', None):
        tsk.set_run_after(self.jar_task)

def configure(conf):
    conf.check_tool('java')
    conf.env.CLASSPATH_KINDLET = ['../../lib/kindlet-1.1.jar', '../../lib/KindletImplementation-1.1.jar', '../../lib/log4j-1.2.15.jar']
    conf.find_program('jarsigner', var='JARSIGNER')
    #conf.check_java_class('java.io.FileOutputStream')
    #conf.check_java_class('FakeClass')

def build(bld):

    bld(source='src/test/TerminalArea.pjava',
        defines=['DESKTOP'])
    # in the following, the feature 'seq' is used to force a sequential order on the tasks created
    # java
    #
    # srcdir: directory containing the sources to compile
    # compat: java compatibility version number (compiling with a too recent jdk may cause problems)
    bld(features='javac jar', 
            srcdir='src', 
            outdir='src',
            compat='1.4', 
            sourcepath=['src'], 
            use='KINDLET',
            destfile='KindleTerm.azw2',
            basedir='src',
            jarcreate='cfm',
            jaropts=['../manifest.mf'])
    for a in ('dkTest', 'diTest', 'dnTest'): 
        bld(features='sign',
            target='KindleTerm.azw2',
            opts = ['-keystore', '../../developer.keystore',
                    '-storepass', 'password'],
            alias = a)
        bld.add_group()
    # jar
    #
    # basedir: directory containing the .class files to package
    # destfile: the destination file
        #bld(features='jar seq',  destfile='playtxt.azw2', jarcreate='cfm', jaropts=['../manifest'])

    #jaropts = '-C default/src/ .', # can be used to give files
    #classpath = '..:.', # can be used to set a custom classpath
    #)
class PreprocessTask(Task.Task):
    def run(self):
        tgts = []
        for i in self.inputs:
            PREPROC = re.compile(r'^\s*#\s*(\w+)')
            PREPROC_IFDEF = re.compile(r'^\s*#\s*ifdef\s+(\w+)\s*$')
            PREPROC_ELSE = re.compile(r'^\s*#\s*else\s*$')
            PREPROC_ENDIF = re.compile(r'^\s*#\s*endif\s*$')
            skip = False
            depth = 0
            with open(i.abspath(), 'r') as f:
                dest = i.change_ext('.java')
                with open(dest.abspath(), 'w') as t:
                    for line in f:
                        #print "examing line: ", line
                        if PREPROC.search(line):
                            #print "found prep line: ", line
                            mo = PREPROC_IFDEF.search(line)
                            if mo:
                                depth += 1
                                oldskip = skip
                                if mo.group(1) in self.defines:
                                    skip = False
                                else:
                                    skip = True
                                continue
                            mo = PREPROC_ELSE.search(line)
                            if mo:
                                skip = not skip
                                continue
                            mo = PREPROC_ENDIF.search(line)
                            if mo:
                                depth -= 1
                                skip = oldskip
                                continue
                        if not skip:
                            t.write(line)
                    else:
                        if depth != 0:
                            raise Exception("Unmatched #if #endif blocks\n")
                tgts.append(dest)
        self.set_outputs(tgts)


@extension('.pjava')
def preprocess(self, n):
    self.preproc_task = tsk = self.create_task('PreprocessTask', n)
    tsk.defines = getattr(self, 'defines', None)
    if getattr(self, 'javac_task', None):
        tsk.set_run_before(self.javac_task)
