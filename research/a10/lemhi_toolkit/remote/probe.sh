#!/bin/sh
set -eu
arch=$(uname -m)
glibc=$(getconf GNU_LIBC_VERSION | awk '{print $2}')
printf '{"architecture":"%s","glibc":"%s","observation_method":"posix-login-probe","platform":"linux-x86_64-glibc","scheduler":"slurm","scope":"login","unavailable":[],"untested":["compute","cuda"]}\n' "$arch" "$glibc"
