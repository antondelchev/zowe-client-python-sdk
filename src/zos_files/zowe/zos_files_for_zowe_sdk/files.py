"""Zowe Python Client SDK.

This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at

https://www.eclipse.org/legal/epl-v20.html

SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zowe Project.
"""

from zowe.core_for_zowe_sdk import SdkApi
from zowe.core_for_zowe_sdk.exceptions import FileNotFound
from zowe.zos_files_for_zowe_sdk import exceptions, constants
import os
import shutil
import json

_ZOWE_FILES_DEFAULT_ENCODING='utf-8'

class Files(SdkApi):
    """
    Class used to represent the base z/OSMF Files API.

    ...

    Attributes
    ----------
    connection
        connection object
    """

    def __init__(self, connection):
        """
        Construct a Files object.

        Parameters
        ----------
        connection
            The z/OSMF connection object (generated by the ZoweSDK object)

        Also update header to accept gzip encoded responses
        """
        super().__init__(connection, "/zosmf/restfiles/")
        self.default_headers["Accept-Encoding"] = "gzip"


    def list_files(self, path):
        """Retrieve a list of USS files based on a given pattern.

        Returns
        -------
        json
            A JSON with a list of dataset names matching the given pattern
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["params"] = {"path": path}
        custom_args["url"] = "{}fs".format(self.request_endpoint)
        response_json = self.request_handler.perform_request("GET", custom_args)
        return response_json

    def get_file_content(self, filepath_name):
        """Retrieve the content of a filename. The complete path must be specified.

        Returns
        -------
        json
            A JSON with the contents of the specified USS file
        """
        custom_args = self._create_custom_request_arguments()
        #custom_args["params"] = {"filepath-name": filepath_name}
        custom_args["url"] = "{}fs{}".format(self.request_endpoint,filepath_name)
        response_json = self.request_handler.perform_request("GET", custom_args)
        return response_json

    def delete_uss(self, filepath_name, recursive=False):
        """
        Delete a file or directory

        Parameters
        ----------
        filepath of the file to be deleted

        recursive
            If specified as True, all the files and sub-directories will be deleted.

        Returns
        -------
        204
            HTTP Response for No Content
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}fs/{}".format(self.request_endpoint, filepath_name.lstrip("/"))
        if recursive:
            custom_args["headers"]["X-IBM-Option"] = "recursive"

        response_json = self.request_handler.perform_request("DELETE", custom_args, expected_code=[204])
        return response_json


    def list_dsn(self, name_pattern):
        """Retrieve a list of datasets based on a given pattern.

        Returns
        -------
        json
            A JSON with a list of dataset names matching the given pattern
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["params"] = {"dslevel": name_pattern}
        custom_args["url"] = "{}ds".format(self.request_endpoint)
        response_json = self.request_handler.perform_request("GET", custom_args)
        return response_json

    def list_dsn_members(self, dataset_name, member_pattern=None,
                         member_start=None, limit=1000, attributes='member'):
        """Retrieve the list of members on a given PDS/PDSE.

        Returns
        -------
        json
            A JSON with a list of members from a given PDS/PDSE
        """
        custom_args = self._create_custom_request_arguments()
        additional_parms = {}
        if member_start is not None:
            additional_parms['start'] = member_start
        if member_pattern is not None:
            additional_parms['pattern'] = member_pattern
        url = "{}ds/{}/member".format(self.request_endpoint, dataset_name)
        separator = '?'
        for k,v in additional_parms.items():
            url = "{}{}{}={}".format(url,separator,k,v)
            separator = '&'
        custom_args['url'] = url
        custom_args["headers"]["X-IBM-Max-Items"]  = "{}".format(limit)
        custom_args["headers"]["X-IBM-Attributes"] = attributes
        response_json = self.request_handler.perform_request("GET", custom_args)
        return response_json['items']  # type: ignore

    def get_dsn_content(self, dataset_name):
        """Retrieve the contents of a given dataset.

        Returns
        -------
        json
            A JSON with the contents of a given dataset
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, dataset_name)
        response_json = self.request_handler.perform_request("GET", custom_args)
        return response_json

    def create_data_set(self, dataset_name, options = {}):

        """
        Create a sequential or partitioned dataset.
        Parameters
        ----------
            dataset_name
        Returns
        -------
        json
        """

        if options.get("like") is None:
            if options.get("primary") is None or options.get("lrecl") is None:
                raise ValueError("If 'like' is not specified, you must specify 'primary' or 'lrecl'.")

            for opt in ("volser", "unit", "dsorg", "alcunit", 
                "primary", "secondary", "dirblk", "avgblk", "recfm", 
                "blksize", "lrecl", "storclass", "mgntclass", "dataclass", 
                "dsntype", "like"):

                if opt == "dsorg":
                    if options.get(opt) is not None and options[opt] not in ("PO", "PS"):
                        raise KeyError

                if opt == "alcunit":
                    if options.get(opt) is None:
                        options[opt] = "TRK"
                    else:
                        if options[opt] not in ("CYL", "TRK"):
                            raise KeyError

                if opt == "primary":
                    if options.get(opt) is not None:
                        if options["primary"] > 16777215:
                            raise ValueError

                if opt == "secondary":
                    if options.get("primary") is not None:
                        if options.get(opt) is None:
                            options["secondary"] = int(options["primary"] / 10)
                        if options["secondary"] > 16777215:
                            raise ValueError

                if opt == "dirblk":
                    if options.get(opt) is not None:
                        if options.get("dsorg") == "PS":
                            if options["dirblk"] != 0:
                                raise ValueError
                        elif options.get("dsorg") == "PO":
                            if options["dirblk"] == 0:
                                raise ValueError

                if opt == "recfm":
                    if options.get(opt) is None:
                        options[opt] = "F"
                    else:
                        if options[opt] not in ("F", "FB", "V", "VB", "U"):
                            raise KeyError

                if opt == "blksize":
                    if options.get(opt) is None and options.get("lrecl") is not None:
                        options[opt] = options["lrecl"]

        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, dataset_name)
        custom_args["json"] = options
        response_json = self.request_handler.perform_request("POST", custom_args, expected_code = [201])
        return response_json

    def create_default_data_set(self, dataset_name: str, default_type: str):
        """
        Create a dataset with default options set.
        Default options depend on the requested type.

        Parameters
        ----------
            dataset_name: str
            default_type: str
                "partitioned", "sequential", "classic", "c" or "binary"

        Returns
        -------
        json - A JSON containing the result of the operation
        """

        if default_type not in ("partitioned", "sequential", "classic", "c", "binary"):
            raise ValueError("Invalid type for default data set.")

        custom_args = self._create_custom_request_arguments()

        if default_type == "partitioned":
            custom_args["json"] = {
                "alcunit": "CYL",
                "dsorg": "PO",
                "primary": 1,
                "dirblk": 5,
                "recfm": "FB",
                "blksize": 6160,
                "lrecl": 80
            }
        elif default_type == "sequential":
            custom_args["json"] = {
                "alcunit": "CYL",
                "dsorg": "PS",
                "primary": 1,
                "recfm": "FB",
                "blksize": 6160,
                "lrecl": 80
            }
        elif default_type == "classic":
            custom_args["json"] = {
                "alcunit": "CYL",
                "dsorg": "PO",
                "primary": 1,
                "recfm": "FB",
                "blksize": 6160,
                "lrecl": 80,
                "dirblk": 25
            }
        elif default_type == "c":
            custom_args["json"] = {
                "dsorg": "PO",
                "alcunit": "CYL",
                "primary": 1,
                "recfm": "VB",
                "blksize": 32760,
                "lrecl": 260,
                "dirblk": 25
            }
        elif default_type == "binary":
            custom_args["json"] = {
                "dsorg": "PO",
                "alcunit": "CYL",
                "primary": 10,
                "recfm": "U",
                "blksize": 27998,
                "lrecl": 27998,
                "dirblk": 25
            }

        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, dataset_name)
        response_json = self.request_handler.perform_request("POST", custom_args, expected_code=[201])
        return response_json

    def create_uss(self, file_path, type, mode = None):
        """
        Add a file or directory
        Parameters
        ----------
        file_path of the file to add
        type = "file" or "dir"
        mode Ex:- rwxr-xr-x

        """

        data = {
            "type": type,
            "mode": mode
        }
        
        custom_args = self._create_custom_request_arguments()
        custom_args["json"] = data
        custom_args["url"] = "{}fs/{}".format(self.request_endpoint, file_path.lstrip("/"))
        response_json = self.request_handler.perform_request("POST", custom_args, expected_code = [201])
        return response_json

    def get_dsn_content_streamed(self, dataset_name):
        """Retrieve the contents of a given dataset streamed.

        Returns
        -------
        raw
            A raw socket response
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, dataset_name)
        raw_response = self.request_handler.perform_streamed_request("GET", custom_args)
        return raw_response

    def get_dsn_binary_content(self, dataset_name, with_prefixes=False):
        """
        Retrieve the contents of a given dataset as a binary bytes object.

        Parameters
        ----------
        dataset_name: str - Name of the dataset to retrieve
        with_prefixes: boolean - if True include a 4 byte big endian record len prefix
                                 default: False
        Returns
        -------
        bytes
            The contents of the dataset with no transformation
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, dataset_name)
        custom_args["headers"]["Accept"] = "application/octet-stream"
        if with_prefixes:
            custom_args["headers"]["X-IBM-Data-Type"] = 'record'
        else:
            custom_args["headers"]["X-IBM-Data-Type"] = 'binary'
        content = self.request_handler.perform_request("GET", custom_args)
        return content

    def get_dsn_binary_content_streamed(self, dataset_name, with_prefixes=False):
        """
        Retrieve the contents of a given dataset as a binary bytes object streamed.

        Parameters
        ----------
        dataset_name: str - Name of the dataset to retrieve
        with_prefixes: boolean - if True include a 4 byte big endian record len prefix
                                 default: False 
        Returns
        -------
        raw
            The raw socket response
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, dataset_name)
        custom_args["headers"]["Accept"] = "application/octet-stream"
        if with_prefixes:
            custom_args["headers"]["X-IBM-Data-Type"] = 'record'
        else:
            custom_args["headers"]["X-IBM-Data-Type"] = 'binary'
        content = self.request_handler.perform_streamed_request("GET", custom_args)
        return content

    def write_to_dsn(self, dataset_name, data, encoding=_ZOWE_FILES_DEFAULT_ENCODING):
        """Write content to an existing dataset.

        Returns
        -------
        json
            A JSON containing the result of the operation
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, dataset_name)
        custom_args["data"] = data
        custom_args['headers']['Content-Type'] = 'text/plain; charset={}'.format(encoding)
        response_json = self.request_handler.perform_request(
            "PUT", custom_args, expected_code=[204, 201]
        )
        return response_json

    def download_dsn(self, dataset_name, output_file):
        """Retrieve the contents of a dataset and saves it to a given file."""
        raw_response = self.get_dsn_content_streamed(dataset_name)
        with open(output_file, 'w') as f:
            shutil.copyfileobj(raw_response, f)

    def download_binary_dsn(self, dataset_name, output_file, with_prefixes=False):
        """Retrieve the contents of a binary dataset and saves it to a given file.

        Parameters
        ----------
        dataset_name:str - Name of the dataset to download
        output_file:str - Name of the local file to create
        with_prefixes:boolean - If true, include a four big endian bytes record length prefix.
                                The default is False

        Returns
        -------
        bytes
            Binary content of the dataset.
        """
        content = self.get_dsn_binary_content_streamed(dataset_name, with_prefixes=with_prefixes)
        with open(output_file, 'wb') as f:
            shutil.copyfileobj(content, f)

    def upload_file_to_dsn(self, input_file, dataset_name, encoding=_ZOWE_FILES_DEFAULT_ENCODING):
        """Upload contents of a given file and uploads it to a dataset."""
        if os.path.isfile(input_file):
            with open(input_file, 'rb') as in_file:
                response_json = self.write_to_dsn(dataset_name, in_file)
        else:
            raise FileNotFound(input_file)

    def write_to_uss(self, filepath_name, data, encoding=_ZOWE_FILES_DEFAULT_ENCODING):
        """Write content to an existing UNIX file.
        Returns
        -------
        json
            A JSON containing the result of the operation
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}fs/{}".format(self.request_endpoint, filepath_name.lstrip("/"))
        custom_args["data"] = data
        custom_args['headers']['Content-Type'] = 'text/plain; charset={}'.format(encoding)
        response_json = self.request_handler.perform_request(
            "PUT", custom_args, expected_code=[204, 201]
        )
        return response_json

    def upload_file_to_uss(self, input_file, filepath_name, encoding=_ZOWE_FILES_DEFAULT_ENCODING):
        """Upload contents of a given file and uploads it to UNIX file"""
        if os.path.isfile(input_file):
            in_file = open(input_file, 'r')
            file_contents = in_file.read()
            response_json = self.write_to_uss(filepath_name, file_contents)
        else:
            raise FileNotFound(input_file)

    def delete_data_set(self, dataset_name, volume=None, member_name=None):
        """Deletes a sequential or partitioned data."""
        custom_args = self._create_custom_request_arguments()
        if member_name is not None:
            dataset_name = f'{dataset_name}({member_name})'
        url = "{}ds/{}".format(self.request_endpoint, dataset_name)
        if volume is not None:
            url = "{}ds/-{}/{}".format(self.request_endpoint, volume, dataset_name)
        custom_args["url"] = url
        response_json = self.request_handler.perform_request(
            "DELETE", custom_args, expected_code=[200, 202, 204])
        return response_json

    def create_zFS_file_system(self, file_system_name, options={}):
        """
        Create a z/OS UNIX zFS Filesystem.
        
        Parameter
        ---------
        file_system_name: str - the name for the file system
        
        Returns
        -------
        json - A JSON containing the result of the operation
        """
        for key, value in options.items():
            if key == 'perms':
                if value < 0 or value > 777:
                    raise exceptions.InvalidPermsOption(value)
            
            if key == "cylsPri" or key == "cylsSec":
                if value > constants.zos_file_constants['MaxAllocationQuantity']:
                    raise exceptions.MaxAllocationQuantityExceeded

        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}mfs/zfs/{}".format(self.request_endpoint, file_system_name)
        custom_args["json"] = options
        response_json = self.request_handler.perform_request("POST", custom_args, expected_code = [201])
        return response_json

    def delete_zFS_file_system(self, file_system_name):
        """
        Deletes a zFS Filesystem
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}mfs/zfs/{}".format(self.request_endpoint, file_system_name)
        response_json = self.request_handler.perform_request("DELETE", custom_args, expected_code=[204])
        return response_json
    
    def mount_file_system(self, file_system_name, mount_point, options={}, encoding=_ZOWE_FILES_DEFAULT_ENCODING):
        """Mounts a z/OS UNIX file system on a specified directory.
        Parameter
        ---------
        file_system_name: str - the name for the file system
        mount_point: str - mount point to be used for mounting the UNIX file system
        options: dict - A JSON of request body options

        Returns
        -------
        json - A JSON containing the result of the operation
        """
        options["action"] = "mount"
        options["mount-point"] = mount_point
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}mfs/{}".format(self.request_endpoint, file_system_name)
        custom_args["json"] = options
        custom_args['headers']['Content-Type'] = 'text/plain; charset={}'.format(encoding)
        response_json = self.request_handler.perform_request("PUT", custom_args, expected_code=[204])
        return response_json

    def unmount_file_system(self, file_system_name, options={}, encoding=_ZOWE_FILES_DEFAULT_ENCODING):
        """Unmounts a z/OS UNIX file system on a specified directory.

        Parameter
        ---------
        file_system_name: str - the name for the file system
        options: dict - A JSON of request body options
        
        Returns
        -------
        json - A JSON containing the result of the operation
        """
        options["action"] = "unmount"
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}mfs/{}".format(self.request_endpoint, file_system_name)
        custom_args["json"] = options
        custom_args['headers']['Content-Type'] = 'text/plain; charset={}'.format(encoding)
        response_json = self.request_handler.perform_request("PUT", custom_args, expected_code=[204])
        return response_json

    def list_unix_file_systems(self, file_path_name=None, file_system_name=None):
        """
        list all mounted filesystems, or the specific filesystem mounted at a given path, or the
        filesystem with a given Filesystem name.

        Parameter
        ---------
        file_path: str - the UNIX directory that contains the files and directories to be listed.
        file_system_name: str - the name for the file system to be listed
        
        Returns
        -------
        json - A JSON containing the result of the operation
        """
        custom_args = self._create_custom_request_arguments()

        custom_args["params"] = {"path":file_path_name, "fsname": file_system_name}
        custom_args["url"] = "{}mfs".format(self.request_endpoint)
        response_json = self.request_handler.perform_request("GET", custom_args, expected_code=[200])
        return response_json

    def delete_migrated_data_set(self, dataset_name: str, wait=False, purge=False):
        """
        Deletes migrated data set.

        Parameters
        ----------
        dataset_name: str
            Name of the data set
        
        wait: bool
            If true, the function waits for completion of the request, otherwise the request is queued.

        purge: bool
            If true, the function uses the PURGE=YES on ARCHDEL request, otherwise it uses the PURGE=NO.

        Returns
        -------
        json - A JSON containing the result of the operation
        """

        data = {
            "request": "hdelete",
            "wait": json.dumps(wait),
            "purge": json.dumps(purge),
        }

        custom_args = self._create_custom_request_arguments()
        custom_args["json"] = data
        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, dataset_name)

        response_json = self.request_handler.perform_request("PUT", custom_args, expected_code=[200])
        return response_json

    def rename_dataset(self, before_dataset_name: str, after_dataset_name: str):
        """
        Renames the data set.

        Parameters
        ----------
        before_dataset_name: str
            The source data set name.

        after_dataset_name: str
            New name for the source data set.
    
        Returns
        -------
        json - A JSON containing the result of the operation
        """
        data = {
            "request": "rename",
            "from-dataset": {
                "dsn": before_dataset_name.strip()
            }
        }

        custom_args = self._create_custom_request_arguments()
        custom_args["json"] = data
        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, after_dataset_name.strip())

        response_json = self.request_handler.perform_request("PUT", custom_args, expected_code=[200])
        return response_json

    def rename_dataset_member(self, dataset_name: str, before_member_name: str, after_member_name: str, enq=""):
        """
        Renames the data set member.

        Parameters
        ----------
        dataset_name: str
            Name of the data set.

        before_member_name: str
            The source member name.
        
        after_member_name: str
            New name for the source member.
        
        enq: str
            Values can be SHRW or EXCLU. SHRW is the default for PDS members, EXCLU otherwise.

        Returns
        -------
        json - A JSON containing the result of the operation
        """

        data = {
            "request": "rename",
            "from-dataset": {
                "dsn": dataset_name.strip(),
                "member": before_member_name.strip(),
            }
        }

        path_to_member = dataset_name.strip() + "(" + after_member_name.strip() + ")"

        if enq:
            if enq in ("SHRW", "EXCLU"):
                data["from-dataset"]["enq"] = enq.strip()
            else:
                raise ValueError("Invalid value for enq.")

        custom_args = self._create_custom_request_arguments()
        custom_args['json'] = data
        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, path_to_member)

        response_json = self.request_handler.perform_request("PUT", custom_args, expected_code=[200])
        return response_json
