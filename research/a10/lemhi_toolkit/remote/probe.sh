#!/bin/sh
set -eu
os=$(uname -s)
arch=$(uname -m)
printf '{"observation_method":"posix-login-probe","platform":"%s-%s","scheduler":"slurm","scope":"login","unavailable":[],"untested":["compute","cuda"]}\n' "$os" "$arch"
