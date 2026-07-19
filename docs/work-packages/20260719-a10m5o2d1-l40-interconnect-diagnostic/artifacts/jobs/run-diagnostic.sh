#!/bin/sh
set -eu
umask 077

job_local=${1:?job-local root required}
output=${2:?output required}
run_root=$PWD
runtime_root=$job_local/runtime/cpython
environment=$job_local/runtime/environment

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1 PIP_NO_INDEX=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
export PATH=/usr/bin:/bin CC=/usr/bin/gcc CXX=/usr/bin/g++
export NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET,P2P
export TORCH_NCCL_ASYNC_ERROR_HANDLING=1
mkdir -p -- "$runtime_root" "$environment" "$job_local/wheels" "$output"
tar -xzf "$run_root/runtime.tar.gz" --strip-components=1 -C "$runtime_root"
test "$("$runtime_root/bin/python3" --version 2>&1)" = "Python 3.11.15"
"$runtime_root/bin/python3" -m venv --copies "$environment"
tar -xf "$run_root/wheelhouse.tar" -C "$job_local/wheels"
"$environment/bin/python" -m pip install --disable-pip-version-check --no-index \
  --require-hashes --find-links "$job_local/wheels/wheelhouse" \
  -r "$run_root/requirements.lock" >"$job_local/pip-install.log" 2>&1
"$environment/bin/python" -m pip check >"$job_local/pip-check.log" 2>&1

nvidia-smi --query-gpu=index,uuid,pci.bus_id,name --format=csv,noheader >"$output/gpu-inventory.csv"
nvidia-smi topo -m >"$output/topology.txt"
set +e
nvidia-smi topo -p2p r >"$output/p2p-read.txt" 2>&1
read_status=$?
nvidia-smi topo -p2p w >"$output/p2p-write.txt" 2>&1
write_status=$?
set -e
printf '%s\n' "$read_status" >"$output/p2p-read.status"
printf '%s\n' "$write_status" >"$output/p2p-write.status"

base_visible=${CUDA_VISIBLE_DEVICES:-}
test "$(printf '%s' "$base_visible" | awk -F, '{print NF}')" -eq 4
for pair in 0,1 0,2 0,3 1,2 1,3 2,3; do
  label=$(printf '%s' "$pair" | tr -d ',')
  printf 'BEGIN pair-%s-default\n' "$label"
  CUDA_VISIBLE_DEVICES=$pair "$environment/bin/torchrun" --standalone --nnodes=1 \
    --nproc-per-node=2 "$run_root/interconnect.py" --expected-world 2 \
    --label "pair-$label-default" --output "$output"
  printf 'BEGIN pair-%s-p2p-disabled\n' "$label"
  CUDA_VISIBLE_DEVICES=$pair NCCL_P2P_DISABLE=1 \
    "$environment/bin/torchrun" --standalone --nnodes=1 --nproc-per-node=2 \
    "$run_root/interconnect.py" --expected-world 2 \
    --label "pair-$label-p2p-disabled" --output "$output"
done

printf 'BEGIN quad-default\n'
CUDA_VISIBLE_DEVICES=$base_visible "$environment/bin/torchrun" --standalone \
  --nnodes=1 --nproc-per-node=4 "$run_root/interconnect.py" --expected-world 4 \
  --label quad-default --output "$output"
printf 'BEGIN quad-p2p-disabled\n'
CUDA_VISIBLE_DEVICES=$base_visible NCCL_P2P_DISABLE=1 \
  "$environment/bin/torchrun" --standalone --nnodes=1 --nproc-per-node=4 \
  "$run_root/interconnect.py" --expected-world 4 \
  --label quad-p2p-disabled --output "$output"

"$environment/bin/python" "$run_root/merge_results.py" --input "$output" \
  --output "$output/evidence.json.part"
