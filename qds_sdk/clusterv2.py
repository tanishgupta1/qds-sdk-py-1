from qds_sdk.qubole import Qubole
from qds_sdk.resource import Resource
from qds_sdk.cloud.cloud import Cloud
from qds_sdk.engine import Engine
from qds_sdk import util
import argparse

import sys
import json

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

class ClusterCmdLine:

    @staticmethod
    def parsers(args):
        action = args[0]
        argparser = argparse.ArgumentParser(
            prog="qds.py cluster",
            description="Cluster Operations for Qubole Data Service.")
        subparsers = argparser.add_subparsers(title="Cluster operations")

        create = subparsers.add_parser("create", help="Create a new cluster")
        if action == "create":
            ClusterCmdLine.create_update_clone_parser(create, action="create")
            create.set_defaults(func=ClusterV2.create)

        update = subparsers.add_parser("update", help="Update the settings of an existing cluster")
        if action == "update":
            ClusterCmdLine.create_update_clone_parser(update, action="update")
            create.set_defaults(func=ClusterV2.update)

        clone = subparsers.add_parser("clone", help="Clone a cluster from an existing one")
        if action == "clone":
            ClusterCmdLine.create_update_clone_parser(clone, action="clone")
            create.set_defaults(func=ClusterV2.clone)

        return argparser


    @staticmethod
    def create_update_clone_parser(subparser, action=None):

        # cloud config parser
        Cloud.get_cloud_object().cloud_config_parser(subparser)

        # cluster info parser
        ClusterInfoV2.cluster_info_parser(subparser, action)

        # engine config parser
        Engine().engine_parser(subparser)


    @staticmethod
    def run(args):
        parser = ClusterCmdLine.parsers(args)
        arguments = parser.parse_args(args)

        customer_ssh_key = util._read_file(arguments.customer_ssh_key_file, "customer ssh key file")

        # This will set cluster info and monitoring settings
        cluster_info = ClusterInfoV2(arguments.label)
        cluster_info.set_cluster_info(disallow_cluster_termination=arguments.disallow_cluster_termination,
                                      enable_ganglia_monitoring=arguments.enable_ganglia_monitoring,
                                      datadog_api_token=arguments.datadog_api_token,
                                      datadog_app_token=arguments.datadog_app_token,
                                      node_bootstrap=arguments.node_bootstrap_file,
                                      master_instance_type=arguments.master_instance_type,
                                      slave_instance_type=arguments.slave_instance_type,
                                      min_nodes=arguments.initial_nodes,
                                      max_nodes=arguments.max_nodes,
                                      slave_request_type=arguments.slave_request_type,
                                      fallback_to_ondemand=arguments.fallback_to_ondemand,
                                      custom_tags=arguments.custom_tags,
                                      heterogeneous_config=arguments.heterogeneous_config,
                                      maximum_bid_price_percentage=arguments.maximum_bid_price_percentage,
                                      timeout_for_request=arguments.timeout_for_request,
                                      maximum_spot_instance_percentage=arguments.maximum_spot_instance_percentage,
                                      stable_maximum_bid_price_percentage=arguments.stable_maximum_bid_price_percentage,
                                      stable_timeout_for_request=arguments.stable_timeout_for_request,
                                      stable_spot_fallback=arguments.stable_spot_fallback,
                                      idle_cluster_timeout=arguments.idle_cluster_timeout,
                                      disk_count=arguments.count,
                                      disk_type=arguments.disk_type,
                                      disk_size=arguments.size,
                                      upscaling_config=arguments.upscaling_config,
                                      enable_encryption=arguments.encrypted_ephemerals,
                                      customer_ssh_key=customer_ssh_key)

        #  This will set cloud config settings
        cloud_config = Cloud.get_cloud_object()
        cloud_config.set_cloud_config_settings(arguments)

        # This will set engine settings
        engine_config = Engine(flavour=arguments.flavour)
        engine_config.set_engine_config_settings(arguments)

        cluster_request = ClusterCmdLine.get_cluster_request_parameters(cluster_info, cloud_config, engine_config)
        return arguments.func(cluster_request)

    @staticmethod
    def get_cluster_request_parameters(cluster_info, cloud_config, engine_config):
        cluster_request = {}
        cluster_request['cloud_config'] = util._make_minimal(cloud_config.__dict__)
        cluster_request['engine_config'] = util._make_minimal(engine_config.__dict__)
        cluster_request.update(util._make_minimal(cluster_info.__dict__))
        return cluster_request


class ClusterInfoV2(object):

    def __init__(self, label):
        self.cluster_info = {}
        self.cluster_info['label'] = label
        self.monitoring = {}
        self.internal = {} # right now not supported

    @staticmethod
    def cluster_info_parser(argparser, action):

        create_required = False
        label_required = False
        if action == "create":
            create_required = True
        elif action == "update":
            argparser.add_argument("cluster_id_label",
                                   help="id/label of the cluster to update")
        elif action == "clone":
            argparser.add_argument("cluster_id_label",
                                   help="id/label of the cluster to update")
            label_required = True

        argparser.add_argument("--label", dest="label",
                               nargs="+", required=(create_required or label_required),
                               help="list of labels for the cluster" +
                                    " (atleast one label is required)")
        cluster_info = argparser.add_argument_group("cluster_info")
        cluster_info.add_argument("--master-instance-type",
                                  dest="master_instance_type",
                                  help="instance type to use for the hadoop" +
                                       " master node")
        cluster_info.add_argument("--slave-instance-type",
                                  dest="slave_instance_type",
                                  help="instance type to use for the hadoop" +
                                       " slave nodes")
        cluster_info.add_argument("--min-nodes",
                                  dest="initial_nodes",
                                  type=int,
                                  help="number of nodes to start the" +
                                       " cluster with", )
        cluster_info.add_argument("--max-nodes",
                                  dest="max_nodes",
                                  type=int,
                                  help="maximum number of nodes the cluster" +
                                       " may be auto-scaled up to")
        cluster_info.add_argument("--idle-cluster-timeout",
                                  dest="idle_cluster_timeout",
                                  help="cluster termination timeout for idle cluster")
        cluster_info.add_argument("--node-bootstrap-file",
                                  dest="node_bootstrap_file",
                                  help="""name of the node bootstrap file for this cluster. It
                                   should be in stored in S3 at
                                   <account-default-location>/scripts/hadoop/NODE_BOOTSTRAP_FILE
                                   """, )
        termination = cluster_info.add_mutually_exclusive_group()
        termination.add_argument("--disallow-cluster-termination",
                                 dest="disallow_cluster_termination",
                                 action="store_true",
                                 default=None,
                                 help="don't auto-terminate idle clusters," +
                                      " use this with extreme caution", )
        termination.add_argument("--allow-cluster-termination",
                                 dest="disallow_cluster_termination",
                                 action="store_false",
                                 default=None,
                                 help="auto-terminate idle clusters,")
        fallback_to_ondemand_group = cluster_info.add_mutually_exclusive_group()
        fallback_to_ondemand_group.add_argument("--fallback-to-ondemand",
                                                dest="fallback_to_ondemand",
                                                action="store_true",
                                                default=None,
                                                help="Fallback to on-demand nodes if spot nodes" +
                                                     " could not be obtained. Valid only if slave_request_type is spot", )
        fallback_to_ondemand_group.add_argument("--no-fallback-to-ondemand",
                                                dest="fallback_to_ondemand",
                                                action="store_false",
                                                default=None,
                                                help="Dont Fallback to on-demand nodes if spot nodes" +
                                                     " could not be obtained. Valid only if slave_request_type is spot", )
        cluster_info.add_argument("--customer-ssh-key",
                                  dest="customer_ssh_key_file",
                                  help="location for ssh key to use to" +
                                       " login to the instance")
        cluster_info.add_argument("--custom-tags",
                                  dest="custom_tags",
                                  help="""Custom tags to be set on all instances
                                                 of the cluster. Specified as JSON object (key-value pairs)
                                                 e.g. --custom-ec2-tags '{"key1":"value1", "key2":"value2"}'
                                                 """, )

        # datadisk settings
        datadisk_group = argparser.add_argument_group("data disk settings")
        datadisk_group.add_argument("--count",
                                    dest="count",
                                    type=int,
                                    help="Number of EBS volumes to attach to" +
                                         " each instance of the cluster", )
        datadisk_group.add_argument("--disk-type",
                                    dest="disk_type",
                                    choices=["standard", "gp2"],
                                    help="Type of the  volume attached to the instances. Valid values are " +
                                         "'standard' (magnetic) and 'gp2' (ssd).")
        datadisk_group.add_argument("--size",
                                    dest="size",
                                    type=int,
                                    help="Size of each EBS volume, in GB", )
        datadisk_group.add_argument("--upscaling-config",
                                    dest="upscaling_config",
                                    help="Upscaling config to be attached with the instances.", )
        ephemerals = datadisk_group.add_mutually_exclusive_group()
        ephemerals.add_argument("--encrypted-ephemerals",
                                dest="encrypted_ephemerals",
                                action="store_true",
                                default=None,
                                help="encrypt the ephemeral drives on" +
                                     " the instance", )
        ephemerals.add_argument("--no-encrypted-ephemerals",
                                dest="encrypted_ephemerals",
                                action="store_false",
                                default=None,
                                help="don't encrypt the ephemeral drives on" +
                                     " the instance", )

        cluster_info.add_argument("--heterogeneous-config",
                                  dest="heterogeneous_config",
                                  help="heterogeneous config for the cluster")

        cluster_info.add_argument("--slave-request-type",
                                  dest="slave_request_type",
                                  choices=["ondemand", "spot", "hybrid"],
                                  help="purchasing option for slave instaces", )

        # spot settings
        spot_instance_group = argparser.add_argument_group("spot instance settings" +
                                                           " (valid only when slave-request-type is hybrid or spot)")
        spot_instance_group.add_argument("--maximum-bid-price-percentage",
                                         dest="maximum_bid_price_percentage",
                                         type=float,
                                         help="maximum value to bid for spot instances" +
                                              " expressed as a percentage of the base" +
                                              " price for the slave node instance type", )
        spot_instance_group.add_argument("--timeout-for-spot-request",
                                         dest="timeout_for_request",
                                         type=int,
                                         help="timeout for a spot instance request" +
                                              " unit: minutes")
        spot_instance_group.add_argument("--maximum-spot-instance-percentage",
                                         dest="maximum_spot_instance_percentage",
                                         type=int,
                                         help="maximum percentage of instances that may" +
                                              " be purchased from the aws spot market," +
                                              " valid only when slave-request-type" +
                                              " is 'hybrid'", )

        stable_spot_group = argparser.add_argument_group("stable spot instance settings")
        stable_spot_group.add_argument("--stable-maximum-bid-price-percentage",
                                       dest="stable_maximum_bid_price_percentage",
                                       type=float,
                                       help="maximum value to bid for stable node spot instances" +
                                            " expressed as a percentage of the base" +
                                            " price for the master and slave node instance types", )
        stable_spot_group.add_argument("--stable-timeout-for-spot-request",
                                       dest="stable_timeout_for_request",
                                       type=int,
                                       help="timeout for a stable node spot instance request" +
                                            " unit: minutes")
        stable_spot_group.add_argument("--stable-allow-fallback",
                                       dest="stable_spot_fallback", default=None,
                                       type=str2bool,
                                       help="whether to fallback to on-demand instances for stable nodes" +
                                            " if spot instances aren't available")
        # monitoring settings
        monitoring_group = argparser.add_argument_group("monitoring settings")
        ganglia = monitoring_group.add_mutually_exclusive_group()
        ganglia.add_argument("--enable-ganglia-monitoring",
                             dest="enable_ganglia_monitoring",
                             action="store_true",
                             default=None,
                             help="enable ganglia monitoring for the" +
                                  " cluster", )
        ganglia.add_argument("--disable-ganglia-monitoring",
                             dest="enable_ganglia_monitoring",
                             action="store_false",
                             default=None,
                             help="disable ganglia monitoring for the" +
                                  " cluster", )

        datadog_group = argparser.add_argument_group("datadog settings")
        datadog_group.add_argument("--datadog-api-token",
                                   dest="datadog_api_token",
                                   default=None,
                                   help="fernet key for airflow cluster", )
        datadog_group.add_argument("--datadog-app-token",
                                   dest="datadog_app_token",
                                   default=None,
                                   help="overrides for airflow cluster", )

    def set_cluster_info(self,
                         disallow_cluster_termination=None,
                         enable_ganglia_monitoring=None,
                         datadog_api_token=None,
                         datadog_app_token=None,
                         node_bootstrap=None,
                         master_instance_type=None,
                         slave_instance_type=None,
                         min_nodes=None,
                         max_nodes=None,
                         slave_request_type=None,
                         fallback_to_ondemand=None,
                         custom_tags=None,
                         heterogeneous_config=None,
                         maximum_bid_price_percentage=None,
                         timeout_for_request=None,
                         maximum_spot_instance_percentage=None,
                         stable_maximum_bid_price_percentage=None,
                         stable_timeout_for_request=None,
                         stable_spot_fallback=None,
                         idle_cluster_timeout=None,
                         disk_count=None,
                         disk_type=None,
                         disk_size=None,
                         upscaling_config=None,
                         enable_encryption=None,
                         customer_ssh_key=None,
                         cluster_name=None,
                         force_tunnel=None):

        def set_monitoring():
            self.monitoring['ganglia'] = enable_ganglia_monitoring
            set_datadog_setting()

        def set_spot_instance_settings():
            self.cluster_info['spot_settings']['spot_instance_settings'] = {}
            self.cluster_info['spot_settings']['spot_instance_settings']['maximum_bid_price_percentage'] = \
                maximum_bid_price_percentage
            self.cluster_info['spot_settings']['spot_instance_settings']['timeout_for_request'] = timeout_for_request
            self.cluster_info['spot_settings']['spot_instance_settings']['maximum_spot_instance_percentage'] = \
                maximum_spot_instance_percentage

        def set_stable_spot_bid_settings():
            self.cluster_info['spot_settings']['stable_spot_bid_settings'] = {}
            self.cluster_info['spot_settings']['stable_spot_bid_settings']['maximum_bid_price_percentage'] = \
                stable_maximum_bid_price_percentage
            self.cluster_info['spot_settings']['stable_spot_bid_settings']['timeout_for_request'] = \
                stable_timeout_for_request
            self.cluster_info['spot_settings']['stable_spot_bid_settings']['stable_spot_fallback'] = \
                stable_spot_fallback

        def set_datadog_setting():
            self.monitoring['datadog'] = {}
            self.monitoring['datadog']['datadog_api_token'] = datadog_api_token
            self.monitoring['datadog']['datadog_app_token'] = datadog_app_token

        def set_data_disk():
            self.cluster_info['datadisk'] = {}
            self.cluster_info['datadisk']['size'] = disk_size
            self.cluster_info['datadisk']['count'] = disk_count
            self.cluster_info['datadisk']['type'] = disk_type
            self.cluster_info['datadisk']['upscaling_config'] = upscaling_config
            self.cluster_info['datadisk']['encryption'] = enable_encryption


        self.cluster_info['master_instance_type'] = master_instance_type
        self.cluster_info['slave_instance_type'] = slave_instance_type
        self.cluster_info['min_nodes'] = min_nodes
        self.cluster_info['max_nodes'] = max_nodes
        self.cluster_info['cluster_name'] = cluster_name
        self.cluster_info['node_bootstrap'] = node_bootstrap
        self.cluster_info['disallow_cluster_termination'] = disallow_cluster_termination
        self.cluster_info['force_tunnel'] = force_tunnel
        self.cluster_info['fallback_to_ondemand'] = fallback_to_ondemand
        self.cluster_info['customer_ssh_key'] = customer_ssh_key
        if custom_tags and custom_tags.strip():
            try:
                self.cluster_info['custom_tags'] = json.loads(custom_tags.strip())
            except Exception as e:
                raise Exception("Invalid JSON string for custom ec2 tags: %s" % e.message)

        self.cluster_info['heterogeneous_config'] = heterogeneous_config
        self.cluster_info['slave_request_type'] = slave_request_type
        self.cluster_info['idle_cluster_timeout'] = idle_cluster_timeout
        self.cluster_info['spot_settings'] = {}

        set_spot_instance_settings()
        set_stable_spot_bid_settings()
        set_data_disk()
        set_monitoring()
        set_data_disk()


class ClusterV2(Resource):

    rest_entity_path = "clusters"

    @classmethod
    def create(cls, cluster_info):
        """
        Create a new cluster using information provided in `cluster_info`.
        """
        conn = Qubole.agent(version="v2")
        return conn.post(cls.rest_entity_path, data=cluster_info)

    @classmethod
    def update(cls, cluster_id_label, cluster_info):
        """
        Update the cluster with id/label `cluster_id_label` using information provided in
        `cluster_info`.
        """
        conn = Qubole.agent(version="v2")
        return conn.put(cls.element_path(cluster_id_label), data=cluster_info)

    @classmethod
    def clone(cls, cluster_id_label, cluster_info, version=None):
        """
        Update the cluster with id/label `cluster_id_label` using information provided in
        `cluster_info`.
        """
        conn = Qubole.agent(version="v2")
        return conn.post(cls.element_path(cluster_id_label) + '/clone', data=cluster_info)

    # implementation needed
    @classmethod
    def list(self, state=None):
        pass






