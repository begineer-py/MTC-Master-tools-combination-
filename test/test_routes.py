from flask import Flask
from routes.reconnaissance_route.attack_route import attack_bp
import pprint

app = Flask(__name__)
app.register_blueprint(attack_bp)

print("蓝图路由:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule}") 