import pytest
from reconnaissance.theHarvester.harvester import HarvesterScanner
from reconnaissance.threads.thread_harvester import HarvesterScanThread
from flask import Flask
import json

def test_harvester_scanner():
    scanner = HarvesterScanner()
    result = scanner.run_harvester('example.com', 1, limit=10)
    
    assert isinstance(result, dict)
    assert 'status' in result
    assert 'scan_time' in result
    assert 'urls' in result
    assert 'emails' in result
    assert 'hosts' in result
    assert isinstance(result['urls'], list)
    assert isinstance(result['emails'], list)
    assert isinstance(result['hosts'], list)

def test_harvester_thread():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        thread = HarvesterScanThread('example.com', 1, app, limit=10)
        thread.start()
        result, success, code = thread.get_result(timeout=300)
        
        assert isinstance(result, dict)
        assert isinstance(success, bool)
        assert isinstance(code, int)
        assert 'status' in result
        
        if success:
            assert result['status'] == 'success'
            assert code == 200
        else:
            assert result['status'] == 'error'
            assert code in [408, 500]

def test_json_serialization():
    scanner = HarvesterScanner()
    result = scanner.run_harvester('example.com', 1, limit=10)
    
    # 测试是否可以序列化为 JSON
    try:
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        
        # 测试是否可以反序列化
        parsed_result = json.loads(json_str)
        assert isinstance(parsed_result, dict)
        assert parsed_result == result
    except Exception as e:
        pytest.fail(f"JSON 序列化/反序列化失败: {str(e)}")

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 