#!/bin/bash

current_dir=$(dirname "$0")
vm_name=$1


php ${current_dir}/parse_vm_list_xen.php $vm_name
