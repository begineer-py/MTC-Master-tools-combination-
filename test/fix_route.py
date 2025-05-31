from flask import Flask, url_for

app = Flask(__name__)

# 定义一个简单的路由，与attack_route.py中的路由签名一致
@app.route('/attack/<int:target_id>', methods=['GET'])
def attack(target_id):
    return f"Attack route for target {target_id}"

# 注册为蓝图
from flask import Blueprint
attack_bp = Blueprint('attack', __name__)

@attack_bp.route('/attack/<int:target_id>', methods=['GET'])
def attack(target_id):
    return f"Attack blueprint route for target {target_id}"

app.register_blueprint(attack_bp)

# 测试URL生成
with app.test_request_context():
    # 尝试使用多种方式生成URL
    print(f"Direct route: {url_for('attack', target_id=1)}")
    print(f"Blueprint route: {url_for('attack.attack', target_id=1)}") 