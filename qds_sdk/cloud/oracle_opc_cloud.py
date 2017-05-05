from qds_sdk.cloud.cloud import Cloud
class OracleOpcCloud(Cloud):
    '''
    qds_sdk.cloud.AzureCloud is the class which stores information about azure cloud config settings.
    The objects of this class can be use to set azure cloud_config settings while create/update/clone a cluster.
    '''

    def __init__(self):
        self.compute_config = {}
        self.location = {}
        self.network_config = {}
        self.storage_config = {}

    def set_cloud_config(self,
                         username=None,
                         password=None,
                         rest_api_endpoint=None,
                         use_account_compute_creds=None,
                         storage_rest_api_endpoint=None,
                         storage_username=None,
                         storage_password=None,
                         location=None,
                         vnic_set=None,
                         ip_network=None):
        '''

        Args:
            username: Username for customer's oracle opc account. This
                is required for creating the cluster.

            password: Password for customer's oracle opc account. This
                is required for creating the cluster.

            rest_api_endpoint: Rest API endpoint for customer's oracle opc cloud.

            use_account_compute_creds: Set it to true to use the account’s compute
                credentials for all clusters of the account.The default value is false

            storage_rest_api_endpoint: Rest API endpoint for storage related operations.

            storage_username: Username for customer's oracle opc account. This
                is required for creating the cluster.

            storage_password: Password for customer's oracle opc account. This
                is required for creating the cluster.

            location: Site name for opc cloud.

            vnic_set: vnic set for oracle opc.

            ip_network: subnet name for oracle opc

        '''


        def set_compute_config():
            self.compute_config['use_account_compute_creds'] = use_account_compute_creds
            self.compute_config['username'] = username
            self.compute_config['password'] = password
            self.compute_config['rest_api_endpoint'] = rest_api_endpoint


        def set_location():
            self.location['site'] = ""

        def set_network_config():
            self.network_config['vnic_set'] = vnic_set
            self.network_config['ip_network'] = ip_network

        def set_storage_config():
            self.storage_config['storage_rest_api_endpoint'] = storage_rest_api_endpoint
            self.storage_config['storage_username'] = storage_username
            self.storage_config['storage_password'] = storage_password

        set_compute_config()
        set_location()
        set_network_config()
        set_storage_config()

    def set_cloud_config_settings(self, arguments):
        self.set_cloud_config(username=arguments.username,
                              password=arguments.password,
                              rest_api_endpoint=arguments.rest_api_endpoint,
                              use_account_compute_creds=arguments.use_account_compute_creds,
                              storage_rest_api_endpoint=arguments.storage_rest_api_endpoint,
                              storage_username=arguments.storage_username,
                              storage_password=arguments.storage_password,
                              location=arguments.location,
                              vnic_set=arguments.vnic_set,
                              ip_network=arguments.ip_network)

    def cloud_config_parser(self, argparser):

        # compute settings parser
        compute_config = argparser.add_argument_group("compute config settings")
        compute_creds = compute_config.add_mutually_exclusive_group()
        compute_creds.add_argument("--enable_account_compute_creds",
                                   dest="use_account_compute_creds",
                                   action="store_true",
                                   default=None,
                                   help="to use account compute credentials")
        compute_creds.add_argument("--disable_account_compute_creds",
                                   dest="use_account_compute_creds",
                                   action="store_false",
                                   default=None,
                                   help="to disable account compute credentials")
        compute_config.add_argument("--username",
                                    dest="username",
                                    default=None,
                                    help="username for opc cloud account")
        compute_config.add_argument("--password",
                                    dest="password",
                                    default=None,
                                    help="password for opc cloud account")
        compute_config.add_argument("--rest-api-endpoint",
                                    dest="rest_api_endpoint",
                                    default=None,
                                    help="Rest API endpoint for oracle opc account")


        # location settings parser
        location_group = argparser.add_argument_group("location config settings")
        location_group.add_argument("--location",
                                    dest="location",
                                    default=None,
                                    help="location for opc cluster")

        # network settings parser
        network_config_group = argparser.add_argument_group("network config settings")
        network_config_group.add_argument("--vnic-set",
                                          dest="vnic_set",
                                          help="vnic set for opc", )
        network_config_group.add_argument("--ip-network",
                                          dest="ip_network",
                                          help="subnet name for opc")
        
        # storage config settings parser
        storage_config = argparser.add_argument_group("storage config settings")
        storage_config.add_argument("--storage-rest-api-endpoint",
                                    dest="storage_rest_api_endpoint",
                                    default=None,
                                    help="REST API endpoint for storage cloud")
        storage_config.add_argument("--storage-username",
                                    dest="storage_username",
                                    default=None,
                                    help="username for opc cloud account")
        storage_config.add_argument("--storage-password",
                                    dest="storage_password",
                                    default=None,
                                    help="password for opc cloud account")





