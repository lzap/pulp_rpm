# -*- coding: utf-8 -*-
#
# Copyright © 2011 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import os

from pulp.plugins.conduits.repo_sync import RepoSyncConduit
from pulp.plugins.conduits.upload import UploadConduit
from pulp.plugins.conduits.unit_import import ImportUnitConduit
from pulp.plugins.conduits.dependency import DependencyResolutionConduit
from pulp.plugins.config import PluginCallConfiguration
from pulp.plugins.model import Unit
import mock
import pycurl

def ISOCurl():
    def perform():
        curl._file_to_write(curl._datas_to_write[curl._data_to_write_index])

    def setopt(opt, setting):
        if opt == pycurl.WRITEFUNCTION:
            curl._file_to_write = setting
        if opt == pycurl.URL:
            name_index_map = {'MANIFEST': 0, 'test.iso': 1, 'test2.iso': 2, 'test3.iso': 3}
            for key, value in name_index_map.items():
                if key in setting:
                    curl._data_to_write_index = value
                    return

    curl = mock.MagicMock()
    curl.close = mock.MagicMock()
    curl.perform = mock.MagicMock(side_effect=perform)
    curl.setopt = mock.MagicMock(side_effect=setopt)
    curl._datas_to_write = [
        'test.iso,f02d5a72cd2d57fa802840a76b44c6c6920a8b8e6b90b20e26c03876275069e0,16\n'
        'test2.iso,c7fbc0e821c0871805a99584c6a384533909f68a6bbe9a2a687d28d9f3b10c16,22\n'
        'test3.iso,94f7fe923212286855dea858edac1b4a292301045af0ddb275544e5251a50b3c,34',
        'This is a file.\n',
        'This is another file.\n',
        'Are you starting to get the idea?\n']
    return curl

def CurlMulti():
    def add_handle(curl):
        curl._is_active = True
        curl_multi._curls.append(curl)

    def info_read():
        return (0, [c for c in curl_multi._curls if c._is_active], [])

    def perform():
        for curl in curl_multi._curls:
            curl.perform()

        return (0, len(curl_multi._curls))

    def remove_handle(curl):
        curl._is_active = False
        curl_multi._curls.remove(curl)

    curl_multi = mock.MagicMock()
    curl_multi._curls = []
    curl_multi.add_handle = mock.MagicMock(side_effect=add_handle)
    curl_multi.close = mock.MagicMock()
    curl_multi.perform = mock.MagicMock(side_effect=perform)
    curl_multi.info_read = mock.MagicMock(side_effect=info_read)
    curl_multi.remove_handle = mock.MagicMock(side_effect=remove_handle)
    curl_multi.select = mock.MagicMock()
    return curl_multi

def get_sync_conduit(type_id=None, existing_units=None, pkg_dir=None):
    def side_effect(type_id, key, metadata, rel_path):
        if rel_path and pkg_dir:
            rel_path = os.path.join(pkg_dir, rel_path)
            if not os.path.exists(os.path.dirname(rel_path)):
                os.makedirs(os.path.dirname(rel_path))
        unit = Unit(type_id, key, metadata, rel_path)
        return unit

    def get_units(criteria=None):
        ret_val = []
        if existing_units:
            for u in existing_units:
                if criteria:
                    if u.type_id in criteria.type_ids:
                        ret_val.append(u)
                else:
                    ret_val.append(u)
        return ret_val

    def search_all_units(type_id, criteria):
        ret_val = []
        if existing_units:
            for u in existing_units:
                if u.type_id == type_id:
                    if u.unit_key['id'] == criteria['filters']['id']:
                        ret_val.append(u)
        return ret_val

    sync_conduit = mock.Mock(spec=RepoSyncConduit)
    sync_conduit.init_unit.side_effect = side_effect
    sync_conduit.get_units.side_effect = get_units
    sync_conduit.search_all_units.side_effect = search_all_units

    return sync_conduit


def get_import_conduit(source_units=None, existing_units=None):
    def get_source_units(criteria=None):
        units = []
        for u in source_units:
            if criteria and u.type_id not in criteria.type_ids:
                continue
            units.append(u)
        return units
    def get_units(criteria=None):
        ret_val = []
        if existing_units:
            for u in existing_units:
                if criteria:
                    if u.type_id in criteria.type_ids:
                        ret_val.append(u)
                else:
                    ret_val.append(u)
        return ret_val
    def search_all_units(type_id=None, criteria=None):
        ret_val = []
        if existing_units:
            for u in existing_units:
                if u.type_id is None:
                    ret_val.append(u)
                elif u.type_id in ["rpm", "srpm"]:
                    ret_val.append(u)
        return ret_val
    def save_unit(unit):
        units = []
        return units.append(unit)
    import_conduit = mock.Mock(spec=ImportUnitConduit)
    import_conduit.get_source_units.side_effect = get_source_units
    import_conduit.get_units.side_effect = get_units
    import_conduit.search_all_units.side_effect = search_all_units
    import_conduit.save_unit = mock.Mock()
    import_conduit.save_unit.side_effect = save_unit
    return import_conduit

def get_upload_conduit(type_id=None, unit_key=None, metadata=None, relative_path=None, pkg_dir=None):
    def side_effect(type_id, unit_key, metadata, relative_path):
        if relative_path and pkg_dir:
            relative_path = os.path.join(pkg_dir, relative_path)
        unit = Unit(type_id, unit_key, metadata, relative_path)
        return unit

    def get_units(criteria=None):
        ret_units = True
        if criteria and hasattr(criteria, "type_ids"):
            if type_id and type_id not in criteria.type_ids:
                ret_units = False
        return []

    upload_conduit = mock.Mock(spec=UploadConduit)
    upload_conduit.init_unit.side_effect = side_effect

    upload_conduit.get_units = mock.Mock()
    upload_conduit.get_units.side_effect = get_units

    upload_conduit.save_units = mock.Mock()
    upload_conduit.save_units.side_effect = side_effect

    upload_conduit.build_failure_report = mock.Mock()
    upload_conduit.build_failure_report.side_effect = side_effect

    upload_conduit.build_success_report = mock.Mock()
    upload_conduit.build_success_report.side_effect = side_effect

    return upload_conduit

def get_dependency_conduit(type_id=None, unit_key=None, metadata=None, existing_units=None, relative_path=None, pkg_dir=None):
    def side_effect(type_id, unit_key, metadata, relative_path):
        if relative_path and pkg_dir:
            relative_path = os.path.join(pkg_dir, relative_path)
        unit = Unit(type_id, unit_key, metadata, relative_path)
        return unit

    def get_units(criteria=None):
        ret_val = []
        if existing_units:
            for u in existing_units:
                if criteria:
                    if u.type_id in criteria.type_ids:
                        ret_val.append(u)
                else:
                    ret_val.append(u)
        return ret_val

    dependency_conduit = mock.Mock(spec=DependencyResolutionConduit)
    dependency_conduit.get_units = mock.Mock()
    dependency_conduit.get_units.side_effect = get_units
    dependency_conduit.build_failure_report = mock.Mock()
    dependency_conduit.build_failure_report.side_effect = side_effect

    dependency_conduit.build_success_report = mock.Mock()
    dependency_conduit.build_success_report.side_effect = side_effect

    return dependency_conduit

def get_basic_config(*arg, **kwargs):
    plugin_config = {"num_retries":0, "retry_delay":0}
    repo_plugin_config = {}
    for key in kwargs:
        repo_plugin_config[key] = kwargs[key]
    config = PluginCallConfiguration(plugin_config,
            repo_plugin_config=repo_plugin_config)
    return config
