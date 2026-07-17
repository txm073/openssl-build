#!/usr/bin/env python3
import os
import re
import subprocess as sp
from pathlib import Path
import argparse
import sys


def build(target):
  opts = [
    'no-apps',
    'no-docs',
    'no-tests',
    'no-shared',
    'no-module',
    'no-engine',
    'no-dso',
    'no-ui-console',
    'no-legacy',
    'no-deprecated',
    'no-ssl3',
    'no-tls1',
    'no-tls1_1',
    'no-comp',
    'no-async',
    'no-filenames',
    'no-stdio'
  ]
  prefix = os.path.abspath(f'build/{target}')
  env = os.environ.copy()
  if target in android_targets:
    env['ANDROID_NDK'] = '/opt/android-ndk'
    bin_dir = env['ANDROID_NDK'] + '/toolchains/llvm/prebuilt/linux-x86_64/bin'
    env['PATH'] = bin_dir + ':' + os.getenv('PATH')
    target_prefixes = (
      'armv7a-linux-androideabi', 'aarch64-linux-android',
      'x86_64-linux-android', 'i686-linux-android'
    )
  procs = str(os.cpu_count() or 1)
  win = target in windows_targets
  if win:
    sp.run(['nmake', 'clean'], cwd='source', env=env)
    sp.run(
      [
        'perl', 'Configure', target,
        *opts, f'--prefix={prefix}',
        '--release'
      ],
      cwd='source', env=env
    )
    makefile = Path("source/Makefile")
    text = makefile.read_text()
    text = text.replace('/Zi', '')
    text = re.sub(r'\s+/Z[7iI]', '', text)       # /Zi /Z7 /ZI
    text = re.sub(r'\s+/Fd[^\s]+', '', text)     # /Fdwhatever
    text = re.sub(
        r'^[ \t]*@if "\$\(SHLIBS\)"=="" \\\\
    [ \t]*"\$\(PERL\)" "\$\(SRCDIR\)\\\\util\\\\copy\.pl" [^\r\n]*\.pdb "\$\(libdir\)"\s*
    ',
        '',
        text,
        flags=re.MULTILINE,
    )
    makefile.write_text(text)
    sp.run(['nmake'], cwd='source', env=env)
    sp.run(['nmake', 'install'], cwd='source', env=env)
  else:
    sp.run(['make', 'clean'], cwd='source')
    sp.run(
      [
        './Configure', target,
        *opts, f'--prefix={prefix}'
      ],
      cwd='source', env=env
    )
    sp.run(
      ['make', '-j', procs],
      cwd='source', env=env, shell=True
    )
    sp.run(
      ['make', 'install_sw'],
      cwd='source', env=env
    )

version = '3.6'
# if not os.path.exists('source'):
#   sp.run(['git', 'clone', 'https://github.com/openssl/openssl', 'source'])
sp.run(['git', 'checkout', f'openssl-{version}'], cwd='source')

android_targets = (
  'android-arm', 'android-arm64', 'android-x86', 'android-x86_64'
)
linux_targets = ('linux-x86', 'linux-x86_64')
macos_targets = ('darwin64-x86_64', 'darwin64-arm64')
windows_targets = ('VC-WIN32', 'VC-WIN64A')

if sys.platform == 'linux':
  platform_targets = linux_targets + android_targets
elif sys.platform == 'win32':
  platform_targets = windows_targets
elif sys.platform == 'darwin':
  platform_targets = macos_targets
else:
  print('invalid host platform')
  exit(1)

parser = argparse.ArgumentParser('openssl-build')
parser.add_argument('target')
args, _ = parser.parse_known_args()
if args.target == 'all':
  for target in platform_targets:
    build(target)
else:
  targets = android_targets + linux_targets + macos_targets + windows_targets
  if args.target not in targets:
    print(f'target {args.target!r} not found')
    exit(1)
  build(args.target)
