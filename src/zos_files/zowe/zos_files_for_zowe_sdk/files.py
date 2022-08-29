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

    def delete_uss(self, filepath_name):
        """
        Delete a file or directory

        Parameters
        ----------
        filepath of the file to be deleted

        Returns
        -------
        204
            HTTP Response for No Content
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}fs/{}".format(self.request_endpoint, filepath_name.lstrip("/"))
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

    def migrate_data_set(self, dataset_name, wait=False):
        """
        Migrates the data set.

        Parameters
        ----------
        dataset_name
            Name of the data set
        
        wait
            If true, the function waits for completion of the request, otherwise the request is queued.

        Returns
        -------
        json
            A JSON containing the result of the operation
        """

        data = {
            "request": "hmigrate",
            "wait": json.dumps(False)
        }

        if wait:
            data["wait"] = json.dumps(True)

        custom_args = self._create_custom_request_arguments()
        custom_args["json"] = data
        custom_args["url"] = "{}ds/{}".format(self.request_endpoint, dataset_name)

        response_json = self.request_handler.perform_request("PUT", custom_args, expected_code=[200])
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
