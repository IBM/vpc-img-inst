from typing import Any, Dict
from vpc_img_inst.config_builder import ConfigBuilder, spinner
from vpc_img_inst.utils import find_default,get_option_from_list,get_region_by_endpoint, CACHE, logger, append_random_suffix, store_output, color_msg, Color

class VPCConfig(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.base_config = base_config

        self.sg_rules = {'outbound_tcp_all': 'selected security group is missing rule permitting outbound TCP access\n',
                        'inbound_tcp_22': 'selected security group is missing rule permitting inbound traffic to tcp port 22 required for ssh\n',}  # security group rules.
        self.vpc_name = 'temp-vpc'
        
    def _get_region(self):
        region = None
        try:
            region = get_region_by_endpoint(self.ibm_vpc_client.service_url)
        except Exception:
            region = ConfigBuilder.region
        return region

    def run(self) -> Dict[str, Any]:
        region = self._get_region()

        vpc_obj, zone_obj = self._select_vpc(self.base_config, region)

        if not vpc_obj:
            raise Exception(f'Failed to select VPC')

        all_subnet_objects = self.ibm_vpc_client.list_subnets().get_result()[
            'subnets']

        # filter only subnets from selected availability zone
        subnet_objects = [s_obj for s_obj in all_subnet_objects if s_obj['zone']
                          ['name'] == zone_obj['name'] and s_obj['vpc']['id'] == vpc_obj['id']]

        if not subnet_objects:
            raise f'Failed to find subnet for vpc {vpc_obj["name"]} in zone {zone_obj["name"]}'
        
        self.base_config['node_config'].update({'vpc_id':vpc_obj['id'],
                                                'resource_group_id':CACHE['resource_group_id'],
                                                'security_group_id':vpc_obj['default_security_group']['id'],
                                                'subnet_id':subnet_objects[0]['id']})

        self.base_config['zone_name'] = zone_obj['name']                                                
        return self.base_config

    def _build_security_group_rule_prototype_model(self, missing_rule, sg_id=None):
        direction, protocol, port = missing_rule.split('_')
        remote = {"cidr_block": "0.0.0.0/0"}

        try: # port number was specified
            port = int(port)
            port_min = port
            port_max = port
        except:
            port_min = 1
            port_max = 65535

            # only valid if security group already exists
            if port == 'sg':
                if not sg_id:
                    return None
                remote = {'id': sg_id}

        return {
            'direction': direction,
            'ip_version': 'ipv4',
            'protocol': protocol,
            'remote': remote,
            'port_min': port_min,
            'port_max': port_max
        }

    def _create_vpc_peripherals(self, ibm_vpc_client, vpc_obj, zone_obj, resource_group):
        vpc_name = vpc_obj['name']
        vpc_id = vpc_obj['id']
        # create subnet
        subnet_name = '{}-subnet'.format(vpc_name)
        subnet_data = None

        # find cidr
        ipv4_cidr_block = None
        res = ibm_vpc_client.list_vpc_address_prefixes(
            vpc_id).result
        address_prefixes = res['address_prefixes']

        # searching for the CIDR block (internal ip range) matching the specified zone of a VPC (whose region has already been set) 
        for address_prefix in address_prefixes:
            if address_prefix['zone']['name'] == zone_obj['name']:
                ipv4_cidr_block = address_prefix['cidr']
                break

        subnet_prototype = {}
        subnet_prototype['zone'] = {'name': zone_obj['name']}
        subnet_prototype['ip_version'] = 'ipv4'
        subnet_prototype['name'] = subnet_name
        subnet_prototype['resource_group'] = resource_group
        subnet_prototype['vpc'] = {'id': vpc_id}
        subnet_prototype['ipv4_cidr_block'] = ipv4_cidr_block

        subnet_data = ibm_vpc_client.create_subnet(
            subnet_prototype).result
        subnet_id = subnet_data['id']
        store_output({"subnet_id":subnet_id},self.base_config)
        logger.info(color_msg(f"Created subnet: {subnet_prototype['name']} with id: {subnet_id}",color=Color.LIGHTGREEN))

        # Update security group to have all required rules
        sg_id = vpc_obj['default_security_group']['id']

        # update sg name
        sg_name = '{}-sg'.format(vpc_name)
        ibm_vpc_client.update_security_group(
            sg_id, security_group_patch={'name': sg_name})

        # add all other required rules configured by the specific backend
        for rule in self.sg_rules.keys():
            sg_rule_prototype = self._build_security_group_rule_prototype_model(
                rule)
            if sg_rule_prototype:
                res = ibm_vpc_client.create_security_group_rule(
                    sg_id, sg_rule_prototype).get_result()
        logger.info(f"Security group {sg_name} been updated with required rules")

    def _select_resource_group(self, auto=False):
        # find resource group

        @spinner
        def get_res_group_objects():
            return self.resource_service_client.list_resource_groups().get_result()['resources']

        res_group_objects = get_res_group_objects()
        if auto:
            return res_group_objects[0]['id']

        default = find_default(
            self.defaults, res_group_objects, id='resource_group_id')
        res_group_obj = get_option_from_list(
            "Select resource group", res_group_objects, default=default)
        return res_group_obj['id']

    def _select_zone(self, vpc_id, region, auto=False):
        # find availability zone
        @spinner
        def get_zones_and_subnets():
            zones_objects = self.ibm_vpc_client.list_region_zones(region).get_result()['zones']
            all_subnet_objects = self.ibm_vpc_client.list_subnets().get_result()['subnets']
            return zones_objects, all_subnet_objects

        zones_objects, all_subnet_objects = get_zones_and_subnets()
        
        if auto:
            return zones_objects[0]

        if vpc_id:
            # filter out zones that given vpc has no subnets in
            zones = [s_obj['zone']['name']
                        for s_obj in all_subnet_objects if s_obj['vpc']['id'] == vpc_id]
            zones_objects = [
                z for z in zones_objects if z['name'] in zones]
        logger.info(f"Zone chosen: {zones_objects[0]['name']}")
        return zones_objects[0] # returning a random zone the vpc has a subnet in.

    def _select_vpc(self, node_config, region):

        vpc_id, vpc_name, zone_obj, sg_id, resource_group = None, None, None, None, None
        ibm_vpc_client = self.ibm_vpc_client
       
        while True:

            @spinner
            def list_vpcs():
                return ibm_vpc_client.list_vpcs().get_result()['vpcs']
            @spinner
            def _create_vpc(vpc_name):
                return ibm_vpc_client.create_vpc(address_prefix_management='auto', classic_access=False,
                                                name=vpc_name, resource_group=resource_group).get_result()
                                                
            vpc_objects = list_vpcs()
            zone_obj = self._select_zone(vpc_id, region)
 
            resource_group_id = self._select_resource_group()
            resource_group = {'id': resource_group_id}

            # Create a unique VPC name
            vpc_name = append_random_suffix(base_name=self.vpc_name)
            vpc_obj = _create_vpc(vpc_name)
            vpc_id = vpc_obj['id']
            store_output({'vpc_id':vpc_id},self.base_config)

            logger.info(color_msg(f"Created VPC: {vpc_name} with id: {vpc_id}",color=Color.LIGHTGREEN))

            self._create_vpc_peripherals(ibm_vpc_client, vpc_obj, zone_obj, resource_group)
            break

        CACHE['resource_group_id'] = resource_group['id']
        
        return vpc_obj, zone_obj

    
