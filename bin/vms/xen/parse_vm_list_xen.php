<?php
// this script returns a JSON array of VMs with the format:
//   {  
//      "VCPUs-number":"1",
//      "uuid":"3848cce7-ad9c-4342-04a5-7c48a99b99fb",
//      "name-label":"astronomia",
//      "name-description": "not supported in Xen",
//      "power-state": "running",
//      "memory-actual_mb":"2048",
//      "ports":[  
//         {  
//            "name":"vif0"
//            "mac":"aa:cc:00:00:00:64",
//            "ips": ["194.116.73.192"],
//         },
//         {  
//            "name":"vif1"
//            "ips": ["194.116.124.181"],
//         }
//      ]
//   }

	$vm_name="";
	$command="";
	
	if (isset($argv[1])) {
	    $vm_name=$argv[1];
	}
	if (isset($argv[2])) {
		$command=$argv[2];
	}
	
		
	// get list of VMs with details
    $stream=array();
	exec("xm list -l " . $vm_name, &$stream);

	$parenthesisbalance_domain=0;
	$parenthesisbalance_vif=0;
	$parenthesisbalance_vbd=0;
	$vms=array();
	$domain=array();
	$port=array();
	$port_counter=0;
	$blockdevice="";
	$inside_vif=false;
	$inside_vbd=false;

	
	foreach($stream as $i => $line) {
		if ($line != "") {
			// dati OK, processa la linea
			$parenthesisbalance_domain+=substr_count($line, "(") - substr_count($line, ")");
			$trimmedline=trim($line, " \t\n\r()");
			$trimmedline_arr=explode(" ",$trimmedline);
		
			if ($inside_vif) {
				if ($parenthesisbalance_domain == $parenthesisbalance_vif) {
					// finita una porta (vif)
					$port["name"]="vif".$port_counter;
				
					if (!array_key_exists("ports", $domain)) {
						$domain["ports"]=array();
					}
					$domain["ports"][]=$port;
				
					$port=array();
					$port_counter++;
					$inside_vif=false;
				} else {
					if ($trimmedline_arr[0] == "ip") {
						$port["ips"]=array($trimmedline_arr[1]);
					}
					if ($trimmedline_arr[0] == "mac") {
						$port["mac"]=$trimmedline_arr[1];
					}
				}
			}

			if ($inside_vbd) {
				if ($parenthesisbalance_domain == $parenthesisbalance_vbd) {
					// finito un block device (vbd)
					if (!array_key_exists("blockdevices", $domain)) {
						//$domain["blockdevices"]=$blockdevice;
					} else {
						//$domain["blockdevices"].=";".$blockdevice;
					}
					$inside_vbd=false;
				} else {
					if ($trimmedline_arr[0] == "uname") {
						$blockdevice=$trimmedline_arr[1];
					}
				}
			}
			
			if ($trimmedline_arr[0] == "uuid") {
				$domain["uuid"]=$trimmedline_arr[1];
			}
			if ($trimmedline_arr[0] == "name") {
				$domain["name-label"]=$trimmedline_arr[1];
			}
			if ($trimmedline_arr[0] == "vcpus") {
				$domain["VCPUs-number"]=$trimmedline_arr[1];
			}
			if ($trimmedline_arr[0] == "memory") {
				$domain["memory-actual_mb"]=$trimmedline_arr[1];
			}
			if ($trimmedline_arr[0] == "vif") {
				$parenthesisbalance_vif=$parenthesisbalance_domain - 1;
				$inside_vif=true;
			}
			if ($trimmedline_arr[0] == "vbd") {
				$parenthesisbalance_vbd=$parenthesisbalance_domain - 1;
				$inside_vbd=true;
			}
			
			// compatibilita' con XenServer
			$domain["name-description"]="";
			$domain["power-state"]="running";
			
			// controlla se e' finito un dominio
			if ($parenthesisbalance_domain == 0) {
				$port=array();
				$port_counter=0;
			
				// salta Domain-0
				if ($domain["name-label"] != "Domain-0") {
					$vms[]=$domain;
				}
				
				$domain=array();
			}
		}
	}
	
	$data=array();
	if ($vm_name == "") {
		// generate discovery list of VMs (only name and uuid)
		foreach($vms as $vm) {
			$vm_entry=array();
			$vm_entry['{#VMNAME}']=$vm["name-label"];
			$vm_entry['{#VMUUID}']=$vm["uuid"];
			
			$data[]=$vm_entry;
		}
	} else {
		// return details of selected VM only
		if (count($vms) > 0) {
			$vm=$vms[0];
		} else {
			// create dummy VM for disappearing VM
			$vm=array("VCPUs-number" => "0", "uuid" => "deleted", "name-label" => $vm_name, "name-description" => "", "power-state" => "deleted", "memory-actual_mb" => "0", "ports" => array() );
		}
		/*
		$vm_entry=array();
		$vm_entry['{#VMNAME}']=$vm["name-label"];
		$vm_entry['{#VMSTATE}']=$vm["power-state"];
		$vm_entry['{#VMCPUS}']=$vm["VCPUs-number"];
		$vm_entry['{#VMUUID}']=$vm["uuid"];
		$vm_entry['{#VMDESC}']=$vm["name-description"];
		$vm_entry['{#VMMEM}']=$vm["memory-actual_mb"];
		$vm_entry['{#VMPORTS}']=$vm["ports"];
		*/
		
		if ($command == "state") {
			$data=$vm["power-state"];
		} else {
			$data=json_encode($vm);
		}
		
		
		
	}
	
	
	print(json_encode(array("data" => $data)));
?>
