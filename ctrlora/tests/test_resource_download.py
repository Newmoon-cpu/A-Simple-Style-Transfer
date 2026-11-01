import unittest,tempfile,hashlib
from pathlib import Path
from unittest.mock import patch
from resource_download import install_resource, safe_target
class DownloadTests(unittest.TestCase):
 def test_reject_traversal(self):
  with self.assertRaises(ValueError):safe_target(Path.cwd(),'../escape')
 def test_existing_verified_skips_network(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'model';p.write_bytes(b'ok');item={'path':'model','bytes':2,'sha256':hashlib.sha256(b'ok').hexdigest(),'url':'https://example.com/model'}
   with patch('resource_download._HTTP.get',side_effect=AssertionError('network used')):install_resource(Path(d),item)
 def test_resume_rejected_by_server_restarts(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/'model.part').write_bytes(b'o')
   response=unittest.mock.Mock();response.status_code=200;response.headers={};response.iter_content.return_value=[b'ok'];response.__enter__=lambda s:s;response.__exit__=lambda *a:None
   item={'path':'model','bytes':2,'sha256':hashlib.sha256(b'ok').hexdigest(),'url':'https://example.com/model'}
   with patch('resource_download._HTTP.get',return_value=response):install_resource(Path(d),item)
   self.assertEqual((Path(d)/'model').read_bytes(),b'ok')
 def test_bad_response_never_installed(self):
  with tempfile.TemporaryDirectory() as d:
   response=unittest.mock.Mock();response.status_code=200;response.headers={};response.iter_content.return_value=[b'<html>'];response.__enter__=lambda s:s;response.__exit__=lambda *a:None
   with patch('resource_download._HTTP.get',return_value=response):
    with self.assertRaises(ValueError):install_resource(Path(d),{'path':'model','bytes':2,'sha256':hashlib.sha256(b'ok').hexdigest(),'url':'https://example.com/model'})
   self.assertFalse((Path(d)/'model').exists())
if __name__=='__main__':unittest.main()
