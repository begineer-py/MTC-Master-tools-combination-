import requests
import re
import ipaddress
from bs4 import BeautifulSoup
import os
import logging

class IPFinder:
    """IP 地址查找器"""
    
    def __init__(self):
        self.logger = logging.getLogger('IPFinder')
