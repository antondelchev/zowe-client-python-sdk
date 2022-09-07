"""Unit tests for the Zowe Python SDK z/OS Files package."""
from unittest import TestCase, mock
from zowe.zos_files_for_zowe_sdk import Files, exceptions
import json

class TestFilesClass(TestCase):
    """File class unit tests."""

    def setUp(self):
        """Setup fixtures for File class."""
        self.test_profile = {"host": "https://mock-url.com",
                                "user": "Username",
                                "password": "Password",
                                "port": 443,
                                "rejectUnauthorized": True
                                }

    def test_object_should_be_instance_of_class(self):
        """Created object should be instance of Files class."""
        files = Files(self.test_profile)
        self.assertIsInstance(files, Files)

    @mock.patch('requests.Session.send')
    def test_delete_uss(self, mock_send_request):
        """Test deleting a directory recursively sends a request"""
        mock_send_request.return_value = mock.Mock(headers={"Content-Type": "application/json"}, status_code=204)

        Files(self.test_profile).delete_uss("filepath_name", recursive=True)
        mock_send_request.assert_called_once()

    @mock.patch('requests.Session.send')
    def test_create_zFS_file_system(self, mock_send_request):
        """Test creating a zfs sends a request"""
        mock_send_request.return_value = mock.Mock(headers={"Content-Type": "application/json"}, status_code=201)

        Files(self.test_profile).create_zFS_file_system("file_system_name", {"perms":100, "cylsPri": 16777213, "cylsSec": 16777215})
        mock_send_request.assert_called_once()

    @mock.patch('requests.Session.send')
    def test_delete_zFS_file_system(self, mock_send_request):
        """Test deleting a zfs sends a request"""
        mock_send_request.return_value = mock.Mock(headers={"Content-Type": "application/json"}, status_code=204)

        Files(self.test_profile).delete_zFS_file_system("file_system_name")
        mock_send_request.assert_called_once()
    
    def test_invalid_permission(self):
        """Test that the correct exception is raised when an invalid permission option is provided"""
        with self.assertRaises(exceptions.InvalidPermsOption) as e_info:
            Files(self.test_profile).create_zFS_file_system("file_system_name", {"perms": -1, "cylsPri": 16777213, "cylsSec": 16777215})
        self.assertEqual(str(e_info.exception), "Invalid zos-files create command 'perms' option: -1")

    def test_invalid_memory_allocation(self):
        """Test that the correct exception is raised when an invalid memory allocation option is provided"""
        with self.assertRaises(exceptions.MaxAllocationQuantityExceeded) as e_info:
            Files(self.test_profile).create_zFS_file_system("file_system_name", {"perms": 775, "cylsPri": 1677755513, "cylsSec": 16777215})
        self.assertEqual(str(e_info.exception), "Maximum allocation quantity of 16777215 exceeded")
    
    @mock.patch('requests.Session.send')
    def test_mount_zFS_file_system(self, mock_send_request):
        """Test mounting a zfs sends a request"""
        mock_send_request.return_value = mock.Mock(headers={"Content-Type": "application/json"}, status_code=204)

        Files(self.test_profile).mount_file_system("file_system_name", "mount_point")
        mock_send_request.assert_called_once()

    @mock.patch('requests.Session.send')
    def test_unmount_zFS_file_system(self, mock_send_request):
        """Test unmounting a zfs sends a request"""
        mock_send_request.return_value = mock.Mock(headers={"Content-Type": "application/json"}, status_code=204)

        Files(self.test_profile).unmount_file_system("file_system_name")
        mock_send_request.assert_called_once()

    @mock.patch('requests.Session.send')
    def test_list_zFS_file_system(self, mock_send_request):
        """Test unmounting a zfs sends a request"""
        mock_send_request.return_value = mock.Mock(headers={"Content-Type": "application/json"}, status_code=200)

        Files(self.test_profile).list_unix_file_systems("file_system_name")
        mock_send_request.assert_called_once()

    @mock.patch('requests.Session.send')
    def test_copy_from_dataset(self, mock_send_request):
        """Test copying from data set sends a request"""
        mock_send_request.return_value = mock.Mock(headers={"Content-Type": "application/json"}, status_code=200)

        Files(self.test_profile).copy_from_dataset("MY.OLD.DSN", "MY.NEW.DSN", replace=True)
        mock_send_request.assert_called_once()

    def test_copy_from_dataset_parameterized(self):
        """Test copying from dataset with different values"""
        test_values = [
            (("MY.TEST.DSN", "MY.WORK.DSN", "", "", "", False, False), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "MEMBER", "", "", False, False), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "MEMBER", "zmf046", "SHRW", False, False), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "MEMBER", "zmf046", "SHRW", True, False), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "MEMBER", "zmf046", "SHRW", True, True), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "MEMBER", "zmf046", "EXCLU", False, False), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "MEMBER", "zmf046", "EXCLU", True, False), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "MEMBER", "zmf046", "EXCLU", True, True), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "MEMBER", "zmf046", "SHR", False, False), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "MEMBER", "zmf046", "SHR", True, False), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "MEMBER", "zmf046", "SHR", True, True), True),
            (("MY.TEST.DSN", "MY.WORK.DSN", "", "", "INVALID", False, False), False),
        ]

        files_test_profile = Files(self.test_profile)

        for test_case in test_values:
            files_test_profile.request_handler.perform_request = mock.Mock()

            data = {
                "request": "copy",
                "from-dataset": {
                    "dsn": test_case[0][0],
                    "alias": json.dumps(test_case[0][6]),
                },
                "replace": json.dumps(test_case[0][5]),
            }

            url = "https://https://mock-url.com:443/zosmf/restfiles/ds/"

            if test_case[0][3]:
                data["from-dataset"]["volser"] = test_case[0][3]
                url += "-({})/".format(test_case[0][3])
            
            url += test_case[0][1]

            if test_case[0][2]:
                data["from-dataset"]["member"] = test_case[0][2]
                url += "({})".format(test_case[0][2])
            
            if test_case[0][4]:
                data["enq"] = test_case[0][4]

            if test_case[1]:
                files_test_profile.copy_from_dataset(*test_case[0])
                custom_args = files_test_profile._create_custom_request_arguments()
                custom_args["json"] = data
                custom_args["url"] = url
                files_test_profile.request_handler.perform_request.assert_called_once_with("PUT", custom_args, expected_code=[200])
            else:
                with self.assertRaises(ValueError) as e_info:
                    files_test_profile.copy_from_dataset(*test_case[0])
                self.assertEqual(str(e_info.exception), "Invalid value for enq.")

    @mock.patch('requests.Session.send')
    def test_copy_from_file(self, mock_send_request):
        """Test copying from file sends a request"""
        mock_send_request.return_value = mock.Mock(headers={"Content-Type": "application/json"}, status_code=200)

        Files(self.test_profile).copy_from_file("MY.OLD.DSN.INFO", "MY.NEW.DSN.INFO1", type="text", replace=True)
        mock_send_request.assert_called_once()

    def test_copy_from_file_parameterized(self):
        """Test copying from file with different values"""
        test_values = [
            (("MY.DSN.FILE", "MY.NEW.DSN.FILE", "text", False), True),
            (("MY.DSN.FILE", "MY.NEW.DSN.FILE", "binary", False), True),
            (("MY.DSN.FILE", "MY.NEW.DSN.FILE", "executable", False), True),
            (("MY.DSN.FILE", "MY.NEW.DSN.FILE", "text", True), True),
            (("MY.DSN.FILE", "MY.NEW.DSN.FILE", "binary", True), True),
            (("MY.DSN.FILE", "MY.NEW.DSN.FILE", "invalid", False), False),
            (("MY.DSN.FILE", "MY.NEW.DSN.FILE", "invalid", True), False),
        ]   

        files_test_profile = Files(self.test_profile)

        for test_case in test_values:
            files_test_profile.request_handler.perform_request = mock.Mock()

            data = {
                "request": "copy",
                "from-file": {
                    "filename": test_case[0][0],
                    "type": test_case[0][2],
                },
            }

            if test_case[0][2] == "text":
                data["replace"] = json.dumps(test_case[0][3])

            if test_case[1]:
                files_test_profile.copy_from_file(*test_case[0])
                custom_args = files_test_profile._create_custom_request_arguments()
                custom_args["json"] = data
                custom_args["url"] = "https://https://mock-url.com:443/zosmf/restfiles/ds/{}".format(test_case[0][1])
                files_test_profile.request_handler.perform_request.assert_called_once_with("PUT", custom_args, expected_code=[200])
            else:
                with self.assertRaises(ValueError) as e_info:
                    files_test_profile.copy_from_file(*test_case[0])
                self.assertEqual(str(e_info.exception), "Invalid value for type.")
