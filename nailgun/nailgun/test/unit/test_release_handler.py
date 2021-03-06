# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from nailgun.db.sqlalchemy.models import Release
from nailgun.openstack.common import jsonutils
from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import reverse


class TestHandlers(BaseIntegrationTest):

    def test_release_put_change_name_and_version(self):
        release = self.env.create_release(api=False)
        resp = self.app.put(
            reverse('ReleaseHandler', kwargs={'obj_id': release.id}),
            params=jsonutils.dumps({
                'name': 'modified release',
                'version': '5.1'
            }),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEqual(200, resp.status_code)
        response = jsonutils.loads(resp.body)
        release_from_db = self.db.query(Release).one()
        self.db.refresh(release_from_db)
        self.assertEqual('5.1', release_from_db.version)
        self.assertEqual('5.1', response['version'])
        self.assertEqual('modified release', response['name'])

    def test_release_put_returns_400_if_no_body(self):
        release = self.env.create_release(api=False)
        resp = self.app.put(
            reverse('ReleaseHandler', kwargs={'obj_id': release.id}),
            "",
            headers=self.default_headers,
            expect_errors=True)
        self.assertEqual(resp.status_code, 400)

    def test_release_delete_returns_400_if_clusters(self):
        cluster = self.env.create_cluster(api=False)
        resp = self.app.delete(
            reverse('ReleaseHandler',
                    kwargs={'obj_id': cluster.release.id}),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.body,
            "Can't delete release with "
            "clusters assigned"
        )

    def test_release_put_orchestrator_data_w_masks(self):
        release = self.env.create_release(api=False)

        orchestrator_data = {
            'repo_metadata': {
                '5.1': 'http://{MASTER_IP}:8080/centos/x86_64',
                '5.1-user': 'http://{MASTER_IP}:8080/centos-user/x86_64',
            },
            'puppet_manifests_source': 'rsync://{MASTER_IP}:/puppet/modules/',
            'puppet_modules_source': 'rsync://{MASTER_IP}:/puppet/manifests/',
        }

        resp = self.app.put(
            reverse('ReleaseHandler', kwargs={'obj_id': release.id}),
            params=jsonutils.dumps({'orchestrator_data': orchestrator_data}),
            headers=self.default_headers)
        self.assertEqual(200, resp.status_code)

        resp = self.app.get(
            reverse('ReleaseHandler', kwargs={'obj_id': release.id}),
            headers=self.default_headers)
        self.assertEqual(200, resp.status_code)
        orchestrator_data = resp.json_body['orchestrator_data']

        self.assertEqual(orchestrator_data['repo_metadata'], {
            '5.1': 'http://127.0.0.1:8080/centos/x86_64',
            '5.1-user': 'http://127.0.0.1:8080/centos-user/x86_64'})
        self.assertEqual(
            orchestrator_data['puppet_manifests_source'],
            'rsync://127.0.0.1:/puppet/modules/')
        self.assertEqual(
            orchestrator_data['puppet_modules_source'],
            'rsync://127.0.0.1:/puppet/manifests/')
